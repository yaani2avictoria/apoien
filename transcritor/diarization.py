"""Optional local speaker diarization using the gated pyannote 3.1 pipeline."""

import os
from pathlib import Path

from .sources import TranscriptionError


MODEL = 'pyannote/speaker-diarization-3.1'


def assign_speakers(segments, turns):
    """Attach chronological Pessoa N labels by temporal overlap.

    `turns` contains (start, end, raw_speaker_label) tuples from diarization.
    Weak/no overlap stays unassigned rather than guessing.
    """
    names = {}
    for start, end, raw_name in sorted(turns, key=lambda turn: (turn[0], turn[1])):
        if raw_name not in names:
            names[raw_name] = f'Pessoa {len(names) + 1}'

    output = []
    for segment in segments:
        start, end = segment['start'], segment['end']
        duration = max(0.0, end - start)
        overlaps = {}
        for turn_start, turn_end, raw_name in turns:
            overlap = max(0.0, min(end, turn_end) - max(start, turn_start))
            overlaps[raw_name] = overlaps.get(raw_name, 0.0) + overlap
        best_name, best_overlap = max(overlaps.items(), key=lambda item: item[1], default=(None, 0.0))
        labeled = dict(segment)
        threshold = min(0.25, duration * 0.2)
        labeled['speaker'] = names[best_name] if best_name is not None and best_overlap >= threshold else None
        output.append(labeled)
    return output, list(names.values())


def diarize_file(path, segments):
    token = os.environ.get('HF_TOKEN')
    if not token:
        raise TranscriptionError(
            'Diarização requer HF_TOKEN no ambiente e acesso aceito ao modelo pyannote/speaker-diarization-3.1.'
        )
    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise TranscriptionError(
            'Dependências opcionais ausentes; instale requirements-diarization.txt.'
        ) from exc

    temporary_audio = None
    try:
        pipeline = Pipeline.from_pretrained(
            MODEL,
            use_auth_token=token,
            cache_dir=str(Path('.cache/pyannote').resolve()),
        )
        if pipeline is None:
            raise TranscriptionError('O modelo de diarização não foi carregado; confira o acesso ao modelo.')
        pipeline.to(torch.device('cpu'))
        # pyannote's audio reader may reject otherwise valid MP4 containers.
        # Reuse PyAV to make a bounded, temporary mono 16 kHz WAV in workspace cache.
        import av
        import tempfile

        cache = Path('.cache/pyannote').resolve()
        cache.mkdir(parents=True, exist_ok=True)
        fd, temporary_audio = tempfile.mkstemp(prefix='diarization-', suffix='.wav', dir=cache)
        os.close(fd)
        with av.open(str(path)) as media, av.open(temporary_audio, mode='w', format='wav') as output:
            audio_streams = media.streams.audio
            if not audio_streams:
                raise TranscriptionError('Arquivo sem faixa de áudio para diarização.')
            output_stream = output.add_stream('pcm_s16le', rate=16000)
            output_stream.layout = 'mono'
            resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
            for frame in media.decode(audio_streams[0]):
                for converted in resampler.resample(frame):
                    for packet in output_stream.encode(converted):
                        output.mux(packet)
            for packet in output_stream.encode(None):
                output.mux(packet)
        annotation = pipeline(temporary_audio)
        if hasattr(annotation, 'speaker_diarization'):
            annotation = annotation.speaker_diarization
        turns = [
            (float(turn.start), float(turn.end), str(label))
            for turn, _, label in annotation.itertracks(yield_label=True)
        ]
    except TranscriptionError:
        raise
    except Exception as exc:
        # Do not include exception text: some network exceptions can contain URLs.
        raise TranscriptionError(f'Falha no modelo de diarização ({type(exc).__name__}).') from exc
    finally:
        if temporary_audio:
            Path(temporary_audio).unlink(missing_ok=True)

    if not turns:
        raise TranscriptionError('A diarização não identificou segmentos de voz.')
    labeled, speakers = assign_speakers(segments, turns)
    return dict(
        model=MODEL,
        status='completed',
        speakers=speakers,
        segments=labeled,
        note='Rótulos Pessoa N identificam vozes, não nomes ou identidades reais.',
    )

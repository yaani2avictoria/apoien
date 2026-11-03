"""Optional, local OCR observations from sparsely sampled video frames.

OCR output is kept separate from spoken transcript segments. It is evidence of
text visible in a frame, not proof that the visible person is speaking.
"""

import csv
import io
import re
import shutil
import subprocess
from pathlib import Path

from .sources import TranscriptionError


def _ocr_words(tsv):
    rows = csv.DictReader(io.StringIO(tsv), delimiter='\t')
    lines = {}
    for row in rows:
        text = (row.get('text') or '').strip()
        try:
            confidence = float(row.get('conf', '-1'))
        except (TypeError, ValueError):
            continue
        if not text or confidence < 50:
            continue
        key = (row.get('block_num'), row.get('par_num'), row.get('line_num'))
        entry = lines.setdefault(key, {'words': [], 'confidences': []})
        entry['words'].append(text)
        entry['confidences'].append(confidence)
    return [
        {'text': ' '.join(line['words']),
         'confidence': round(sum(line['confidences']) / len(line['confidences']), 1)}
        for line in lines.values()
    ]


def _nearest_segment(seconds, segments):
    if not segments:
        return None
    index = min(range(len(segments)), key=lambda i: min(
        abs(seconds - segments[i]['start']), abs(seconds - segments[i]['end']),
        0 if segments[i]['start'] <= seconds <= segments[i]['end'] else float('inf')))
    segment = segments[index]
    if segment['start'] <= seconds <= segment['end']:
        delta = 0.0
    else:
        delta = min(abs(seconds - segment['start']), abs(seconds - segment['end']))
    return {'segment_index': index, 'delta_seconds': round(delta, 3)}


def local_visual_ocr(path, segments, max_seconds, frame_interval=10, max_frames=20,
                     language='eng'):
    """Sample local video frames and return timestamped OCR, without a vision API.

    At most ``max_frames`` frames are sent to Tesseract. If the requested
    interval would exceed that bound, samples are spread across the media.
    """
    media_path = Path(path)
    if not media_path.is_file():
        raise TranscriptionError('Arquivo de vídeo não encontrado para OCR.')
    if not re.fullmatch(r'[A-Za-z0-9_+]+', language):
        raise TranscriptionError('Idioma OCR inválido; use códigos instalados no Tesseract.')
    tesseract = shutil.which('tesseract')
    if not tesseract:
        raise TranscriptionError('OCR solicitado, mas o executável Tesseract não está instalado.')
    try:
        language_result = subprocess.run(
            [tesseract, '--list-langs'], capture_output=True, timeout=5, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TranscriptionError('Tesseract excedeu o tempo ao listar idiomas instalados.') from exc
    language_output = (language_result.stdout + language_result.stderr).decode('utf-8', 'replace')
    available_languages = set(language_output.splitlines()[1:])
    requested_languages = set(language.split('+'))
    missing_languages = requested_languages - available_languages
    if language_result.returncode or missing_languages:
        missing = ', '.join(sorted(missing_languages)) or 'lista de idiomas indisponível'
        raise TranscriptionError(f'Pacote(s) OCR ausente(s) no Tesseract: {missing}.')
    try:
        import av
    except ImportError as exc:
        raise TranscriptionError('Leitura de quadros requer PyAV (`av`) no ambiente.') from exc

    observations = []
    sample_times = []
    with av.open(str(media_path)) as container:
        if not container.streams.video:
            raise TranscriptionError('Arquivo sem faixa de vídeo para OCR.')
        stream = container.streams.video[0]
        duration = None
        if stream.duration is not None and stream.time_base is not None:
            duration = float(stream.duration * stream.time_base)
        elif container.duration is not None:
            duration = float(container.duration / av.time_base)
        if duration is None or duration <= 0 or duration > max_seconds:
            raise TranscriptionError(
                f'Duração de vídeo desconhecida ou superior a {max_seconds}s; '
                'forneça um trecho curto.'
            )

        effective_interval = max(frame_interval, duration / max_frames)
        next_sample = 0.0
        for frame in container.decode(video=0):
            seconds = frame.time
            if seconds is None:
                continue
            seconds = float(seconds)
            if seconds > duration or seconds + 1e-6 < next_sample:
                continue
            if len(sample_times) >= max_frames:
                break
            width, height = frame.width, frame.height
            scale = min(1.0, 1280 / width, 720 / height)
            scaled_width = max(1, round(width * scale))
            scaled_height = max(1, round(height * scale))
            rgb_frame = frame.reformat(width=scaled_width, height=scaled_height,
                                       format='rgb24')
            pixels = rgb_frame.to_ndarray().tobytes()
            ppm = f'P6\n{scaled_width} {scaled_height}\n255\n'.encode() + pixels
            try:
                result = subprocess.run(
                    [tesseract, 'stdin', 'stdout', '-l', language, 'tsv'],
                    input=ppm, capture_output=True, timeout=8, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TranscriptionError('OCR excedeu 8 segundos em um quadro; processamento encerrado.') from exc
            if result.returncode:
                message = result.stderr.decode('utf-8', 'replace').strip()[:500]
                raise TranscriptionError(f'Tesseract falhou ({result.returncode}): {message}')
            sample_times.append(round(seconds, 3))
            nearest = _nearest_segment(seconds, segments)
            for line in _ocr_words(result.stdout.decode('utf-8', 'replace')):
                observations.append({
                    'timestamp': round(seconds, 3),
                    'text': line['text'],
                    'ocr_confidence': line['confidence'],
                    'evidence': 'visible_text_ocr',
                    'nearest_speech_segment': nearest,
                })
            next_sample = seconds + effective_interval

    return {
        'method': 'local_tesseract_ocr',
        'fidelity_verified': False,
        'frame_interval_seconds': round(effective_interval, 3),
        'sampled_frame_count': len(sample_times),
        'sampled_timestamps': sample_times,
        'observations': observations,
        'speaker_identity_inferred': False,
    }

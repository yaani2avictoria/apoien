from pathlib import Path
from urllib.parse import urlparse, parse_qs
import re
import urllib.request


class TranscriptionError(Exception):
    pass


def youtube_id(url):
    p = urlparse(url)
    if p.scheme != 'https':
        return None
    if p.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        value = parse_qs(p.query).get('v', [''])[0]
    elif p.hostname == 'youtu.be':
        value = p.path.strip('/')
    else:
        return None
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        raise TranscriptionError('URL do YouTube sem identificador válido.')
    return value


def captions(video_id, languages):
    from youtube_transcript_api import YouTubeTranscriptApi
    import requests
    class TimedSession(requests.Session):
        def request(self, *args, **kwargs):
            kwargs.setdefault('timeout', 15)
            return super().request(*args, **kwargs)
    with TimedSession() as session:
        result = YouTubeTranscriptApi(http_client=session).fetch(video_id, languages=languages)
        segments = [dict(start=s.start, end=s.start+s.duration, text=s.text) for s in result]
        if not segments:
            raise TranscriptionError('O serviço não retornou legendas.')
        return dict(source='youtube_captions', language=result.language_code,
                    generated=result.is_generated, segments=segments)


def download(url, target, max_bytes=25*1024*1024):
    if urlparse(url).scheme != 'https':
        raise TranscriptionError('Downloads exigem HTTPS.')
    with urllib.request.urlopen(url, timeout=20) as response:
        if urlparse(response.url).scheme != 'https':
            raise TranscriptionError('Redirecionamento sem HTTPS recusado.')
        with Path(target).open('wb') as out:
            size = 0
            while chunk := response.read(65536):
                size += len(chunk)
                if size > max_bytes:
                    raise TranscriptionError('Download excede o limite de 25 MiB.')
                out.write(chunk)


def local_audio(path, model, threads, max_seconds):
    import av
    from faster_whisper import WhisperModel
    if not Path(path).is_file():
        raise TranscriptionError('Arquivo não encontrado.')
    with av.open(str(path)) as media:
        if not media.streams.audio:
            raise TranscriptionError('Arquivo sem faixa de áudio.')
        duration = media.duration / av.time_base if media.duration else None
        if duration is None or duration > max_seconds:
            raise TranscriptionError(f'Duração desconhecida ou superior a {max_seconds}s; forneça um trecho curto.')
    engine = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=threads,
                          num_workers=1, download_root=str(Path('.cache/models').resolve()))
    stream, info = engine.transcribe(str(path), beam_size=1, vad_filter=False,
                                     condition_on_previous_text=False)
    segments = [dict(start=s.start, end=s.end, text=s.text.strip()) for s in stream]
    if not segments:
        raise TranscriptionError('Nenhuma fala reconhecida; nenhum conteúdo foi criado.')
    return dict(source='local_faster_whisper', model=model, device='cpu', compute_type='int8',
                language=info.language, segments=segments)

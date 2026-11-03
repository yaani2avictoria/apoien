import argparse
import json
import resource
import sys
import tempfile
import time
from pathlib import Path
from .sources import youtube_id, captions, local_audio, download, TranscriptionError
from .export import export
from .visual import local_visual_ocr
from .diarization import diarize_file


def bounded_seconds(value):
    number = int(value)
    if not 1 <= number <= 300:
        raise argparse.ArgumentTypeError('Use entre 1 e 300 segundos.')
    return number


def main():
    p = argparse.ArgumentParser(description='Transcrição local gratuita; URLs do YouTube usam somente legendas acessíveis.')
    p.add_argument('source')
    p.add_argument('--output', default='outputs/transcricao')
    p.add_argument('--model', choices=['tiny', 'base'], default='tiny')
    p.add_argument('--language', default=None,
                   help='Idioma do áudio (ex.: pt); omitido, o Whisper detecta automaticamente.')
    p.add_argument('--diarize', action='store_true',
                   help='Opcional: separa vozes localmente como Pessoa 1, Pessoa 2 etc. Requer dependências e HF_TOKEN.')
    p.add_argument('--model-dir', type=Path, help='Diretório local de modelo CTranslate2 oficial já obtido de forma autorizada.')
    p.add_argument('--threads', type=int, choices=range(1, 5), default=2)
    p.add_argument('--max-seconds', type=bounded_seconds, default=60)
    p.add_argument('--languages', nargs='+', default=['pt', 'en'])
    p.add_argument('--authorized', action='store_true', help='Confirma autorização para processar arquivo ou URL direta de mídia.')
    p.add_argument('--visual-ocr', action='store_true', help='Opcional: lê texto visível em poucos quadros locais; não atribui identidade ao falante.')
    p.add_argument('--frame-interval', type=int, choices=range(5, 61), default=10,
                   help='Intervalo mínimo de amostragem visual em segundos (5–60).')
    p.add_argument('--ocr-languages', default='eng',
                   help='Idiomas instalados no Tesseract, por exemplo por+eng.')
    args = p.parse_args()
    started = time.monotonic()
    status = 'failed'
    try:
        video = youtube_id(args.source)
        if video:
            if args.diarize:
                raise TranscriptionError('Diarização local aceita arquivo de mídia, não URL do YouTube.')
            if args.visual_ocr:
                raise TranscriptionError('OCR visual recebe somente arquivo local; URLs do YouTube não são baixadas.')
            result = captions(video, args.languages)
        else:
            if not args.authorized:
                raise TranscriptionError('Confirme autorização com --authorized para processar mídia.')
            with tempfile.TemporaryDirectory(prefix='transcritor-') as tmp:
                source = args.source
                if args.visual_ocr and source.startswith(('https://', 'http://')):
                    raise TranscriptionError('OCR visual experimental exige um arquivo local autorizado.')
                if source.startswith(('https://', 'http://')):
                    source = Path(tmp) / 'media'
                    download(args.source, source)
                model = args.model
                if args.model_dir:
                    if not args.model_dir.is_dir():
                        raise TranscriptionError('Diretório de modelo não encontrado.')
                    model = str(args.model_dir.resolve())
                result = local_audio(source, model, args.threads, args.max_seconds,
                                     language=args.language)
                if args.diarize:
                    diarized = diarize_file(source, result['segments'])
                    result['segments'] = diarized.pop('segments')
                    result['diarization'] = diarized
                if args.visual_ocr:
                    result['visual_context'] = local_visual_ocr(
                        source, result['segments'], args.max_seconds,
                        frame_interval=args.frame_interval, language=args.ocr_languages,
                    )
        export(result, args.output)
        status = 'passed'
        print(f"Exportados TXT, SRT e JSON: {args.output}; segmentos: {len(result['segments'])}")
        return 0
    except MemoryError:
        print('Erro: memória insuficiente; reduza modelo/duração.', file=sys.stderr)
    except ImportError as exc:
        print(f'Dependência ausente ou incompatível: {exc}', file=sys.stderr)
    except OSError as exc:
        print(f'Falha de rede, arquivo ou recurso ({type(exc).__name__}): {exc}', file=sys.stderr)
    except Exception as exc:
        print(f'Falha ({type(exc).__name__}): {exc}', file=sys.stderr)
    finally:
        print(json.dumps(dict(status=status, elapsed_seconds=round(time.monotonic()-started, 3),
                              peak_rss_mib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 2))), file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())

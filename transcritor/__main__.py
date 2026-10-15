import argparse
import json
import resource
import sys
import tempfile
import time
from pathlib import Path
from .sources import youtube_id, captions, local_audio, download, TranscriptionError
from .export import export


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
    p.add_argument('--model-dir', type=Path, help='Diretório local de modelo CTranslate2 oficial já obtido de forma autorizada.')
    p.add_argument('--threads', type=int, choices=range(1, 5), default=2)
    p.add_argument('--max-seconds', type=bounded_seconds, default=60)
    p.add_argument('--languages', nargs='+', default=['pt', 'en'])
    p.add_argument('--authorized', action='store_true', help='Confirma autorização para processar arquivo ou URL direta de mídia.')
    args = p.parse_args()
    started = time.monotonic()
    status = 'failed'
    try:
        video = youtube_id(args.source)
        if video:
            result = captions(video, args.languages)
        else:
            if not args.authorized:
                raise TranscriptionError('Confirme autorização com --authorized para processar mídia.')
            with tempfile.TemporaryDirectory(prefix='transcritor-') as tmp:
                source = args.source
                if source.startswith(('https://', 'http://')):
                    source = Path(tmp) / 'media'
                    download(args.source, source)
                model = args.model
                if args.model_dir:
                    if not args.model_dir.is_dir():
                        raise TranscriptionError('Diretório de modelo não encontrado.')
                    model = str(args.model_dir.resolve())
                result = local_audio(source, model, args.threads, args.max_seconds)
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

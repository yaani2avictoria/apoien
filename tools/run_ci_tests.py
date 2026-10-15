"""Run existing tests and a dependency smoke check without models, network or secrets."""
import argparse
import importlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('artifacts/tests'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output/'summary.json').exists():
        parser.error('Output already exists; choose a new report directory.')
    started = time.monotonic()
    with (args.output/'unittest.log').open('w') as log:
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        with patch('socket.socket.connect', side_effect=RuntimeError('Network disabled in unit tests')):
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    smoke = {'status': 'passed'}
    try:
        for name in ['transcritor.sources', 'transcritor.export', 'transcritor.diagnostico',
                     'youtube_transcript_api', 'faster_whisper', 'ctranslate2', 'av']:
            importlib.import_module(name)
        # Exercises the exact decoder kwarg used by faster-whisper, no model download.
        import av
        audio = io.BytesIO()
        with wave.open(audio, 'wb') as writer:
            writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(16000)
            writer.writeframes(b'\0\0'*1600)
        audio.seek(0)
        with av.open(audio, metadata_errors='ignore') as media:
            if not list(media.decode(audio=0)):
                raise RuntimeError('Decoder returned no frames')
    except Exception as exc:
        smoke = {'status': 'failed', 'exception_type': type(exc).__name__}
    summary = {'schema': 1, 'runner': {'github_actions': os.getenv('GITHUB_ACTIONS')=='true', 'run_id':os.getenv('GITHUB_RUN_ID')}, 'tests_run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skipped': len(result.skipped),
               'dependency_smoke': smoke, 'elapsed_seconds': round(time.monotonic()-started, 3),
               'external_requests': 0, 'gemini_called': False}
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))
    return 0 if result.testsRun and result.wasSuccessful() and smoke['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())

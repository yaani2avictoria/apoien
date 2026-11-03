import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from transcritor.sources import local_audio


class LanguageOption(unittest.TestCase):
    def run_fake_transcription(self, language, detected_language):
        class FakeMedia:
            duration = 1_000_000
            streams = types.SimpleNamespace(audio=[object()])

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        class FakeSegment:
            start, end, text = 0.0, 1.0, 'Texto de teste.'

        seen = {}

        class FakeWhisperModel:
            def __init__(self, *args, **kwargs):
                pass

            def transcribe(self, *args, **kwargs):
                seen.update(kwargs)
                return iter([FakeSegment()]), types.SimpleNamespace(language=detected_language)

        fake_av = types.SimpleNamespace(open=lambda path: FakeMedia(), time_base=1_000_000)
        fake_fw = types.SimpleNamespace(WhisperModel=FakeWhisperModel)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'audio.mp4'
            path.write_bytes(b'x')
            with patch.dict(sys.modules, {'av': fake_av, 'faster_whisper': fake_fw}):
                result = local_audio(path, 'tiny', 2, 60, language=language)
        return seen, result

    def test_forces_portuguese_when_requested(self):
        kwargs, result = self.run_fake_transcription('pt', 'pt')
        self.assertEqual(kwargs['language'], 'pt')
        self.assertEqual(result['requested_language'], 'pt')
        self.assertEqual(result['language'], 'pt')

    def test_none_preserves_automatic_detection(self):
        kwargs, result = self.run_fake_transcription(None, 'en')
        self.assertIsNone(kwargs['language'])
        self.assertIsNone(result['requested_language'])
        self.assertEqual(result['language'], 'en')


if __name__ == '__main__':
    unittest.main()

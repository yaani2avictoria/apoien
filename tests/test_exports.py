import json
import tempfile
import unittest
from pathlib import Path
from transcritor.export import export, timestamp
from transcritor.sources import youtube_id, TranscriptionError


class Formats(unittest.TestCase):
    def test_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)/'sample'
            result = {'source': 'synthetic_format_test', 'segments': [{'start': 0.125, 'end': 1.5, 'text': 'Teste de formato.'}]}
            export(result, base)
            self.assertEqual(json.loads(base.with_suffix('.json').read_text()), result)
            self.assertEqual(base.with_suffix('.txt').read_text(), 'Teste de formato.\n')
            self.assertIn('00:00:00,125 --> 00:00:01,500', base.with_suffix('.srt').read_text())

    def test_visual_evidence_stays_out_of_spoken_text_and_srt(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'enriched'
            result = {
                'source': 'local_faster_whisper',
                'segments': [{'start': 0, 'end': 1, 'text': 'Bom dia.'}],
                'visual_context': {'observations': [{'timestamp': 0, 'text': 'Nome no slide'}]},
            }
            export(result, base)
            self.assertIn('Nome no slide', json.loads(base.with_suffix('.json').read_text())['visual_context']['observations'][0]['text'])
            self.assertNotIn('Nome no slide', base.with_suffix('.txt').read_text())
            self.assertNotIn('Nome no slide', base.with_suffix('.srt').read_text())

    def test_rounding(self):
        self.assertEqual(timestamp(59.9999), '00:01:00,000')

    def test_urls(self):
        self.assertEqual(youtube_id('https://www.youtube.com/watch?v=nkjymufhKpU'), 'nkjymufhKpU')
        self.assertIsNone(youtube_id('https://example.com/audio.wav'))
        with self.assertRaises(TranscriptionError):
            youtube_id('https://youtube.com/watch?v=bad')

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from transcritor.diarization import assign_speakers, diarize_file
from transcritor.export import export
from transcritor.sources import TranscriptionError


class Diarization(unittest.TestCase):
    def test_assigns_chronological_person_labels_by_overlap(self):
        segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'Oi.'},
            {'start': 2.0, 'end': 4.0, 'text': 'Olá.'},
        ]
        turns = [(2.0, 4.0, 'speaker_b'), (0.0, 2.0, 'speaker_a')]
        labeled, speakers = assign_speakers(segments, turns)
        self.assertEqual(speakers, ['Pessoa 1', 'Pessoa 2'])
        self.assertEqual([segment['speaker'] for segment in labeled], ['Pessoa 1', 'Pessoa 2'])

    def test_leaves_segment_unassigned_without_temporal_evidence(self):
        labeled, _ = assign_speakers([{'start': 3.0, 'end': 4.0, 'text': 'Oi.'}], [(0.0, 1.0, 'a')])
        self.assertIsNone(labeled[0]['speaker'])

    def test_diarization_requires_token_without_revealing_or_loading_model(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(TranscriptionError, 'HF_TOKEN'):
                diarize_file('media.mp4', [])

    def test_speaker_labels_appear_in_txt_srt_and_json(self):
        result = {'segments': [{'start': 0, 'end': 1, 'text': 'Bom dia.', 'speaker': 'Pessoa 1'}]}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / 'speaker'
            export(result, base)
            self.assertIn('[Pessoa 1] Bom dia.', base.with_suffix('.txt').read_text())
            self.assertIn('[Pessoa 1] Bom dia.', base.with_suffix('.srt').read_text())
            self.assertEqual(json.loads(base.with_suffix('.json').read_text()), result)


if __name__ == '__main__':
    unittest.main()

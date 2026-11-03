import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from transcritor.visual import _nearest_segment, _ocr_words, local_visual_ocr
from transcritor.sources import TranscriptionError


class VisualContext(unittest.TestCase):
    def test_ocr_groups_confident_words_by_line(self):
        tsv = ('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
               '5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90\tAna\n'
               '5\t1\t1\t1\t1\t2\t12\t0\t20\t10\t80\tSouza\n'
               '5\t1\t1\t1\t2\t1\t0\t20\t10\t10\t20\truído\n')
        self.assertEqual(_ocr_words(tsv), [{'text': 'Ana Souza', 'confidence': 85.0}])

    def test_nearest_speech_is_temporal_metadata_only(self):
        segments = [{'start': 1.0, 'end': 2.0, 'text': 'Olá.'},
                    {'start': 8.0, 'end': 10.0, 'text': 'Slide.'}]
        self.assertEqual(_nearest_segment(8.5, segments),
                         {'segment_index': 1, 'delta_seconds': 0.0})
        self.assertEqual(_nearest_segment(4.0, segments),
                         {'segment_index': 0, 'delta_seconds': 2.0})

    def test_requires_local_media_and_ocr_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / 'video.mp4'
            media.touch()
            with patch('transcritor.visual.shutil.which', return_value=None):
                with self.assertRaisesRegex(TranscriptionError, 'Tesseract'):
                    local_visual_ocr(media, [], 60)

    def test_rejects_invalid_ocr_language_before_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / 'video.mp4'
            media.touch()
            with self.assertRaisesRegex(TranscriptionError, 'Idioma OCR inválido'):
                local_visual_ocr(media, [], 60, language='por; rm -rf /')

    def test_missing_language_data_is_reported_before_video_decode(self):
        languages = types.SimpleNamespace(
            returncode=0, stdout=b'List of available languages (2):\neng\nosd\n', stderr=b'')
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / 'video.mp4'
            media.touch()
            with patch('transcritor.visual.shutil.which', return_value='/usr/bin/tesseract'), \
                 patch('transcritor.visual.subprocess.run', return_value=languages):
                with self.assertRaisesRegex(TranscriptionError, 'ausente.*por'):
                    local_visual_ocr(media, [], 60, language='por+eng')

    def test_samples_are_bounded_and_keeps_ocr_separate(self):
        class Pixels:
            def tobytes(self):
                return b'\0\0\0' * 4

        class Frame:
            width = 2
            height = 2
            def __init__(self, time): self.time = time
            def reformat(self, **kwargs): return self
            def to_ndarray(self): return Pixels()

        class Container:
            duration = 30_000_000
            streams = types.SimpleNamespace(video=[types.SimpleNamespace(duration=30, time_base=1)])
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def decode(self, video=0): return iter(Frame(t) for t in range(31))

        fake_av = types.SimpleNamespace(time_base=1_000_000, open=lambda _: Container())
        tsv = ('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
               '5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t95\tNOME\n')
        result = types.SimpleNamespace(returncode=0, stdout=tsv.encode(), stderr=b'')
        languages = types.SimpleNamespace(returncode=0, stdout=b'List of available languages (2):\neng\nosd\n', stderr=b'')
        segments = [{'start': 0.0, 'end': 1.0, 'text': 'Fala.'}]
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / 'video.mp4'
            media.touch()
            with patch.dict(sys.modules, {'av': fake_av}), \
                 patch('transcritor.visual.shutil.which', return_value='/usr/bin/tesseract'), \
                 patch('transcritor.visual.subprocess.run', side_effect=[languages, result, result, result]) as run:
                context = local_visual_ocr(media, segments, 60, frame_interval=10, max_frames=3)
        self.assertEqual(context['sampled_timestamps'], [0.0, 10.0, 20.0])
        self.assertEqual(context['sampled_frame_count'], 3)
        self.assertFalse(context['speaker_identity_inferred'])
        self.assertFalse(context['fidelity_verified'])
        self.assertEqual(context['observations'][0]['text'], 'NOME')
        self.assertEqual(context['observations'][0]['nearest_speech_segment']['segment_index'], 0)
        self.assertEqual(run.call_count, 4)


if __name__ == '__main__':
    unittest.main()

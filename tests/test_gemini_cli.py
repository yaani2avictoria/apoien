import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location('gemini_cli', Path(__file__).resolve().parents[1]/'tools/testar_gemini_youtube.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class GeminiCLI(unittest.TestCase):
    def run_cli(self, response, directory):
        destination = Path(directory)/'result.json'
        args = ['script', '--free-tier-confirmed', '--url', 'https://youtu.be/abcdefghijk',
                '--start-seconds', '270', '--duration-seconds', '20', '--output', str(destination)]
        with patch('sys.argv', args), patch.dict(cli.os.environ, {'GEMINI_API_KEY': 'test-placeholder'}), patch.object(cli.urllib.request, 'urlopen', return_value=io.StringIO(json.dumps(response))) as request, patch('sys.stdout', new_callable=io.StringIO):
            status = cli.main()
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload['contents'][0]['parts'][0]['video_metadata'], {'start_offset':'270s','end_offset':'290s'})
        self.assertEqual(payload['contents'][0]['parts'][0]['file_data']['file_uri'], 'https://www.youtube.com/watch?v=abcdefghijk')
        return status, destination

    def test_complete_response_exports_text_without_claiming_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, p = self.run_cli({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Fala de teste.'}]}}]}, tmp)
            self.assertEqual(status, 0)
            self.assertEqual(p.with_suffix('.txt').read_text(), 'Fala de teste.\n')
            self.assertFalse(json.loads(p.read_text())['verified_transcription'])

    def test_truncated_response_preserves_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, p = self.run_cli({'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'Trecho incompleto'}]}}]}, tmp)
            self.assertEqual(status, 1)
            self.assertTrue(p.exists())
            self.assertFalse(p.with_suffix('.txt').exists())

    def test_quota_error_does_not_retry(self):
        error = urllib.error.HTTPError('https://example.test', 429, 'Quota', {}, io.BytesIO(b'{"error":{"message":"Quota exceeded"}}'))
        with patch('sys.argv',['script','--free-tier-confirmed']), patch.dict(cli.os.environ,{'GEMINI_API_KEY':'test-placeholder'}), patch.object(cli.urllib.request,'urlopen',side_effect=error) as request, patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(cli.main(),1)
            self.assertEqual(request.call_count,1)

    def test_full_video_omits_crop_and_sets_output_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = ['script', '--free-tier-confirmed', '--full-video', '--output', str(Path(tmp)/'whole.json')]
            response = {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Texto simulado.'}]}}]}
            with patch('sys.argv', args), patch.dict(cli.os.environ,{'GEMINI_API_KEY':'test-placeholder'}), patch.object(cli.urllib.request,'urlopen',return_value=io.StringIO(json.dumps(response))) as request, patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(cli.main(),0)
            payload = json.loads(request.call_args.args[0].data)
            self.assertNotIn('video_metadata',payload['contents'][0]['parts'][0])
            self.assertEqual(payload['generationConfig']['maxOutputTokens'],32768)
            result=json.loads((Path(tmp)/'whole.json').read_text())
            self.assertEqual(result['requested_scope'],'full_video')
            self.assertIsNone(result['requested_range_seconds'])

    def test_full_video_explicit_end_covers_thirteen_minutes(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)/'whole.json'
            args = ['script', '--free-tier-confirmed', '--full-video', '--full-end-seconds', '780', '--output', str(destination)]
            response = {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Texto simulado.'}]}}]}
            with patch('sys.argv', args), patch.dict(cli.os.environ,{'GEMINI_API_KEY':'test-placeholder'}), patch.object(cli.urllib.request,'urlopen',return_value=io.StringIO(json.dumps(response))) as request, patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(cli.main(),0)
            payload=json.loads(request.call_args.args[0].data)
            self.assertEqual(payload['contents'][0]['parts'][0]['video_metadata'],{'start_offset':'0s','end_offset':'780s'})
            self.assertEqual(json.loads(destination.read_text())['requested_range_seconds'],[0,780])
            self.assertEqual(request.call_count,1)

    def test_whitespace_is_not_a_transcription(self):
        with tempfile.TemporaryDirectory() as tmp:
            status,p=self.run_cli({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':' \n\t'}]}}]},tmp)
            self.assertEqual(status,1)
            self.assertTrue(p.exists())
            self.assertFalse(p.with_suffix('.txt').exists())

    def test_saved_matching_response_reuses_without_second_api_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,destination=self.run_cli({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Fala em cache.'}]}}]},tmp)
            args=['script','--free-tier-confirmed','--reuse-result','--url','https://youtu.be/abcdefghijk','--start-seconds','270','--duration-seconds','20','--output',str(destination)]
            with patch('sys.argv',args), patch.object(cli.urllib.request,'urlopen') as request, patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(cli.main(),0)
            request.assert_not_called()

    def test_mismatching_request_never_overwrites_saved_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,destination=self.run_cli({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Original'}]}}]},tmp)
            original=destination.read_bytes()
            args=['script','--free-tier-confirmed','--reuse-result','--url','https://youtu.be/abcdefghijk','--start-seconds','280','--output',str(destination)]
            with patch('sys.argv',args), patch.object(cli.urllib.request,'urlopen') as request, patch('sys.stdout',new_callable=io.StringIO):
                self.assertEqual(cli.main(),1)
            request.assert_not_called()
            self.assertEqual(destination.read_bytes(),original)

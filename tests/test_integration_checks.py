import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from transcritor import integration_checks as checks


class IntegrationChecks(unittest.TestCase):
    def test_caption_json3_keeps_real_timestamps_and_limits_sample(self):
        result=checks.json3_segments({'events':[
            {'tStartMs':1000,'dDurationMs':2000,'segs':[{'utf8':'Olá '},{'utf8':'mundo'}]},
            {'tStartMs':119000,'dDurationMs':3000,'segs':[{'utf8':'Final'}]},
            {'tStartMs':130000,'dDurationMs':1000,'segs':[{'utf8':'Fora'}]}]})
        self.assertEqual(result,[{'start':1.0,'end':3.0,'text':'Olá mundo'},{'start':119.0,'end':120,'text':'Final'}])

    def test_invalid_caption_timestamps_are_not_exported(self):
        with self.assertRaises(ValueError):
            checks.bounded_segments([{'start':float('nan'),'end':4,'text':'X'}])

    def test_samples_export_actual_text_four_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            result=checks.save_sample(out,'provider','pt',True,[{'start':1.25,'end':2.5,'text':'Teste real de formato'}])
            self.assertEqual(result['status'],'passed')
            self.assertIn('00:00:01.250 --> 00:00:02.500',(out/'provider.vtt').read_text())
            self.assertEqual(json.loads((out/'provider.json').read_text())['segments'][0]['start'],1.25)
            self.assertEqual(len(list(out.iterdir())),4)

    def test_empty_sample_creates_no_fake_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(checks.save_sample(Path(tmp),'provider','en',True,[])['status'],'unavailable')
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_auth_flag_is_required_before_network(self):
        with patch('sys.argv',['script']), patch.dict(checks.os.environ,{'TEST_AUTHORIZED':'false'}), patch.object(checks,'connectivity') as request, patch('sys.stderr',new_callable=io.StringIO):
            with self.assertRaises(SystemExit):checks.main()
        request.assert_not_called()

    def test_network_failure_skips_both_tools_and_writes_report(self):
        connectivity={label:{'dns':{'status':'resolved'},'https':{'status':'failed','category':'proxy_policy_denied'}} for label in ['general','youtube']}
        with tempfile.TemporaryDirectory() as tmp, patch('sys.argv',['script','--authorized','--mode','all','--output',tmp]), patch.object(checks,'connectivity',return_value=connectivity), patch.object(checks,'yt_metadata') as metadata, patch.object(checks,'library_captions') as captions, patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(checks.main(),2)
            report=json.loads((Path(tmp)/'report.json').read_text())
            self.assertFalse(report['gemini_called']);self.assertFalse(report['media_downloaded'])
            self.assertEqual(report['checks']['yt_dlp_metadata']['status'],'not_run')
        metadata.assert_not_called();captions.assert_not_called()

    def test_special_library_failures_are_distinguished(self):
        blocked=type('RequestBlocked',(Exception,),{})('blocked')
        disabled=type('TranscriptsDisabled',(Exception,),{})('disabled')
        self.assertEqual(checks.failure(blocked)['category'],'platform_access_restriction')
        self.assertEqual(checks.failure(disabled)['status'],'unavailable')

    def test_caption_destination_cannot_be_an_arbitrary_service(self):
        info={'subtitles':{'en':[{'ext':'json3','url':'https://other.example/private?token=secret'}]}}
        with tempfile.TemporaryDirectory() as tmp, patch.object(checks.urllib.request,'urlopen') as request:
            result=checks.ytdlp_captions(info,'en',Path(tmp))
        self.assertEqual(result['category'],'unexpected_caption_destination');request.assert_not_called()

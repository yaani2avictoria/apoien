import importlib.util
from pathlib import Path
import json
import unittest
spec=importlib.util.spec_from_file_location('annotations',Path(__file__).resolve().parents[1]/'tools/annotate_actions_report.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ActionsAnnotations(unittest.TestCase):
    def test_summary_excludes_media_urls_text_and_credentials(self):
        report={'schema':1,'video_id':'65uBZ-kaWzc','checks':{
            'yt_dlp_metadata':{'status':'failed','error':'https://host.test/?signature=private','raw_info':{'url':'secret'}},
            'youtube_transcript_api':{'status':'passed','segments':2,'text':'unpublished caption'}}}
        text=json.dumps(module.compact_report(report))
        self.assertNotIn('signature',text)
        self.assertNotIn('unpublished caption',text)
        self.assertNotIn('raw_info',text)
        self.assertIn('segments',text)

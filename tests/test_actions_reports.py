import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('read_actions_report',Path(__file__).resolve().parents[1]/'tools/read_actions_report.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)


class ActionsReports(unittest.TestCase):
    def test_zip_is_read_without_extracting_other_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'artifact.zip'
            report={'schema':1,'tests_run':26,'failures':0,'errors':0,'skipped':0,'runner':{'run_id':'42'}}
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('summary.json',json.dumps(report));z.writestr('../../unwanted.txt','never extract')
            data=reader.read_reports(path,'42')
            self.assertEqual(data[0]['tests_run'],26)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()),['artifact.zip'])

    def test_run_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            reader.summarize({'schema':1,'tests_run':1,'runner':{'run_id':'old'}},'new')

    def test_unknown_schema_is_rejected(self):
        with self.assertRaises(ValueError):reader.summarize({'schema':9,'tests_run':1})

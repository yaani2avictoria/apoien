"""Inspect downloaded development artifacts without extracting or executing files."""
import argparse
import json
from pathlib import Path
import zipfile

LIMIT=2*1024*1024


def summarize(data, expected_run=None):
    if data.get('schema')!=1:
        raise ValueError('Unknown report schema')
    runner=data.get('runner',{})
    if expected_run and str(runner.get('run_id'))!=str(expected_run):
        raise ValueError('Run ID does not match the requested run')
    if 'tests_run' in data:
        return {'kind':'unit_tests','tests_run':data['tests_run'],'failures':data.get('failures'),
                'errors':data.get('errors'),'skipped':data.get('skipped'),
                'dependency_smoke':data.get('dependency_smoke'),'runner':runner}
    if isinstance(data.get('checks'),dict):
        return {'kind':'youtube_diagnostics','status':data.get('status'),'video_id':data.get('video_id'),
                'runner':runner,'checks':data['checks'],'gemini_called':data.get('gemini_called'),
                'media_downloaded':data.get('media_downloaded')}
    raise ValueError('Not a recognized Actions development report')


def read_reports(path, expected_run=None):
    reports=[]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            entries=[f for f in archive.infolist() if Path(f.filename).name in ('summary.json','report.json')]
            if not 1<=len(entries)<=10:
                raise ValueError('Expected 1–10 report files')
            for info in entries:
                if info.file_size>LIMIT:
                    raise ValueError('Report exceeds 2 MiB')
                # No filesystem extraction; member names cannot overwrite anything.
                with archive.open(info) as stream:raw=stream.read(LIMIT+1)
                if len(raw)>LIMIT:raise ValueError('Report exceeds 2 MiB')
                reports.append(summarize(json.loads(raw),expected_run))
    else:
        if path.stat().st_size>LIMIT:raise ValueError('Report exceeds 2 MiB')
        reports.append(summarize(json.loads(path.read_text()),expected_run))
    return reports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact',type=Path)
    parser.add_argument('--expected-run')
    args=parser.parse_args()
    try:
        print(json.dumps(read_reports(args.artifact,args.expected_run),ensure_ascii=False,indent=2))
    except (ValueError,OSError,zipfile.BadZipFile) as exc:
        print(f'Invalid artifact: {type(exc).__name__}')
        return 1
    print('Artifact metadata is not cryptographic proof of origin; confirm the run in GitHub.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

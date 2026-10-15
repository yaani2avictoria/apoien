"""Expose a bounded diagnostic summary through normal Actions check annotations."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from transcritor.diagnostico import safe_error


def compact_report(report):
    result={k:report.get(k) for k in ['schema','video_id','status','packages','runner','gemini_called','media_downloaded']}
    checks=report.get('checks',{})
    result['connectivity']={name:{'dns_status':item.get('dns',{}).get('status'),
                                 'https':item.get('https',{})} for name,item in checks.get('connectivity',{}).items()}
    for name in ['yt_dlp_metadata','youtube_transcript_api','yt_dlp_captions']:
        item=checks.get(name,{})
        result[name]={k:item[k] for k in ['status','category','exception_type','http_status','exit_code','language','generated','segments'] if k in item}
        if item.get('error'):result[name]['error']=safe_error(item['error'])
        for field in ['manual_languages','automatic_languages']:
            if field in item:result[name][field]=item[field][:10]
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args()
    if not a.report.is_file():
        print('No diagnostic report was generated; consult the failed setup step.')
        return 0
    if a.report.stat().st_size>2*1024*1024:
        p.error('Diagnostic report too large')
    result=compact_report(json.loads(a.report.read_text()))
    text=json.dumps(result,ensure_ascii=True,separators=(',',':'))
    if len(text)>8000:p.error('Summary too large')
    escaped=text.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print('::notice title=YouTube diagnostic result::'+escaped)
    return 0


if __name__=='__main__':raise SystemExit(main())

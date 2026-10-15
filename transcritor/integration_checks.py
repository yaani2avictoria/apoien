"""Manual development integration checks. Never invokes Gemini or downloads media."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .sources import youtube_id, TranscriptionError
from .export import export, timestamp
from .diagnostico import classify, safe_error

MAX_CAPTION_BYTES = 2 * 1024 * 1024
SAMPLE_SECONDS = 120


def failure(exc, status=None):
    name=type(exc).__name__
    if name in ('TranscriptsDisabled','NoTranscriptFound'):
        return {'status':'unavailable','category':'captions_unavailable','exception_type':name}
    if name in ('RequestBlocked','IpBlocked','PoTokenRequired'):
        return {'status':'failed','category':'platform_access_restriction','exception_type':name}
    if name in ('VideoUnavailable','VideoUnplayable') or 'this video is unavailable' in str(exc).lower():
        return {'status':'unavailable','category':'video_unavailable','exception_type':name}
    code = status if status is not None else getattr(exc, 'code', None)
    return {'status': 'failed', 'category': classify(exc, code),
            'exception_type': type(exc).__name__, 'http_status': code, 'error': safe_error(exc)}


def connectivity():
    checks = {}
    for label, host in [('general', 'example.com'), ('youtube', 'www.youtube.com')]:
        try:
            count = len({v[4][0] for v in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
            dns = {'status': 'resolved', 'address_count': count}
        except OSError as exc:
            dns = {'status': 'failed', 'error': safe_error(exc)}
        url = f'https://{host}' + ('/robots.txt' if label=='youtube' else '/')
        started = time.monotonic()
        try:
            request = urllib.request.Request(url, method='HEAD' if label=='general' else 'GET')
            with urllib.request.urlopen(request, timeout=12) as response:
                response.read(128)
                http = {'status': 'passed', 'http_status': response.status,
                        'final_host': urlsplit(response.url).hostname}
        except Exception as exc:
            http = failure(exc)
        checks[label] = {'dns': dns, 'https': http, 'elapsed_seconds': round(time.monotonic()-started,3)}
    return checks


def yt_metadata(url):
    # Isolate the extractor, disable user config/plugins/cookies, no downloads or retries.
    command = [sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-plugin-dirs',
               '--skip-download', '--no-playlist', '--no-cache-dir', '--retries', '0',
               '--extractor-retries', '0', '--socket-timeout', '10', '--js-runtimes', 'node', '--dump-single-json', url]
    try:
        process = subprocess.run(command, text=True, capture_output=True, timeout=50)
    except subprocess.TimeoutExpired as exc:
        return failure(exc), None
    if process.returncode:
        return dict(failure(process.stderr), exit_code=process.returncode), None
    try:
        info = json.loads(process.stdout)
    except ValueError as exc:
        return failure(exc), None
    if info.get('_type') in ('playlist', 'multi_video'):
        return {'status':'failed', 'category':'not_a_single_video'}, None
    return {'status':'passed', 'id':info.get('id'), 'title':str(info.get('title',''))[:200],
            'duration_seconds':info.get('duration'), 'availability':info.get('availability'),
            'manual_languages':sorted((info.get('subtitles') or {}).keys()),
            'automatic_languages':sorted((info.get('automatic_captions') or {}).keys()),
            'automatic_languages_may_include_translations':True}, info


def bounded_segments(values):
    out = []
    for item in values:
        start, end = float(item['start']), float(item['end'])
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end < start:
            raise ValueError('Invalid caption timestamps')
        text = str(item['text']).strip()
        if start >= SAMPLE_SECONDS or not text or end == start:
            continue
        out.append({'start':start, 'end':min(end, SAMPLE_SECONDS), 'text':text})
        if len(out) >= 600:
            break
    return out


def json3_segments(data):
    segments=[]
    for event in data.get('events', []):
        text=''.join(s.get('utf8','') for s in event.get('segs',[])).strip()
        if text and 'tStartMs' in event:
            start=event['tStartMs']/1000
            segments.append({'start':start,'end':start+event.get('dDurationMs',0)/1000,'text':text})
    return bounded_segments(segments)


def save_sample(output, provider, language, generated, segments):
    if not segments:
        return {'status':'unavailable','category':'no_captions_in_first_120_seconds'}
    data={'source':provider, 'language':language, 'generated':generated,
          'scope':'caption_sample_first_120_seconds', 'verified_transcription':False, 'segments':segments}
    destination=output/provider
    export(data,destination)
    vtt='WEBVTT\n\n'+'\n\n'.join(
        f"{timestamp(s['start']).replace(',', '.')} --> {timestamp(s['end']).replace(',', '.')}\n{s['text']}"
        for s in segments)+'\n'
    destination.with_suffix('.vtt').write_text(vtt,encoding='utf-8')
    return {'status':'passed','language':language,'generated':generated,'segments':len(segments),
            'sample_limit_seconds':SAMPLE_SECONDS,'files':[provider+ext for ext in ['.json','.txt','.srt','.vtt']]}


def library_captions(video_id, language, output):
    try:
        import requests
        from youtube_transcript_api import YouTubeTranscriptApi
        class Session(requests.Session):
            def request(self,*args,**kwargs):
                kwargs.setdefault('timeout',10)
                return super().request(*args,**kwargs)
        with Session() as session:
            tracks=YouTubeTranscriptApi(http_client=session).list(video_id)
            inventory=[{'language':t.language_code,'generated':t.is_generated} for t in tracks]
            selected=next((t for t in tracks if t.language_code==language and not t.is_generated),None)
            if selected is None:
                selected=next((t for t in tracks if t.language_code==language),None)
            if selected is None:
                return {'status':'unavailable','category':'requested_language_not_available','tracks':inventory}
            fetched=selected.fetch()
            segments=bounded_segments({'start':s.start,'end':s.start+s.duration,'text':s.text} for s in fetched)
            return dict(save_sample(output,'youtube_transcript_api',language,selected.is_generated,segments),tracks=inventory)
    except Exception as exc:
        return failure(exc)


def ytdlp_captions(info, language, output):
    manual=(info.get('subtitles') or {}).get(language)
    generated=not bool(manual)
    formats=manual or (info.get('automatic_captions') or {}).get(language) or []
    if not formats:
        return {'status':'unavailable','category':'requested_language_not_available'}
    selected=next((item for item in formats if item.get('ext')=='json3'),None)
    if not selected:
        return {'status':'unavailable','category':'json3_format_not_available'}
    url=selected.get('url','');p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in ('www.youtube.com','youtube.com') or p.username or p.password:
        return {'status':'failed','category':'unexpected_caption_destination'}
    try:
        with urllib.request.urlopen(url,timeout=10) as response:
            final=urlsplit(response.url)
            if final.scheme!='https' or final.hostname not in ('www.youtube.com','youtube.com'):
                return {'status':'failed','category':'unexpected_caption_redirect'}
            raw=response.read(MAX_CAPTION_BYTES+1)
        if len(raw)>MAX_CAPTION_BYTES:
            return {'status':'failed','category':'caption_size_limit'}
        return save_sample(output,'yt_dlp',language,generated,json3_segments(json.loads(raw)))
    except Exception as exc:
        return failure(exc)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default=os.getenv('TEST_VIDEO_URL','https://www.youtube.com/watch?v=BaW_jenozKc'))
    parser.add_argument('--language',default=os.getenv('TEST_LANGUAGE','en'))
    parser.add_argument('--mode',choices=['connectivity','metadata','captions','all'],default=os.getenv('TEST_MODE','connectivity'))
    parser.add_argument('--authorized',action='store_true',default=os.getenv('TEST_AUTHORIZED','').lower()=='true')
    parser.add_argument('--output',type=Path,default=Path('artifacts/youtube-diagnostics'))
    args=parser.parse_args()
    if args.mode not in ('connectivity','metadata','captions','all'):
        parser.error('Invalid test mode.')
    if not args.authorized:
        parser.error('This is a development test; confirm authorization for the public test fixture.')
    try: video=youtube_id(args.url)
    except TranscriptionError: video=None
    if not video or urlsplit(args.url).username or urlsplit(args.url).password:
        parser.error('Expected a single HTTPS YouTube video URL without credentials.')
    if not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',args.language):
        parser.error('Invalid language code.')
    if (args.output/'report.json').exists():
        parser.error('Report already exists; select a new output directory.')
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    versions={}
    for name in ['yt-dlp','yt-dlp-ejs','youtube-transcript-api','requests']:
        try: versions[name]=version(name)
        except PackageNotFoundError: versions[name]=None
    report={'schema':1,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'video_id':video,
            'mode':args.mode,'language':args.language,'packages':versions,
            'runner':{'github_actions':os.getenv('GITHUB_ACTIONS')=='true','run_id':os.getenv('GITHUB_RUN_ID')},
            'gemini_called':False,'media_downloaded':False,'checks':{}}
    checks=report['checks']; checks['connectivity']=connectivity()
    reachable=checks['connectivity']['youtube']['https']['status']=='passed'
    if not reachable:
        checks['yt_dlp_metadata']={'status':'not_run','category':'network_prerequisite_failed'}
        checks['youtube_transcript_api']={'status':'not_run','category':'network_prerequisite_failed'}
        checks['yt_dlp_captions']={'status':'not_run','category':'network_prerequisite_failed'}
    else:
        info=None
        if args.mode in ('metadata','captions','all'):
            if versions['yt-dlp']:
                checks['yt_dlp_metadata'],info=yt_metadata(f'https://www.youtube.com/watch?v={video}')
            else: checks['yt_dlp_metadata']={'status':'not_run','category':'dependency_missing'}
        if args.mode in ('captions','all'):
            checks['youtube_transcript_api']=library_captions(video,args.language,args.output)
            checks['yt_dlp_captions']=(ytdlp_captions(info,args.language,args.output) if info else
                                      {'status':'not_run','category':'metadata_prerequisite_failed'})
    statuses=[item['https']['status'] for item in checks['connectivity'].values()]
    statuses += [item['status'] for name,item in checks.items() if name!='connectivity']
    report['status']='passed' if all(s=='passed' for s in statuses) else 'incomplete_or_failed'
    report['elapsed_seconds']=round(time.monotonic()-started,3)
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (args.output/'summary.md').write_text('# YouTube development diagnostics\n\n'+
        f"Status: {report['status']}\n\nSee report.json for independent checks. Caption files are limited to the first 120 seconds; they are not full transcripts. No Gemini or media download.\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' else 2


if __name__=='__main__':
    raise SystemExit(main())

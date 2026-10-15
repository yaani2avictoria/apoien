import json
from pathlib import Path


def timestamp(seconds):
    ms = max(0, round(seconds * 1000))
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def export(result, destination):
    base = Path(destination)
    base.parent.mkdir(parents=True, exist_ok=True)
    segments = result['segments']
    base.with_suffix('.txt').write_text('\n'.join(s['text'] for s in segments)+'\n', encoding='utf-8')
    base.with_suffix('.srt').write_text('\n\n'.join(
        f"{i}\n{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text']}"
        for i, s in enumerate(segments, 1))+'\n', encoding='utf-8')
    base.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

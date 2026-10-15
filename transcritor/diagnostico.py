"""Diagnóstico opcional sem downloads de mídia ou chamadas Gemini."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .sources import youtube_id, TranscriptionError

SCHEMA = 1
TTL = 600


def classify(message, status=None):
    text = str(message).lower()
    if 'tunnel connection failed: 403' in text:
        return 'proxy_policy_denied'
    if 'proxy' in text and any(x in text for x in ['refused', 'resolve', 'connect', '403']):
        return 'proxy_connection_failed'
    if status is None:
        match = re.search(r'\bhttp(?: error)?[\s:]+(401|403|429)\b', text)
        if match:
            status = int(match.group(1))
    if status == 429 or 'too many requests' in text:
        return 'rate_limited'
    if status == 401:
        return 'authentication_required'
    if status == 403:
        return 'http_access_denied'
    if any(x in text for x in ['sign in', 'captcha', 'not a bot', 'private video', 'login required']):
        return 'access_restriction'
    if any(x in text for x in ['name resolution', 'getaddrinfo', 'name or service not known']):
        return 'dns_failed'
    if 'timed out' in text or 'timeout' in text:
        return 'timeout'
    return 'network_or_extraction_failed'


def safe_error(message):
    # Never return signed URLs, headers, proxy userinfo, cookies or key-like strings.
    text = re.sub(r'(?im)^.*\b(cookie|authorization|api[_ -]?key|access[_ -]?token)\s*[:=].*$', '[credencial omitida]', str(message))
    text = re.sub(r'https?://\S+', '[URL omitida]', text)
    text = re.sub(r'AIza[A-Za-z0-9_-]+', '[CHAVE omitida]', text)
    text = re.sub(r'(?i)(cookie|authorization|api.key|token)\s*[:=]\s*\S+', r'\1=[omitido]', text)
    return re.sub(r'\x1b\[[0-9;]*m', '', text)[:500]


def read_policy(path=Path('/etc/codex/network-policy.json')):
    try:
        value = json.loads(path.read_text())
        if value.get('version') != 1:
            return None
        return value.get('http_network_policy')
    except (OSError, ValueError):
        return None


def host_permitted(host, policy):
    if not policy:
        return None
    mode = policy.get('type')
    if mode == 'unrestricted':
        return True  # Desired snapshot only; the request must still succeed.
    if mode == 'disabled':
        return False
    if mode != 'restricted':
        return None
    for rule in policy.get('egress_rules', []):
        pattern = rule.get('host', '').lower()
        if pattern == '*' or host == pattern:
            return True
        if pattern.startswith('*.') and host.endswith(pattern[1:]):
            return True
    return False


def https_probe():
    url = 'https://www.youtube.com/robots.txt'
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            sample = response.read(128)
            return {'status': 'reachable', 'http_status': response.status,
                    'final_host': urlsplit(response.url).hostname,
                    'sample_bytes': len(sample), 'elapsed_seconds': round(time.monotonic()-started, 3)}
    except Exception as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        return {'status': 'failed', 'category': classify(exc, status),
                'http_status': status, 'error': safe_error(exc),
                'elapsed_seconds': round(time.monotonic()-started, 3)}


def metadata_probe(url):
    command = [sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-plugin-dirs',
               '--skip-download', '--no-playlist', '--retries', '0', '--extractor-retries', '0',
               '--socket-timeout', '10', '--no-cache-dir', '--dump-single-json', url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return {'status': 'failed', 'category': 'timeout'}
    if result.returncode:
        return {'status': 'failed', 'category': classify(result.stderr),
                'exit_code': result.returncode, 'error': safe_error(result.stderr)}
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return {'status': 'failed', 'category': 'invalid_metadata_response'}
    return {'status': 'passed', 'id': data.get('id'), 'title': data.get('title'),
            'duration_seconds': data.get('duration'), 'availability': data.get('availability'),
            'formats_count': len(data.get('formats') or [])}


def audit(url, check_metadata=False, policy=None):
    video = youtube_id(url)
    if not video:
        raise TranscriptionError('Informe URL HTTPS válida do YouTube.')
    canonical = f'https://www.youtube.com/watch?v={video}'
    try:
        yt_version = version('yt-dlp')
    except PackageNotFoundError:
        yt_version = None
    result = {'schema': SCHEMA, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'video_id': video, 'gemini_called': False, 'media_downloaded': False,
              'yt_dlp_version': yt_version, 'network_policy_type': (policy or {}).get('type'),
              'network_policy_source': 'startup_snapshot_not_runtime_readiness', 'dns': {}}
    for host in ['youtube.com', 'www.youtube.com']:
        try:
            count = len({x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
            result['dns'][host] = {'status': 'resolved', 'address_count': count}
        except OSError as exc:
            result['dns'][host] = {'status': 'failed', 'category': 'dns_failed', 'error': safe_error(exc)}
    permitted = host_permitted('www.youtube.com', policy)
    if permitted is False:
        result['https'] = {'status': 'not_run', 'category': 'policy_excludes_destination',
                           'note': 'Sem requisição: o snapshot local não permite www.youtube.com.'}
    else:
        result['https'] = https_probe()
    if not check_metadata:
        result['metadata'] = {'status': 'not_requested'}
    elif result['https']['status'] != 'reachable':
        result['metadata'] = {'status': 'not_run', 'category': 'network_prerequisite_failed'}
    elif yt_version is None:
        result['metadata'] = {'status': 'not_run', 'category': 'dependency_missing'}
    else:
        result['metadata'] = metadata_probe(canonical)
    result['direct_access_ready'] = result['metadata']['status'] == 'passed'
    result['next_action'] = ('Metadados disponíveis; acesso ao áudio ainda precisa de validação e autorização.'
                             if result['direct_access_ready'] else
                             'Corrigir o pré-requisito indicado; arquivo autorizado + Whisper é alternativa. Gemini somente com autorização explícita.')
    return result


def cached_audit(url, check_metadata, policy, cache_dir, refresh=False):
    video = youtube_id(url)
    if not video:
        raise TranscriptionError('URL inválida.')
    try:
        yt_version = version('yt-dlp')
    except PackageNotFoundError:
        yt_version = None
    identity = {'schema': SCHEMA, 'video': video, 'metadata': check_metadata,
                'policy': policy, 'yt_dlp': yt_version, 'python': sys.version}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    target = Path(cache_dir)/(digest+'.json')
    if not refresh:
        try:
            saved = json.loads(target.read_text())
            age = time.time()-saved['saved_at']
            if 0 <= age < TTL:
                return dict(saved['result'], cache_hit=True, cache_age_seconds=round(age, 2))
        except (OSError, ValueError, KeyError, TypeError):
            pass
    result = audit(url, check_metadata, policy)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=target.parent, delete=False) as stream:
        json.dump({'saved_at': time.time(), 'result': result}, stream)
        temporary = Path(stream.name)
    temporary.replace(target)
    return dict(result, cache_hit=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--check-metadata', action='store_true', help='Executar yt-dlp só se a conectividade funcionar.')
    parser.add_argument('--refresh', action='store_true', help='Autoriza refazer diagnóstico agora, ignorando o cache.')
    parser.add_argument('--cache-dir', type=Path, default=Path('.cache/diagnostico'))
    args = parser.parse_args()
    try:
        result = cached_audit(args.url, args.check_metadata, read_policy(), args.cache_dir, args.refresh)
    except (TranscriptionError, OSError) as exc:
        print(json.dumps({'status': 'failed', 'error': safe_error(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['direct_access_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

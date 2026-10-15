import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from transcritor import diagnostico as d

URL='https://www.youtube.com/watch?v=nkjymufhKpU'


class Diagnostics(unittest.TestCase):
    def test_proxy_denial_is_not_site_authentication(self):
        self.assertEqual(d.classify('Tunnel connection failed: 403 Forbidden'),'proxy_policy_denied')
        self.assertEqual(d.classify('Forbidden',403),'http_access_denied')
        self.assertEqual(d.classify('ERROR: HTTP Error 403: Forbidden'),'http_access_denied')
        self.assertEqual(d.classify('Denied',401),'authentication_required')
        self.assertEqual(d.classify('rate limit',429),'rate_limited')

    def test_host_patterns_do_not_authorize_lookalikes(self):
        policy={'type':'restricted','egress_rules':[{'host':'*.googlevideo.com'}]}
        self.assertTrue(d.host_permitted('rr1.googlevideo.com',policy))
        self.assertFalse(d.host_permitted('googlevideo.com.evil.test',policy))
        self.assertIsNone(d.host_permitted('www.youtube.com',None))

    def test_policy_denial_skips_https_and_extractor(self):
        with patch.object(d.socket,'getaddrinfo',return_value=[]), patch.object(d,'https_probe') as https, patch.object(d,'metadata_probe') as metadata:
            result=d.audit(URL,True,{'type':'restricted','egress_rules':[{'host':'generativelanguage.googleapis.com'}]})
        https.assert_not_called(); metadata.assert_not_called()
        self.assertEqual(result['https']['category'],'policy_excludes_destination')
        self.assertFalse(result['gemini_called'])

    def test_runtime_denial_skips_extractor_even_with_unrestricted_snapshot(self):
        with patch.object(d.socket,'getaddrinfo',return_value=[]), patch.object(d,'https_probe',return_value={'status':'failed','category':'proxy_policy_denied'}), patch.object(d,'metadata_probe') as metadata:
            result=d.audit(URL,True,{'type':'unrestricted'})
        metadata.assert_not_called()
        self.assertEqual(result['metadata']['category'],'network_prerequisite_failed')

    def test_cached_failure_does_not_repeat_until_policy_changes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'audit',return_value={'direct_access_ready':False}) as audit:
            d.cached_audit(URL,True,{'type':'restricted'},tmp)
            self.assertTrue(d.cached_audit(URL,True,{'type':'restricted'},tmp)['cache_hit'])
            self.assertEqual(audit.call_count,1)
            d.cached_audit(URL,True,{'type':'unrestricted'},tmp)
            self.assertEqual(audit.call_count,2)
            d.cached_audit(URL,True,{'type':'unrestricted'},tmp,refresh=True)
            self.assertEqual(audit.call_count,3)

    def test_signed_urls_and_authorization_are_removed(self):
        message='https://user:password@host.test/media?signature=secret\nAuthorization: Bearer sensitive\nCookie: private'
        redacted=d.safe_error(message)
        for value in ['password','signature','sensitive','private']:
            self.assertNotIn(value,redacted)

    def test_metadata_exports_only_allowlisted_fields(self):
        info={'id':'abc','title':'Title','duration':30,'formats':[{'url':'https://host.test/?signature=secret'}],'cookies':'secret'}
        completed=subprocess.CompletedProcess([],0,json.dumps(info),'')
        with patch.object(d.subprocess,'run',return_value=completed) as run:
            result=d.metadata_probe(URL)
        command=run.call_args.args[0]
        self.assertIn('--skip-download',command);self.assertIn('--ignore-config',command)
        self.assertIn('--no-plugin-dirs',command)
        self.assertNotIn('signature',json.dumps(result))
        self.assertNotIn('cookies',result)
        self.assertEqual(result['formats_count'],1)

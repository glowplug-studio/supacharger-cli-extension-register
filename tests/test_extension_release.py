import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_extension_release import update, verify, locate, main

NAME = 'supacharger-ext-invitations'
COMMIT = 'a' * 40


def archive(version='1.0.0', comment=COMMIT, extra=None):
    output = io.BytesIO()
    manifest = dict(schemaVersion=3, coreOwnershipVersion=2, name=NAME, version=version,
                    dependencies=[], core_services=['transactional_email'], files=[{'source': 'payload/app/index.ts'}])
    with zipfile.ZipFile(output, 'w') as z:
        z.comment = comment.encode()
        z.writestr(NAME + '/extension.json', json.dumps(manifest))
        z.writestr(NAME + '/package.json', json.dumps(dict(name=NAME, version=version)))
        z.writestr(NAME + '/payload/app/index.ts', 'export {}')
        if extra:
            z.writestr(extra, 'unexpected')
    return output.getvalue()


class ExtensionReleaseTests(unittest.TestCase):
    def setUp(self):
        self.record = dict(schemaVersion=2, name=NAME, version='', source_commit='',
                           requires_license=True, sellsource_url='https://example.com/licensed',
                           dependencies=[], core_services=[], version_history={})
        self.fields = verify(archive(), NAME, '1.0.0', COMMIT)

    def test_exact_bytes_hash(self):
        self.assertEqual(self.fields['archive_checksum']['value'], hashlib.sha256(archive()).hexdigest())

    def test_initial_preserves_licence_without_placeholder_history(self):
        result = update(self.record, self.fields)
        self.assertEqual(result['version_history'], {})
        self.assertTrue(result['requires_license'])
        self.assertEqual(result['sellsource_url'], self.record['sellsource_url'])

    def test_snapshot_and_retries(self):
        first = update(self.record, self.fields)
        second = update(first, {**self.fields, 'version': '1.1.0'})
        self.assertEqual(second['version_history']['1.0.0']['sellsource_url'], first['sellsource_url'])
        self.assertNotIn('schemaVersion', second['version_history']['1.0.0'])
        self.assertEqual(update(second, self.fields), second)
        self.assertEqual(update(first, self.fields), first)
        self.assertEqual(self.record['version'], '')

    def test_conflicting_retry(self):
        current = update(self.record, self.fields)
        with self.assertRaises(ValueError):
            update(current, {**self.fields, 'source_commit': 'b' * 40})

    def test_stale_release(self):
        current = update(self.record, self.fields)
        with self.assertRaises(ValueError):
            update(current, {**self.fields, 'version': '0.9.0'})

    def test_wrong_commit(self):
        with self.assertRaises(ValueError):
            verify(archive(comment='b' * 40), NAME, '1.0.0', COMMIT)

    def test_wrong_version(self):
        with self.assertRaises(ValueError):
            verify(archive(version='2.0.0'), NAME, '1.0.0', COMMIT)

    def test_unsafe_or_unlisted_payload(self):
        for extra in (NAME + '/../secret', NAME + '/payload/unlisted', '/absolute'):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                verify(archive(extra=extra), NAME, '1.0.0', COMMIT)

    def test_receiver_downloads_and_writes_verified_record(self):
        data = archive()
        def api(path, binary=False, repo=None):
            self.assertEqual(repo, 'glowplug-studio/' + NAME)
            if path.startswith('releases/tags/'):
                return dict(id=10, draft=False, published_at='2026-10-31', tag_name='v1.0.0')
            if path.startswith('commits/'):
                return {'sha': COMMIT}
            if path.startswith('releases/10/assets'):
                return [dict(name=NAME + '.zip', state='uploaded', id=20, size=len(data))]
            self.assertEqual(path, 'releases/assets/20')
            self.assertTrue(binary)
            return data
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'record.json'
            path.write_text(json.dumps(self.record))
            with patch.dict('os.environ', EXTENSION_NAME=NAME, RELEASE_TAG='v1.0.0'), patch('update_extension_release.locate', return_value=(path, self.record, 'glowplug-studio/' + NAME)), patch('update_extension_release.request', side_effect=api):
                main()
            result = json.loads(path.read_text())
            self.assertEqual(result['source_commit'], COMMIT)
            self.assertEqual(result['archive_checksum'], self.fields['archive_checksum'])

    def test_unregistered_name(self):
        for name in ('../core', 'supacharger-ext-unregistered'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                locate(name)


if __name__ == '__main__':
    unittest.main()

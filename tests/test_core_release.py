import copy
import importlib.util
import unittest
from unittest.mock import patch
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('updater', 'scripts/update_core_release.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.record = {'schemaVersion': 2, 'name': 'supacharger', 'version': '1.0.0',
                       'dependencies': ['example'], 'core_services': ['auth'],
                       'source_commit': 'a' * 40, 'download_url': 'old.zip',
                       'archive_checksum': {'algorithm': 'sha256', 'format': 'zip', 'value': '1' * 64},
                       'version_history': {}}

    def publish(self, record=None, version='1.1.0'):
        return updater.update(record or self.record, version, 'b' * 40, 'new.zip', '2' * 64)

    def test_snapshot_preserves_every_release_field(self):
        original = copy.deepcopy(self.record)
        result = self.publish()
        self.assertEqual(result['version_history']['1.0.0'], {k: v for k, v in original.items() if k not in ('schemaVersion', 'version_history')})
        self.assertEqual(result['dependencies'], ['example'])
        self.assertEqual(result['core_services'], ['auth'])
        self.assertNotIn('1.1.0', result['version_history'])
        self.assertEqual(self.record, original)

    def test_identical_retry_noop(self):
        first = self.publish()
        self.assertEqual(self.publish(first), first)

    def test_conflicting_retry_fails(self):
        with self.assertRaises(ValueError):
            updater.update(self.publish(), '1.1.0', 'c' * 40, 'new.zip', '2' * 64)

    def test_historical_retry_does_not_roll_back(self):
        first = self.publish()
        second = self.publish(first, '1.2.0')
        self.assertEqual(self.publish(second), second)

    def test_out_of_order_release_fails(self):
        with self.assertRaises(ValueError):
            self.publish(version='0.9.0')

    def test_unversioned_placeholder_has_no_snapshot(self):
        self.record['version'] = None
        self.assertEqual(self.publish()['version_history'], {})

    def test_semantic_version_ordering(self):
        values = ['1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.2', '1.0.0-alpha.10', '1.0.0-beta', '1.0.0-rc.1', '1.0.0', '1.1.0']
        self.assertEqual(sorted(reversed(values), key=updater.version_key), values)

    def test_invalid_versions(self):
        for version in ['main', '1.0', '01.0.0', '1.0.0-alpha..1', '1.0.0-01', '1.0.0+x..y']:
            with self.subTest(version=version), self.assertRaises(ValueError):
                updater.version_key(version)


class ArchiveTests(unittest.TestCase):
    def run_release(self, comment):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.comment = comment.encode()
            archive.writestr('supacharger/package.json', json.dumps({'name': 'supacharger'}))
        data = stream.getvalue()
        def api(path, binary=False):
            if path.startswith('releases/tags/'):
                return {'draft': False, 'published_at': '2026-10-29T00:00:00Z', 'tag_name': 'v1.1.0', 'id': 1}
            if path.startswith('commits/'):
                return {'sha': 'b' * 40}
            if path.startswith('releases/1/assets'):
                return [{'id': 2, 'name': 'supacharger.zip', 'state': 'uploaded', 'size': len(data),
                         'browser_download_url': 'https://github.com/glowplug-studio/supacharger/releases/download/v1.1.0/supacharger.zip'}]
            return data
        original_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                Path('core').mkdir()
                record = {'schemaVersion': 2, 'name': 'supacharger', 'version': None, 'dependencies': [], 'version_history': {}}
                Path('core/supacharger.json').write_text(json.dumps(record))
                with patch.dict(os.environ, {'RELEASE_TAG': 'v1.1.0'}), patch.object(updater, 'request', side_effect=api):
                    updater.main()
                return json.loads(Path('core/supacharger.json').read_text())
            finally:
                os.chdir(original_dir)

    def test_verified_archive_updates_record(self):
        result = self.run_release('b' * 40)
        self.assertEqual(result['source_commit'], 'b' * 40)
        self.assertEqual(len(result['archive_checksum']['value']), 64)
        self.assertEqual(result['version_history'], {})

    def test_wrong_commit_archive_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_release('c' * 40)


if __name__ == '__main__':
    unittest.main()

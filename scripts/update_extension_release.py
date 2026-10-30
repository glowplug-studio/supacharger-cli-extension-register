#!/usr/bin/env python3
"""Verify an extension's published ZIP and atomically advance its registry record."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote
import zipfile
from update_core_release import request, version_key


def locate(name):
    if not re.fullmatch(r'supacharger-ext-[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Invalid extension name')
    index = json.loads(Path('manifest.json').read_text())
    matches = [e for e in index['extensions'] if e['name'] == name]
    expected = 'extensions/' + name + '.json'
    if len(matches) != 1 or matches[0]['path'] != expected:
        raise ValueError('Extension must already have a registered record')
    path = Path(expected)
    record = json.loads(path.read_text())
    repo = 'glowplug-studio/' + name
    if record.get('schemaVersion') != 2 or record.get('name') != name:
        raise ValueError('Unexpected registry identity/schema')
    if record.get('github_repo_url') not in ('git@github.com:' + repo + '.git', 'https://github.com/' + repo, 'https://github.com/' + repo + '.git'):
        raise ValueError('Registry source repository mismatch')
    if not isinstance(record.get('requires_license'), bool) or (record['requires_license'] and not record.get('sellsource_url')):
        raise ValueError('Invalid licence metadata')
    return path, record, repo


def verify(archive, name, version, commit):
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        if zipped.testzip() is not None or zipped.comment.decode('ascii') != commit:
            raise ValueError('Damaged ZIP or source commit mismatch')
        names = zipped.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        for entry in zipped.infolist():
            parts = PurePosixPath(entry.filename).parts
            if not parts or parts[0] != name or '..' in parts or '\\' in entry.filename or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe ZIP entry')
        manifest = json.loads(zipped.read(name + '/extension.json'))
        package = json.loads(zipped.read(name + '/package.json'))
        if manifest.get('schemaVersion') != 3 or manifest.get('coreOwnershipVersion') != 2:
            raise ValueError('Unsupported extension contract')
        for document in (manifest, package):
            if document.get('name') != name or document.get('version') != version:
                raise ValueError('ZIP identity/version does not match release')
        for field in ('dependencies', 'core_services'):
            values = manifest.get(field)
            if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
                raise ValueError('Invalid ' + field)
        sources = [name + '/' + f['source'] for f in manifest['files']]
        payload = {n for n in names if n.startswith(name + '/payload/') and not n.endswith('/')}
        if len(sources) != len(set(sources)) or set(sources) != payload:
            raise ValueError('ZIP payload does not match ownership contract')
    return dict(version=version, source_commit=commit,
                dependencies=manifest['dependencies'], core_services=manifest['core_services'],
                archive_checksum=dict(algorithm='sha256', format='zip', value=hashlib.sha256(archive).hexdigest()))


def update(record, fields):
    version = fields['version']
    version_key(version)
    current = {k: v for k, v in record.items() if k not in ('schemaVersion', 'version_history')}
    history = dict(record['version_history'])
    if current.get('version') in history:
        raise ValueError('Current version must not appear in history')
    existing = current if current.get('version') == version else history.get(version)
    if existing is not None:
        if any(existing.get(k) != v for k, v in fields.items()):
            raise ValueError('Conflicting data for an existing version')
        return record
    if current.get('version'):
        if version_key(version) <= version_key(current['version']):
            raise ValueError('Refusing out-of-order release')
        history[current['version']] = current
    return {**record, **fields, 'version_history': history}


def main():
    name, tag = os.environ['EXTENSION_NAME'], os.environ['RELEASE_TAG']
    version = tag.removeprefix('v')
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('Expected a three-integer extension version')
    path, original, repo = locate(name)
    def api(path, binary=False):
        return request(path, binary=binary, repo=repo)
    release = api('releases/tags/' + quote(tag, safe=''))
    if release['draft'] or not release['published_at'] or release['tag_name'] != tag:
        raise ValueError('Expected a published release')
    commit = api('commits/' + quote(tag, safe=''))['sha']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid source commit')
    assets = api('releases/' + str(release['id']) + '/assets?per_page=100')
    matches = [a for a in assets if a['name'] == name + '.zip' and a['state'] == 'uploaded']
    if len(matches) != 1:
        raise ValueError('Expected one uploaded extension ZIP')
    asset = matches[0]
    archive = api('releases/assets/' + str(asset['id']), binary=True)
    fields = verify(archive, name, version, commit)
    if len(archive) != asset['size'] or (asset.get('digest') and asset['digest'] != 'sha256:' + fields['archive_checksum']['value']):
        raise ValueError('GitHub ZIP size/digest mismatch')
    result = update(original, fields)
    if result != original:
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        temporary.replace(path)
    print('Verified ' + name + ' ' + version + ('; registry updated' if result != original else '; already recorded'))


if __name__ == '__main__':
    main()

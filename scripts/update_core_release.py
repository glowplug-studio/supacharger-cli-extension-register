#!/usr/bin/env python3
"""Verify a published Core release and update its registry record."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
import zipfile

REPO = 'glowplug-studio/supacharger'
ASSET = 'supacharger.zip'


def request(path, binary=False):
    headers = {'Authorization': 'Bearer ' + os.environ['SC_RELEASE_TOKEN'],
               'Accept': 'application/octet-stream' if binary else 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'supacharger-registry'}
    req = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + path, headers=headers)
    # urllib strips neither arbitrary headers nor credentials on cross-host redirects.
    # Release asset redirects must therefore be followed without the API token.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=120) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        if not binary or error.code not in (301, 302, 303, 307, 308):
            raise
        location = error.headers['Location']
        if urllib.parse.urlsplit(location).scheme != 'https':
            raise ValueError('Non-HTTPS asset redirect')
        with urllib.request.urlopen(location, timeout=120) as response:
            data = response.read()
    return data if binary else json.loads(data)


def version_key(value):
    match = re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?', value)
    if not match:
        raise ValueError('Release tag must be a semantic version, optionally prefixed with v')
    pre = match[4]
    for part in (pre or '').split('.'):
        if pre and (not part or (part.isdigit() and len(part) > 1 and part.startswith('0'))):
            raise ValueError('Invalid prerelease version')
    if match[5] and any(not p for p in match[5].split('.')):
        raise ValueError('Invalid version build metadata')
    return (*map(int, match.group(1, 2, 3)), pre is None,
            tuple((0, int(p)) if p.isdigit() else (1, p) for p in pre.split('.')) if pre else ())


def update(record, version, commit, url, checksum):
    version_key(version)
    if record.get('schemaVersion') != 2 or record.get('name') != 'supacharger':
        raise ValueError('Unexpected registry schema or package')
    current = {k: v for k, v in record.items() if k not in ('schemaVersion', 'version_history')}
    history = record['version_history']
    if current.get('version') in history:
        raise ValueError('Current version must not appear in history')
    fields = dict(version=version, source_commit=commit, download_url=url,
                  archive_checksum=dict(algorithm='sha256', format='zip', value=checksum))
    existing = current if current.get('version') == version else history.get(version)
    if existing is not None:
        if any(existing.get(k) != v for k, v in fields.items()):
            raise ValueError('Conflicting data for an existing version')
        return record
    if current.get('version') and version_key(version) <= version_key(current['version']):
        raise ValueError('Refusing an out-of-order release or equal-precedence version')
    history = dict(history)
    if current.get('version'):
        history[current['version']] = current
    return {**record, **fields, 'version_history': history}


def main():
    tag = os.environ['RELEASE_TAG']
    version = tag.removeprefix('v')
    version_key(version)
    release = request('releases/tags/' + urllib.parse.quote(tag, safe=''))
    if release['draft'] or not release['published_at'] or release['tag_name'] != tag:
        raise ValueError('Expected a published release')
    commit = request('commits/' + urllib.parse.quote(tag, safe=''))['sha']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid source commit')
    assets = request('releases/' + str(release['id']) + '/assets?per_page=100')
    matches = [a for a in assets if a['name'] == ASSET and a['state'] == 'uploaded']
    if len(matches) != 1:
        raise ValueError('Expected exactly one uploaded supacharger.zip release asset')
    asset = matches[0]
    archive = request('releases/assets/' + str(asset['id']), binary=True)
    if len(archive) != asset['size']:
        raise ValueError('Archive size mismatch')
    checksum = hashlib.sha256(archive).hexdigest()
    if asset.get('digest') and asset['digest'] != 'sha256:' + checksum:
        raise ValueError('GitHub asset digest mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        if zipped.testzip() is not None:
            raise ValueError('Damaged ZIP')
        if zipped.comment.decode('ascii') != commit:
            raise ValueError('ZIP source commit does not match the release tag')
        package = json.loads(zipped.read('supacharger/package.json'))
        if package['name'] != 'supacharger':
            raise ValueError('Unexpected package in ZIP')
    expected_url = 'https://github.com/' + REPO + '/releases/download/' + urllib.parse.quote(tag, safe='') + '/' + ASSET
    if asset['browser_download_url'] != expected_url:
        raise ValueError('Unexpected release asset URL')
    path = Path('core/supacharger.json')
    original = json.loads(path.read_text())
    result = update(original, version, commit, expected_url, checksum)
    if result != original:
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        temporary.replace(path)
    print('Verified Core ' + version + ('; registry updated' if result != original else '; already recorded'))


if __name__ == '__main__':
    main()

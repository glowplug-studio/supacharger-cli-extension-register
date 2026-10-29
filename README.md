# Supacharger extension register

This repository lists Supacharger core and extensions by their registry name, for example `supacharger-ext-brevo`.

The [manifest.json registry](https://github.com/glowplug-studio/supacharger-cli-extension-register/blob/main/manifest.json) is the route to check the existence, versions, source download paths (`github_repo_url`), purchase URLs (`sellsource_url`) and checksums of Supacharger core and extensions. For programmatic access, use the [raw JSON](https://raw.githubusercontent.com/glowplug-studio/supacharger-cli-extension-register/main/manifest.json).

Paid extensions are provided through [sellsource.io](https://sellsource.io). If an extension has no `github_repo_url`, it is a paid extension and its package must be purchased through the registry's `sellsource_url`.

Monetise your own private repository with [sellsource.io](https://sellsource.io).

## Get Supacharger core

![Supacharger](saas.webp)

Download or clone core from the [Supacharger repository](https://github.com/glowplug-studio/supacharger):

```sh
git clone https://github.com/glowplug-studio/supacharger.git
```

## Build with Specdrive

Develop Supacharger apps with [specdrive.dev](https://specdrive.dev), the anti-vibe-coding platform for enterprises and serious developers. Bring rigour to agentic development with specification design, architecture decision records (ADRs) and an audit trail. Write specifications, not code, to build and maintain your apps.

## Release record structure

The manifest contains top-level `schemaVersion: 1`, a `core` object and an `extensions` array. `extensions` replaces the former `modules` key; consuming CLIs must support this structure before using the manifest with `--registry` to install reviewed local release source. Each release entry has:

| Field | Content |
| --- | --- |
| name | Registry name matching the bundle |
| github_repo_url | Source repository URL used to download or clone the source; absent for paid extensions |
| sellsource_url | Sellsource purchase URL; required for paid extensions that have no `github_repo_url` |
| version | Three integers, such as 4.0.0 |
| source_commit | Exact full Git commit ID |
| checksum | algorithm: sha256; format: sc-source-tree-v1; value: source digest |
| dependencies | Array of required extension registry names; empty for Brevo |

The core record currently has `null` values for `version`, `source_commit` and checksum `value`: no verified core release is registered yet. It cannot be verified until those fields are populated. Repository URLs provide source access; they are not version-specific release archive URLs.

Each snapshot contains one version per registry name. Verification of an older release requires its matching registry record. `provider_dependencies` maps a config field to the dependencies of its selected provider. Invitations defaults to `emailProvider: brevo`; only that provider’s registry names are required. The installed developer config takes precedence on updates.

## Source checksum

The registry uses **SHA-256 hashing**, not encryption, to check that source files match the registered release. `checksum.value` is a lowercase hexadecimal digest of the complete committed source tree, using the `sc-source-tree-v1` format. It is neither the checksum of a downloaded ZIP nor the Git commit ID. A match establishes consistency with the registry record; it is not a digital signature.

To verify a release, a client or agent follows these steps:

1. Select the record matching the package name and version. Require `checksum.algorithm: sha256`, `checksum.format: sc-source-tree-v1`, a complete `source_commit` and a populated checksum value.
2. Obtain the source repository containing that exact commit. Enumerate its files with `git ls-tree -rz --full-tree <source_commit>`. Only regular Git blobs with mode `100644` or `100755` are supported. Reject symlinks, submodules, Git LFS pointers, invalid UTF-8 paths, backslashes, absolute paths, empty/`.`/`..` path components and paths that collide when lowercased.
3. Read each blob's exact bytes with `git cat-file blob <object-id>` and compute its SHA-256 digest. Do not normalise whitespace or line endings. Build one record per file: `[relativePath, mode, lowercaseHexDigest]`, where the mode is a string.
4. Sort the records by their paths' UTF-8 bytes, then calculate the source-tree digest using the JavaScript expression below. Compare it exactly with `checksum.value`.
5. Verify the actual files to be installed: each recorded path must exist, its bytes must produce the same per-file digest, and its executable status must match the recorded mode. Require `extension.json` and every declared payload source to appear in the verified inventory. A matching committed tree alone does not verify modified working files or additional payload files.

```js
import { createHash } from 'node:crypto';

// records contains [relativePath, mode, lowercaseHexDigest] for every Git blob.
records.sort((a, b) => Buffer.compare(Buffer.from(a[0], 'utf8'), Buffer.from(b[0], 'utf8')));
const checksum = createHash('sha256')
  .update('sc-source-tree-v1\n' + JSON.stringify(records) + '\n', 'utf8')
  .digest('hex');
```

Any mismatch means the supplied source has not passed verification. A paid package needs the same source inventory and commit data to use this verification method; an archive alone cannot be checked by comparing its file hash with the source-tree checksum.

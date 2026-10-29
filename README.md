# Supacharger extension register

This repository lists Supacharger core and extensions by their registry name, for example `supacharger-ext-brevo`.

The [manifest.js registry](https://github.com/glowplug-studio/supacharger-cli-extension-register/blob/main/manifest.js) is the route to check the existence, versions, source download paths (`github_repo_url`) and checksums of Supacharger core and extensions. For programmatic access, use the [raw JSON](https://raw.githubusercontent.com/glowplug-studio/supacharger-cli-extension-register/main/manifest.js). Despite its filename, it contains JSON data and is never executed as JavaScript.

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
| github_repo_url | Source repository URL used to download or clone the source |
| version | Three integers, such as 4.0.0 |
| source_commit | Exact full Git commit ID |
| checksum | algorithm: sha256; format: sc-source-tree-v1; value: source digest |
| dependencies | Array of required extension registry names; empty for Brevo |

The core record will be updated and managed by GitHub Actions later. Its `version`, `source_commit` and checksum `value` are currently `null`, indicating that a verified core release has not yet been registered. Consumers must not treat that record as an installable, verified release until those fields are populated. Repository URLs provide source access; they are not version-specific release archive URLs.

Each snapshot contains one version per registry name. Retain historical release metadata for original-version verification; remote catalogue storage and ZIP delivery are coming soon. `provider_dependencies` maps a config field to the dependencies of its selected provider. Invitations defaults to `emailProvider: brevo`; only that provider’s registry names are required. The installed developer config wins on updates. Do not list a provider as supported before its implementation exists.

## Source checksum

Enumerate every regular committed Git blob at source_commit. Reject symlinks, submodules, LFS pointers, invalid/unsafe paths and case-colliding paths. For each file create `[path, mode, sha256OfExactBlobBytes]`, with string mode 100644 or 100755. Sort by UTF-8 path bytes. Calculate SHA-256 of UTF-8 `sc-source-tree-v1` + LF + JavaScript `JSON.stringify(records)` + LF. This is a source digest, not a ZIP checksum or Git commit hash. The Core/CLI registry.cjs sourceInventory function implements it.

Commit and publish a new extension version before updating its registry record. Never hash uncommitted changes as a released version or replace an existing release with different bytes. The local verifier checks committed source and actual supplied working files, then per-payload hashes. The remote download and archive verification layer remains deferred.

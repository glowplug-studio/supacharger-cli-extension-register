# Supacharger extension register

This repository lists Supacharger extensions by their registry name, for example `supacharger-ext-brevo`. Its remote is `glowplug-studio/supacharger-cli-extension-register`; the existing local folder name need not change.

`manifest.js` is JSON data containing the latest verified release for each extension. Pass it with `--registry` when installing reviewed local release source. It is never executed as JavaScript.

## Release record structure

The local CLI verifier accepts JSON data (never JavaScript execution): top-level `schemaVersion: 1` and `modules` array. Each release entry has:

| Field | Content |
| --- | --- |
| name | Registry name matching the bundle |
| github_repo_url | Source repository URL |
| version | Three integers, such as 4.0.0 |
| source_commit | Exact full Git commit ID |
| checksum | algorithm: sha256; format: sc-source-tree-v1; value: source digest |
| dependencies | Array of required extension registry names; empty for Brevo |

Each snapshot contains one version per registry name. Retain historical release metadata for original-version verification; remote catalogue storage and ZIP delivery are coming soon. `provider_dependencies` maps a config field to the dependencies of its selected provider. Invitations defaults to `emailProvider: brevo`; only that provider’s registry names are required. The installed developer config wins on updates. Do not list a provider as supported before its implementation exists.

## Source checksum

Enumerate every regular committed Git blob at source_commit. Reject symlinks, submodules, LFS pointers, invalid/unsafe paths and case-colliding paths. For each file create `[path, mode, sha256OfExactBlobBytes]`, with string mode 100644 or 100755. Sort by UTF-8 path bytes. Calculate SHA-256 of UTF-8 `sc-source-tree-v1` + LF + JavaScript `JSON.stringify(records)` + LF. This is a source digest, not a ZIP checksum or Git commit hash. The Core/CLI registry.cjs sourceInventory function implements it.

Commit and publish a new extension version before updating its registry record. Never hash uncommitted changes as a released version or replace an existing release with different bytes. The local verifier checks committed source and actual supplied working files, then per-payload hashes. The remote download and archive verification layer remains deferred.

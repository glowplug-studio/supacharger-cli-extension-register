# Supacharger Extension Register

This repository lists Supacharger core and extensions by their registry name, for example `supacharger-ext-brevo`.

The [manifest.json registry](https://github.com/glowplug-studio/supacharger-cli-extension-register/blob/main/manifest.json) is the route to check the existence, versions, source download paths (`github_repo_url`), download URLs for licence-gated extensions (`sellsource_url`) and checksums of Supacharger core and extensions. For programmatic access, use the [raw JSON](https://raw.githubusercontent.com/glowplug-studio/supacharger-cli-extension-register/main/manifest.json).

Licence-gated extensions are available through [sellsource.io](https://sellsource.io?ref=gh-sc-extension-register). When `requires_license` is `true`, a valid licence is required to download the extension through its `sellsource_url`.

Monetise your own private repository with [sellsource.io](https://sellsource.io?ref=gh-sc-extension-register).

## Get Supacharger core

[![Supacharger](sc-banner.webp)](https://supacharger.dev?ref=gh-sc-extension-register)

Download or clone core from the [Supacharger repository](https://github.com/glowplug-studio/supacharger):

```sh
git clone https://github.com/glowplug-studio/supacharger.git
```

## Build with Specdrive

Develop Supacharger apps with [specdrive.dev](https://specdrive.dev?ref=gh-sc-extension-register), the anti-vibe-coding platform for enterprises and serious developers. Bring rigour to agentic development with specification design, architecture decision records (ADRs) and an audit trail. Write specifications, not code, to build and maintain your apps.

## Release record structure

`manifest.json` lists core and extensions by `name` and `path`. Paths are relative to the manifest. Each package file contains its current release and `version_history`.

| Field | Content |
| --- | --- |
| schemaVersion | Version of the JSON structure of these files, separate from the package release version |
| name | Registry name matching the bundle |
| github_repo_url | Source repository URL, where available |
| requires_license | Extension download requires a valid licence when `true`; no download licence is required when `false` |
| download_url | ZIP download URL for the specific core release, or `null` when not specified |
| sellsource_url | URL for downloading a licence-gated extension through Sellsource |
| version | Release version, such as `4.0.0` or `0.0.1-alpha` |
| source_commit | Exact full Git commit ID |
| archive_checksum | Downloaded ZIP checksum: algorithm `sha256`, format `zip`, value: SHA-256 hash of the original ZIP, or `null` when unavailable |
| dependencies | Registry names of extensions this extension requires to function, regardless of provider choice. An empty array means no extensions are required. |
| core_services | Core services this extension requires, such as `auth` or `transactional_email`. Providers are selected in `SC_CONFIG.CORE_SERVICES`. An empty array means no core services are required. |
| version_history | Previous release records keyed by version; excludes the current release and contains no nested histories |

Invitations requires `transactional_email`. The application’s `SC_CONFIG.CORE_SERVICES.transactional_email.provider` identifies its selected provider, such as `supacharger-ext-brevo`. `dependencies` identifies specific extensions required independently of that selection.

## Verify downloaded ZIPs

A SHA-256 checksum lets you check that a downloaded ZIP matches the registered release. This works for developers and agents downloading through the CLI or Sellsource, provided they receive the same original release ZIP.

1. Follow your package’s `path` in the registry and select the matching version in its file, using `version_history` for an older release. Use its `archive_checksum.value`, with algorithm `sha256` and format `zip`.
2. Calculate the SHA-256 hash of your downloaded ZIP **before extracting it**. Replace `package.zip` below with your filename.
3. Compare the result with `archive_checksum.value`. The hashes must match (letter case does not matter). If they differ, do not install the package.

**macOS:**
```sh
shasum -a 256 package.zip
```

**Linux:**
```sh
sha256sum package.zip
```

**Windows PowerShell:**
```powershell
Get-FileHash .\package.zip -Algorithm SHA256
```

Hash the original download, not a folder or a ZIP you recreate yourself. Repacking the same source files can change the ZIP hash. A match confirms agreement with the registry, not that the code is safe or that its publisher is authentic. SHA-256 is hashing, not encryption or a digital signature.

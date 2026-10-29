{
  "schemaVersion": 1,
  "core": {
    "name": "supacharger",
    "github_repo_url": "https://github.com/glowplug-studio/supacharger.git",
    "version": null,
    "source_commit": null,
    "checksum": {
      "algorithm": "sha256",
      "format": "sc-source-tree-v1",
      "value": null
    },
    "dependencies": []
  },
  "extensions": [
    {
      "name": "supacharger-ext-brevo",
      "github_repo_url": "git@github.com:glowplug-studio/supacharger-ext-brevo.git",
      "version": "4.0.5",
      "source_commit": "6bbc175fbdf1876028d3eba7780c9375dc0e8c41",
      "checksum": {
        "algorithm": "sha256",
        "format": "sc-source-tree-v1",
        "value": "699452284aa265cb362e88f274dab8a7ce394b80054fbd234175c000f09aebfb"
      },
      "dependencies": []
    },
    {
      "name": "supacharger-ext-invitations",
      "github_repo_url": "git@github.com:glowplug-studio/supacharger-ext-invitations.git",
      "version": "0.2.1",
      "source_commit": "0dfd03192aad9b16e04dbc5ce2a02d540523d2e7",
      "checksum": {
        "algorithm": "sha256",
        "format": "sc-source-tree-v1",
        "value": "fe609f2d7dfbe82d8db2418b7e48b430e6d694ef06c281dc4cc94b69c15fa2e9"
      },
      "dependencies": [],
      "provider_dependencies": {
        "email": {
          "default": "brevo",
          "config_key": "emailProvider",
          "providers": {
            "brevo": [
              "supacharger-ext-brevo"
            ]
          }
        }
      }
    }
  ]
}

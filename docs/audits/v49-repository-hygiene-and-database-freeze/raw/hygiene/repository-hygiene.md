# Repository hygiene gate

```json
{
  "format": "gda-v49-repository-hygiene/v1",
  "status": "PASS",
  "trackedFileCount": 2517,
  "checks": {
    "activeDatabaseRootCount": 1,
    "activeDatabaseRoot": "database",
    "legacyDbRootPresent": false,
    "trackedRuntimeFiles": [],
    "activeRawCaptureDirectories": [],
    "activeBackupDirectories": [],
    "preV49Generated": [],
    "unconsumedGenerated": [],
    "unmanifestedReleaseInputs": [],
    "brokenDocumentationLinks": [],
    "brokenScriptReferences": [],
    "brokenFrontendImports": [],
    "activeScriptAllowlistPass": true,
    "unreferencedActiveScriptPolicy": "DOCUMENTED_ALLOWLIST",
    "historicalPromptActiveCount": 0,
    "unreferencedProjectAssetCount": 0,
    "brokenLfsPointerCount": 0,
    "lfsFsckOutput": "Git LFS fsck OK",
    "unmanifestedLargeFiles": [],
    "largeFileManifest": [
      {
        "path": "data/prefreeze_candidate_v48.sqlite",
        "byteSize": 421801984,
        "sha256": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
        "category": "release_input"
      },
      {
        "path": "frontend/public/data/archive-search-v1.json",
        "byteSize": 22695973,
        "sha256": "3674aa608a555e37651d5f88359f1faa01b1255be4ae870aa5a529acbd9a9d76",
        "category": "current_frontend_runtime"
      },
      {
        "path": "frontend/public/data/public_surface_mock_v0.json",
        "byteSize": 90895254,
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "category": "current_frontend_runtime"
      },
      {
        "path": "frontend/src/data/public_surface_mock_v0.json",
        "byteSize": 90895254,
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "category": "current_frontend_runtime"
      },
      {
        "path": "generated/public_surfaces_prefreeze_candidate_v48.json",
        "byteSize": 190067852,
        "sha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
        "category": "release_input"
      }
    ],
    "duplicateLargeBlobViolations": [],
    "duplicateLargeBlobAllowlist": [
      {
        "sha256": "92335ba0c49e28b644374841fb5e1d0d72f8f49cbbcd4a7ab5d38bcd893329f0",
        "byteSize": 3272608,
        "paths": [
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/fresh-b-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/candidate-derived-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/fresh-b-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "7815d5eb9bc666375bd1fe9c91b488f7e3f879f51a51970f767a8a8a6908d8de",
        "byteSize": 1749122,
        "paths": [
          "docs/audits/v49-api-read-contract-closure/raw/fresh-c/reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/final/reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/final-reconciliation/quarantined-stable-ids.tsv",
          "docs/audits/v49-repository-hygiene-and-database-freeze/raw/fresh-d/reconciliation/quarantined-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "01ac7dbf498e38f38eb1d8fbba6188722f7f56f390e38c04f00b1a183e0974b8",
        "byteSize": 3240896,
        "paths": [
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/fresh-a-stable-ids.tsv",
          "docs/audits/v49-release-projection-snapshot-db-closure/raw/restarted-17e06abd/reconciliation/fresh-b-stable-ids.tsv"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      },
      {
        "sha256": "4f293487d7d5d3ff64db3aabc154091c279bcad3fc4c2e06f4745e16a50c9138",
        "byteSize": 90895254,
        "paths": [
          "frontend/public/data/public_surface_mock_v0.json",
          "frontend/src/data/public_surface_mock_v0.json"
        ],
        "reason": "self-contained audit evidence or current frontend contract copy"
      }
    ],
    "secretPatternMatches": [],
    "projectLogBytes": 2023,
    "projectLogPolicyPass": true,
    "readmeV49ArchitecturePass": true,
    "releaseManifestPass": true,
    "auditIndexPass": true,
    "databaseFreezePass": true,
    "databaseFreezeOutput": "{\"databaseVersion\": 49, \"frozenFileCount\": 126, \"frozenPathDriftCount\": 0, \"manifestSha256\": \"f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e\", \"mode\": \"verify\", \"status\": \"PASS\", \"unmanifestedV49DatabaseFileCount\": 0}",
    "sourceTagCommit": "d78f496bcdf2cd6941791986007cd7a885c4c532",
    "sourceTagResolvable": true
  },
  "violations": []
}
```

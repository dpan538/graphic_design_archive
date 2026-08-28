# Repository hygiene gate

```json
{
  "format": "gda-v49-repository-hygiene/v1",
  "status": "PASS",
  "trackedFileCount": 5099,
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
    "activeScriptAllowlistDeclaredCount": 290,
    "activeScriptAllowlistRowCount": 290,
    "activeScriptAllowlistTrackedCount": 290,
    "activeScriptAllowlistMissingScripts": [],
    "activeScriptAllowlistUnexpectedScripts": [],
    "activeScriptAllowlistDuplicatePathCount": 0,
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
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-functional-http-case-ledger-v2.tsv",
        "byteSize": 162498021,
        "sha256": "dad0a42f8a3efd11fec8fad45de517eb5f641d6795d136e4f4ec5e8c1af70aaa",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-functional-validation-v2.json",
        "byteSize": 78575302,
        "sha256": "1c61513c2d2dbb75dc280fab2a9171f3b44106d6b4379dcefad0dc4db1c06a3f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-v2-service-dto-case-ledger.tsv",
        "byteSize": 109706355,
        "sha256": "6cca40d5ea5d0b7baa4014b1445481cbd85d0723ef3776be96635140f274cfd9",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/api-v2-transition-case-ledger.tsv",
        "byteSize": 195678263,
        "sha256": "3e7651a372d53b671042c685ce17be34277023d72b878c1fa2e5d99a6337c6c2",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification-cases-v2.tsv",
        "byteSize": 186160119,
        "sha256": "f30a639b70a226a0d38ed60bce40597f286f00b057dd848ddb03b7b7e1dfceaa",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification.json",
        "byteSize": 182907607,
        "sha256": "794a16071edc9efce13c17de56c6b901aac86feb1dd5091fb490e1f20febf35f",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv",
        "byteSize": 284522777,
        "sha256": "3a58b52f3c95fbc33ad992481ff55485b9a566418adc15daa1a39f86e9dd96a0",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/json-c1-warm-run2.json",
        "byteSize": 18931343,
        "sha256": "0ff0653ece2d600b0f88f25a6c4ecf186107a6b29162be2edfb54cd68ffd4612",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/mixed-c25-stabilization-run2.json",
        "byteSize": 46486621,
        "sha256": "bc956f72e1ffc0fe86025b2e8b4bc59e086600524341d334c23e3726a7caf864",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2-run2/mixed-c25-sustained-run2.json",
        "byteSize": 46348011,
        "sha256": "49264b0672c3e0ec03e3c156dfb2413d7a5ccfafc70fbac4de13c468e901adbd",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2/json-c1-warm.json",
        "byteSize": 19301266,
        "sha256": "15d51ebf4a0cd6945102a3b5a9d7d5e49f50cc9507c21f5c647131abd37b8931",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-full-space-closure-round1/raw/workloads-v2/mixed-c25-sustained.json",
        "byteSize": 46331756,
        "sha256": "dac188ce06cab681b9c7be2617439a161967551c123d08a33c0226c58c20968a",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/prior-object-reconciliation-universe-v1-exports.tsv",
        "byteSize": 11541976,
        "sha256": "d0e7ee1eb8c44b74ec50246509f686e023d5b3bc7f38aa479b8e199521d4b836",
        "category": "final_audit_evidence"
      },
      {
        "path": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/prior-object-reconciliation-universe-v1-states.tsv",
        "byteSize": 12307984,
        "sha256": "fab7057bb7c59feeb91a09d08fee55dd843cf2059dac683f89760a8a64354c87",
        "category": "final_audit_evidence"
      },
      {
        "path": "frontend/generated/trace-context-v1/records.json",
        "byteSize": 13109622,
        "sha256": "c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7",
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
    "projectLogBytes": 36600,
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

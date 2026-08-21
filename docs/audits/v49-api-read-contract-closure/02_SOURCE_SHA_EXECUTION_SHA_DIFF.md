# Source SHA / execution SHA diff

- Previous execution SHA: `1a2a2b9a0f9b43a00a5ebd360fac42d48d6aa5dc`
- Previous final/source SHA: `55f1d715722f1a3bdb5b14d716a703e8a79ffb57`
- Changed paths: 196
- Paths outside `docs/audits/**`: 0

Every changed path is part of the previous database-closure audit package: narrative receipts, raw evidence, its manifest, or its checksum ledger. There are no changes to `database/**`, migration runners, SQL, roles, builders/importers, fixture generators, reconciliation code, API runtime code, or contract tests.

```text
PREVIOUS_FINAL_SHA_DIFF_CLASSIFICATION=PASS:AUDIT_ONLY
PREVIOUS_FINAL_SHA_DIFF_FILES=196
PREVIOUS_FINAL_SHA_RECHECK_REQUIRED=FOCUSED_DATABASE_RECHECK
```

The complete machine-readable name/status list and diff stat are in `raw/source-diff/`.

```text
PREVIOUS_FINAL_SHA_RECHECK_RESULT=PASS
```

The independent recheck comprised a fresh formal replay, official verifier, current-leaf fixture, 14/14 missingness, 36/36 DML permissions, 32/1k/2k/full focused performance, stable-ID reconciliation, and post-API schema/release fingerprints.

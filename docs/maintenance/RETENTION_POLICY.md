# Retention policy

Every source-tree file is recorded in `v49-retention-ledger.csv` and JSON with its hash, consumer evidence, authority, rights sensitivity, and disposition.

- `KEEP_ACTIVE`: current runtime/API/test/CI/maintenance implementation.
- `KEEP_RELEASE_INPUT`: byte-pinned canonical or reconciliation input needed for fresh replay.
- `KEEP_RELEASE_EVIDENCE`: formal self-contained v49 audit evidence.
- `KEEP_CURRENT_DOCUMENTATION`: current or indexed documentation.
- `ARCHIVE_BY_IMMUTABLE_REF`: removed from the active tip only after the remote source anchor was verified.
- `DELETE_REGENERABLE`: superseded generated data with no current consumer and immutable source recovery.
- `DELETE_LOCAL_RUNTIME`: never tracked; covered by `.gitignore` and hygiene gates.
- `KEEP_BLOCKED`: unknown dependency, rights, provenance, or authority. A blocked file cannot be deleted.

No file may remain unclassified. Canonical inputs, sealed evidence, rights policy, manifests, and current final audit packages are never rewritten for size or formatting.


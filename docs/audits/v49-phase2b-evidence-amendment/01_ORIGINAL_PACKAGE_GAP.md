# Original Phase 2B audit package gap

The original package at `docs/audits/v49-phase2b-performance/` is immutable
historical evidence. This amendment does not change its `MANIFEST.json`,
`CHECKSUMS.sha256`, receipts, or referenced paths.

```text
SOURCE_SHA=11e7b82d27b2774273d2f0d68904632246dabd37
ORIGINAL_CHECKSUM_ENTRY_COUNT=72
ORIGINAL_PRESENT_COUNT=61
ORIGINAL_PRESENT_HASH_MATCH=61/61
ORIGINAL_MISSING_COUNT=11
ORIGINAL_CHECKSUM_VERIFICATION=61/72
ORIGINAL_PACKAGE_VERIFIED=false
HISTORICAL_ARTIFACTS_RECOVERED=false
CHECKSUM_GATE_LOWERED=false
HISTORICAL_AUDIT_FILES_REWRITTEN=false
SOURCE_TREE_AT_11E_SELF_CONTAINED=false
SUPERSESSION_DECLARED=true
```

All eleven missing entries are exactly `evidence/P1_*.log`; no existing entry
has a byte or SHA-256 mismatch. The original manifest records their expected
lengths and hashes, while the source commit contains no corresponding blobs.

The old `*.log` ignore rule explains how a local manifest generator could
observe the files while ordinary staging omitted them. The condition is a
packaging defect, not evidence that replacement bytes match the lost files.
The additive `reproduced/` evidence is deliberately outside the missing
historical paths and has its own checksum ledger.

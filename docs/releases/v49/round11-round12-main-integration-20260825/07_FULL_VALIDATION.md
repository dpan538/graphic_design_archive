# Full validation

All authoritative gates completed successfully. The machine-readable matrix is `docs/audits/v49-round11-round12-main-integration/raw/test_results.tsv`.

- Repository integrity: full Git fsck, Git LFS fsck, broken documentation links, script references, frontend imports, allowlist reconciliation, database freeze, and audit self-containment passed.
- Round 8–10: reset/domain boundaries, vocabulary research, grammar pair matrix, universal-node gate, and sealed audit checks passed.
- Round 11: Round 10 reconciliation, 20 adversarial cases, compiler behavior, synthetic isolation, real-build rejection, immutability, and ten fail-open mutations passed.
- Round 12: immutable freeze and evidence coverage, nine Python reference tests, fourteen cross-runtime fixtures, strict schemas, flow/tree planning, five Instances, and historical-claim rejection passed.
- Platform: TypeScript, Search, Context, Spacetime, API/read-platform, and production build (46/46 static pages) passed.

Round 6 all-pair similarity and Round 7 dense encoding were intentionally not rerun because both are superseded historical research.

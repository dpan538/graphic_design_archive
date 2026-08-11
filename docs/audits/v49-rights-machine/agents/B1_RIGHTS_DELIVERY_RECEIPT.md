# B1 — Rights and delivery truth-table receipt

## Result

`PASS`

B1 merged the overlapping rights/visual/machine P0 findings into one boundary-aware crosswalk and locked an ordered, fail-closed delivery rule. B1 does not assert the combined Phase 1D gate; the visual entity/cardinality, legacy baseline, machine contract, negative oracle, normative calibration, and independent joint verification remain outside this receipt.

## Task boundary

B1 owned only:

- `docs/audits/v49-rights-machine/01_P0_CROSSWALK.md`;
- `docs/audits/v49-rights-machine/04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`;
- this receipt.

B1 did not edit a normative architecture document, code, package file, frozen asset, QA image, or any other audit output.

## Assets read

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- all four files under `docs/adr/`
- `docs/audits/v49-pre-migration/06_RIGHTS_AND_VISUAL_FEDERATION.md`
- `docs/audits/v49-pre-migration/10_MACHINE_API_SECURITY_CI_DEPLOYMENT.md`
- `docs/audits/v49-pre-migration/11_CLEANUP_ACTION_LEDGER.md`
- `docs/audits/v49-pre-migration/12_FREEZE_READINESS_MATRIX.md`
- Phase 1C executive receipt, authority matrix, gate receipt, manifest, and detached A5 verifier receipt
- the Spreadsheets skill, required style guide, artifact-tool quick start, and scientific-research guidance

The Phase 1C manifest and receipt establish `AUTHORITY_RESEARCH_DELTA_CLOSED=true` while leaving rights/visual/machine decisions open. B1 did not reuse the superseded Phase 1B readiness result as current truth.

## Evidence commands

Representative read-only command families:

```text
git status --short
rg --files docs/adr docs/audits/v49-authority-research-delta
wc -l <named normative and audit evidence>
sed -n '<complete bounded ranges>p' <named files>
```

TSV authoring and verification use the loader-provided runtime only:

```text
NODE_PATH=/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
/private/tmp/v49_phase1d_b1/validate_rights_truth_table.mjs
```

The validator parses every TSV row, checks unique headers and constant field width, rejects tabs/newlines inside cells, writes the matrix into an `@oai/artifact-tool` workbook, and inspects the complete table range. A separate standard-library parse reconciles the row count, unique rule IDs, numeric precedence, closed delivery vocabulary, the single remote-image allow row, and the terminal fail-closed rule.

## Measured results

| Measure | Result |
|---|---:|
| Unique consolidated P0 decision themes | 5 |
| Explicit later implementation themes | 3 |
| Truth-table data rows | 20 |
| Truth-table columns | 16 |
| Unique rule IDs | 20 |
| `REMOTE_IMAGE` rules | 1 |
| Terminal fail-closed rules | 1 |
| Active-takedown precedence rules | 2 |
| Locator exposure outside an allowed delivery mode | 0 |

The closed delivery vocabulary is `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, and `REMOTE_IMAGE`. The table preserves five independent axes: rights assessment, provider-policy evaluation, delivery decision, endpoint health, and takedown. Attribution completeness and typed-locator health are explicit prerequisites rather than implied permission.

## Findings

1. A6/A10 contain five unique pre-DDL decision themes after deduplication, not every P0 implementation gap as a separate schema blocker.
2. A10-P0-03 is deliberately split: stable identity, version fields, field exposure, and fail-closed serializer semantics are pre-DDL; actual JSON Schema, OpenAPI, JSON-LD, Linked Art/PROV-O, DCAT, sitemap, and change-feed artifacts are pre-freeze or pre-promotion implementation work.
3. A6-P0-06 and A10-P0-04 are also split: future public projections must suppress held locators before DDL is fixed, while removal of current legacy remote-pixel rendering remains a frontend-promotion gate.
4. Unknown, missing, conflicting, or stale rights/policy never yields `SOURCE_VIEWER` or `REMOTE_IMAGE`.
5. Endpoint health never raises delivery. Only one rule can yield `REMOTE_IMAGE`, and it requires explicit remote-display rights, explicit provider-policy permission, complete attribution, an allowlisted typed locator, and fresh healthy endpoint evidence.
6. IIIF, API availability, HTTP success, redirect success, thumbnail presence, or source reputation is never a rights or policy input.

## Unresolved items outside B1

- B2 must lock the FK/cardinality model and dual release/seal/CAS protocol using the same vocabulary.
- B3 must measure and type 100% of the legacy visual-reference population and define positive-rights coverage without making it a PASS threshold.
- B4 must lock stable IDs/URN mapping, dual-version envelopes, public/internal/held fields, version mismatch, and registry-absent behavior.
- B5 and the joint verifier must prove cross-document consistency and the negative oracle.
- PostgreSQL, Read API, OpenAPI, JSON Schema, JSON-LD/RDF/DCAT, CI, deployment, production health checks, and frontend visual integration remain unimplemented by design.

These are not evidence conflicts within B1.

## Files written

Exactly the three B1-owned paths listed in the task boundary.

## Actions explicitly not performed

No network, HTTP/IIIF/image request, provider probe, media download, PostgreSQL, SQLite, Docker, npm, Next.js, TypeScript, browser, frontend build, data export, migration, API implementation, fixture, package change, frozen-asset edit, QA edit, protected-main mutation, commit, push, PR, merge, or deployment was performed.

## Residual processes

B1 started no server, compiler, browser, database, package installer, data generator, or background process. The bounded Node validator exits synchronously. Final OS-wide process ownership remains with the primary task.

## Exit status

```text
B1_STATUS=PASS
B1_COVERAGE=COMPLETE
P0_CROSSWALK_UNIQUE=true
RIGHTS_DELIVERY_TRUTH_TABLE_LOCKED=true
RIGHTS_POLICY_DELIVERY_HEALTH_TAKEDOWN_ORTHOGONAL=true
ENDPOINT_HEALTH_CAN_WIDEN=false
REMOTE_IMAGE_RULE_COUNT=1
NETWORK_ACCESSED=false
FILES_MODIFIED=3
RESIDUAL_B1_PROCESS=0
```

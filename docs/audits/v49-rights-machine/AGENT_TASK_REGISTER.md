# Phase 1D rights/machine agent task register

- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Initial commit: `967cbe34a8f30f8e74fa117e1bdee74644f71afe`
- Maximum concurrent subagents: 3
- Package stage: rights/visual/machine decisions only; runtime cleanup is a later, separate commit

## Register

| Task | Independent boundary | Owned outputs | Result | Process / non-action boundary |
|---|---|---|---|---|
| B1 — Rights/delivery | P0 crosswalk and ordered five-mode truth table | `01_P0_CROSSWALK.md`; `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`; `agents/B1_RIGHTS_DELIVERY_RECEIPT.md` | PASS | 20 rules; artifact-tool and strict TSV validation; no provider/network/implementation action. The controller stopped the completed slot after its receipt existed; no B1 process remained. |
| B2 — Visual identity/release | External-reference identity, FK cardinalities, dual release/seal/CAS | `02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md`; `03_VISUAL_ENTITY_CARDINALITY_MATRIX.md`; `07_DUAL_RELEASE_SEAL_CAS_SPEC.md`; B2 receipt | PASS | No DDL/API/frontend action. The controller stopped the completed slot after its receipt existed; no B2 process remained. |
| B3 — Legacy visual baseline | One full canonical-candidate visual enumeration and compact typed ledger | `05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv`; `06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`; B3 receipt | PASS | Candidate parsed once; 15,923 accounted; artifact-tool/strict parse passed; no network/rights inference. The controller stopped the completed slot after its receipt existed; no B3 process remained. |
| B4 — Machine/redaction | Exact response identity, stable URNs, field classes and positive serializer | `08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md`; `09_STABLE_ID_URI_POLICY.md`; B4 receipt | PASS | No API/schema implementation. The controller stopped the completed slot after its receipt existed; no B4 process remained. |
| B5 — Negative oracle | Rights, machine, seal/CAS and derived anti-write cases | `10_NEGATIVE_TEST_SPEC.md`; B5 receipt | PASS | 39 unique cases; link/format checks pass; no executable implementation claimed. |
| B6 — Normative cross-check | Independent cross-document term and gate audit after primary integration | B6 receipt only | PASS | 19 integration deltas resolved; final residual P0/P1/P2 = 0/0/0; no normative edit by B6. |
| B7 — Package verifier | Independent deterministic Phase 1C prerequisite + rights package + candidate recomputation | `scripts/verify_v49_rights_machine.py`; B7 receipt | PASS | One full parse; 216 checks, 0 failures; 99.071 s total; PID 18190 exited; no network/database/image access. |

## Coordination and conflict resolution

The primary task resolved these cross-agent differences before package closure:

1. B2's logical/internal `registrySha256` and database `registry_sha256` map to the single public `visualRegistrySha256`; no fifth version value exists.
2. B2's early endpoint-dependent mismatch wording is narrowed by B4/B5: registry not selected or no compatible current yields research-only success, while an explicitly supplied incompatible visual pair yields `409 RELEASE_VERSION_MISMATCH`.
3. B3's `rawStructuredEvidenceSurfaceBundles=15923` is a raw-field-presence measure. Its mutually exclusive overall disposition remains 15,788 `RIGHTS_UNKNOWN` plus 135 `NO_VISUAL_REFERENCE`; `EVIDENCE_PRESENT=0` does not mean the raw fields are absent.
4. B2's `urn:graphic-design-archive:...` deterministic UUIDv5 name is an internal seed input. B4's `urn:gdarchive:...` value is the canonical public resource URN. They are not aliases.
5. API/OpenAPI/JSON Schema/JSON-LD/DCAT, CI, deployment, frontend Repository integration, production health checks and browser evidence remain later implementation gates rather than DDL decision blockers.

## Primary-task actions

The primary task:

- verified Git/remote/ancestry, protected-main fingerprints, Prompt A checksums and gate fields before dispatch;
- reran the Phase 1C verifier once with PASS;
- integrated the locked B1–B5 terms into the ten affected normative files;
- created the executive/gate receipts and package manifest/checksums;
- did not run PostgreSQL, Docker, npm, Next.js, TypeScript, a browser, an image fetch, data import/export, migration, PR, merge or deployment during this package stage.

Runtime cleanup, its own agents and its own receipt are deliberately absent from this register because cleanup begins only after this package is committed independently.

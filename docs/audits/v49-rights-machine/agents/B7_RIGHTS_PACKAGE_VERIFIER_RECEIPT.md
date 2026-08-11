# B7 — Independent deterministic rights/machine package verifier receipt

- Agent task: v49 Phase 1D B7
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Result: **PASS**
- Verifier exit: `0`
- Implementation performed: **false**

## Task boundary

B7 independently verified the Phase 1C prerequisite, the B1–B5 Phase 1D package, the integrated normative corpus, the frozen visual-input population, the ordered rights/delivery rule, and the implementation-neutral negative oracle. B7 owned only:

- `scripts/verify_v49_rights_machine.py`;
- this receipt.

The verifier is standard-library Python, stdout-only and deterministic. It has no network client or package dependency, does not open a database, does not access image bytes or provider endpoints, and writes no file, database, frozen asset, manifest or checksum. It parses the 190,067,852-byte candidate exactly once per invocation.

## Assets read

### Phase 1C prerequisite

- `scripts/verify_v49_authority_research_delta.py` in full;
- `docs/audits/v49-authority-research-delta/13_AUTHORITY_RESEARCH_GATE_RECEIPT.md`;
- `docs/audits/v49-authority-research-delta/MANIFEST.json`;
- `docs/audits/v49-authority-research-delta/CHECKSUMS.sha256`;
- all five named frozen assets for byte/SHA verification.

### Phase 1D B1–B5

- `01_P0_CROSSWALK.md`;
- `02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md`;
- `03_VISUAL_ENTITY_CARDINALITY_MATRIX.md`;
- all 20 data rows in `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`;
- all 71 data rows in `05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv`;
- complete `06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`;
- `07_DUAL_RELEASE_SEAL_CAS_SPEC.md`;
- `08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md`;
- `09_STABLE_ID_URI_POLICY.md`;
- all 39 cases in `10_NEGATIVE_TEST_SPEC.md`;
- B1, B2, B3, B4 and B5 agent receipts.

### Integrated normative corpus

- `ARCHITECTURE.md`;
- `DATA_MODEL_V49.md`;
- `READ_API_V1.md`;
- `MIGRATION_V48_TO_V49.md`;
- `ACCEPTANCE_GATES.md`;
- `docs/architecture/DDL_DECISION_PACK_V49.md`;
- ADR 0001–0004.

## Commands and process receipt

Static preflight, with no candidate parse:

```text
python3 -m py_compile scripts/verify_v49_rights_machine.py
python3 scripts/verify_v49_rights_machine.py --help
git diff --check -- scripts/verify_v49_rights_machine.py
python3 -c '<import verifier; run every non-candidate check family>'
```

The non-candidate preflight returned `101 checks / 0 errors`. A source scan confirmed one `classify_candidate(...)` call, one candidate `read_bytes()` and one `json.loads(raw_bytes)` call in the executable path.

The single full invocation was:

```text
python3 scripts/verify_v49_rights_machine.py --json
```

| Process item | Result |
|---|---:|
| unified exec session | `16785` |
| verifier PID | `18190` |
| candidate parse invocations | `1` |
| candidate parse/classification time | `81.164333 s` |
| total verifier time | `99.070680 s` |
| final checks | `216` |
| final failures | `0` |
| exit | `0` |
| post-exit `kill -0 18190` | failed with “no such process”, confirming exit |

The verifier was not restarted. No duplicate candidate parser or hash/classification process was opened.

## Frozen integrity and Phase 1C prerequisite

All five actual byte streams matched their exact byte lengths and SHA-256 values:

| Frozen asset | Bytes | SHA-256 | Result |
|---|---:|---|---|
| Candidate JSON | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | PASS |
| SQLite reconciliation snapshot | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | PASS |
| Transfer manifest JSON | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | PASS |
| Transfer manifest CSV | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | PASS |
| TRACE manifest | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | PASS |

The Prompt A manifest and gate receipt independently agreed on the required true/zero fields:

```text
AUDIT_BASELINE_VERIFIED=true
INPUT_PARITY=true
METADATA_SUPPORTED_CONFLICT_RESOLVED=true
PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED=true
UNCLASSIFIED_GRAPH_FACT=0
UNCLASSIFIED_RAW_SOURCE=0
UNKNOWN_RELATION_FAIL_CLOSED=true
RESEARCH_CORPUS_POLICY_VERSIONED=true
MISSINGNESS_BASELINE_VERSIONED=true
AUTHORITY_RESEARCH_DELTA_CLOSED=true
TARGET_20000_IS_ACCEPTANCE_GATE=false
```

All 25 Prompt A package-local checksum entries, including its manifest and verifier, remained exact. The three root normative files already authorized for Phase 1D integration (`ACCEPTANCE_GATES.md`, `DATA_MODEL_V49.md`, and `MIGRATION_V48_TO_V49.md`) were explicitly excluded from the Phase 1C detached checksum replay rather than incorrectly reported as a frozen-package failure.

## Candidate and legacy visual measurement

The one candidate parse independently reproduced the B3 unit boundary and all requested counts:

| Metric | Result |
|---|---:|
| candidate visual bundles | 15,923 |
| accounted bundles | 15,923 |
| unaccounted bundles | 0 |
| unique surface IDs | 15,923 |
| unique source-record IDs | 15,923 |
| reference-bearing bundles | 15,788 |
| `NO_VISUAL_REFERENCE` bundles | 135 |
| external locator occurrences | 15,790 |
| distinct external locator values | 15,788 |
| malformed locator occurrences | 0 |
| unclassified visual references | 0 |
| positive-rights-qualified bundles | 0 |
| positive-rights coverage | 0.0000% |

Exact locator-role occurrences also matched:

| Candidate role | Occurrences |
|---|---:|
| `image.url` | 15,621 |
| `image.viewerUrl` | 165 |
| `image.sourceViewerUrl` | 2 |
| `image.evidenceImageUrl` | 2 |

The B3 JSON summary distributions, observed schema, 71-row/29-column compact TSV, group uniqueness, surface/locator aggregates, zero malformed/positive totals, candidate hash, authority role and recovery reference all reconciled. The TSV SHA-256 is `ca802327787821c5d9f0a0a1d3a818b3f6534a92361319fdfbcf7373d6e24e24`.

Independent candidate recomputation matched all seven B3 sequence/set hashes:

| Evidence | SHA-256 |
|---|---|
| surface ordinal/ID sequence | `0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418` |
| surface ID set | `7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46` |
| source-record ID set | `16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e` |
| raw visual-bundle sequence | `265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e` |
| external-locator occurrence sequence | `1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812` |
| external-locator value set | `434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28` |
| classified-surface sequence | `2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc` |

This proves that `UNKNOWN` and `UNMAPPED_PROVIDER` are typed fail-closed dispositions, while positive authorization remains unproven. It does not infer a negative legal conclusion from the absence of governed policy evidence.

## Rights truth table and machine oracle

The truth table passed all structural checks:

- 20 rows, 16 columns, 20 unique rule IDs and 20 unique increasing numeric precedences;
- exact closed modes `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, `REMOTE_IMAGE`;
- exactly one `REMOTE_IMAGE` row, `RD-080`, requiring `REMOTE_DISPLAY_PERMITTED`, `REMOTE_DISPLAY_ALLOWED`, complete attribution, fresh healthy remote-image evidence and an allowlisted remote-pixel locator;
- lower modes expose zero pixel, thumbnail or image-service fields;
- `RD-001` / `RD-002` are the first two rules and enforce takedown precedence;
- terminal `RD-999` yields `CITATION_ONLY` and omits all locator classes.

The negative oracle contains exactly 39 unique definition rows: 11 rights/delivery, 14 machine/redaction/version, nine seal/CAS and five derived-authority anti-write cases. Required unknown-rights, viewer-only, endpoint-downgrade, takedown, positive-control, mismatch, held-locator, read-only API, post-seal, stale-CAS, Search/TRACE anti-write and unknown-relation cases are all present.

## Normative consistency

The integrated ten-file normative allowlist passed the frozen terminology scan:

- no `PIXEL_ALLOWED`, `WITHHELD` or public `registrySha256` remains;
- public `visualRegistrySha256` and the internal `registry_sha256` mapping are explicit;
- stable class URNs exist for object, relation, claim, source and visual reference;
- the only `.example` URLs are exact historical UUIDv5 seed-name inputs in the DDL decision pack, guarded as non-resolvable and never public;
- visual pair atomic nullability, normal research-only registry absence and explicit `RELEASE_VERSION_MISMATCH` are present;
- `SAFE` / `PUBLIC` / `INTERNAL` / `HELD`, positive serializer allowlists and GET/HEAD/OPTIONS-only semantics are present;
- the independent `draft → candidate → validated → sealed` lifecycle, sidecars and CAS rules remain present;
- missing API/OpenAPI/JSON Schema/JSON-LD/DCAT/CI/deployment/browser implementations remain later gates rather than physical-schema blockers.

All checked B1–B5 relative Markdown links resolve inside the repository.

## Package-wrapper boundary

At the detached B7 run, the primary-task-owned `00_EXECUTIVE_RECEIPT.md`, `11_RIGHTS_MACHINE_GATE_RECEIPT.md`, `AGENT_TASK_REGISTER.md`, `MANIFEST.json`, and `CHECKSUMS.sha256` did not yet exist. Their absence was deliberately not disguised as self-verification: B7 verifies the decision package before the primary task creates those wrappers and avoids a checksum cycle. The verifier will require all three wrappers atomically once any wrapper exists and will verify `MANIFEST.json` plus `CHECKSUMS.sha256` atomically when both exist. The primary task owns final package generation and the post-generation checksum pass.

## Priority findings

| Priority | Finding | Result |
|---|---|---|
| P0 | Phase 1C authority/count/research prerequisite remains closed. | PASS |
| P0 | Every legacy candidate visual bundle is accounted and typed; unclassified is zero. | PASS |
| P0 | Rights/policy/delivery/health/takedown truth table is closed, ordered and fail-closed. | PASS |
| P0 | Stable identity, atomic dual version identity, registry absence/mismatch and structural redaction are consistent in the normative corpus. | PASS |
| P0 | Negative oracle covers the 39 required decision families. | PASS |
| P1 | Positive rights remain unproven for all 15,788 reference-bearing bundles. | Correctly measured at 0.0000%; not a pre-DDL PASS threshold. |
| P1 | Actual DDL/API/schema/CI/deployment/runtime conformance remains unimplemented. | Correctly deferred; not claimed by B7. |

## Actions explicitly not performed

No PostgreSQL/SQLite connection, DDL, migration, data import/export/regeneration, network/HTTP/IIIF/provider access, image read/download/proxy, Docker, npm, Next.js, TypeScript, browser, screenshot, API/fixture/frontend/package/CI/deployment edit, frozen-asset/QA/protected-main mutation, manifest/checksum generation, commit, push, PR, merge or deployment was performed by B7.

## Exit fields

```text
B7_STATUS=PASS
B7_CHECKS=216
B7_FAILURES=0
CANDIDATE_PARSE_COUNT=1
LEGACY_INPUT_SURFACES=15923
ACCOUNTED_INPUT_SURFACES=15923
UNACCOUNTED_INPUT_SURFACES=0
LEGACY_VISUAL_REFERENCE_INVENTORIED=100%
LEGACY_VISUAL_REFERENCE_TYPED=100%
LEGACY_POSITIVE_RIGHTS_COVERAGE=0.0000%
UNCLASSIFIED_VISUAL_REFERENCE=0
TRUTH_TABLE_RULES=20
NEGATIVE_ORACLE_CASES=39
PROMPT_A_AUTHORITY_RESEARCH_DELTA_CLOSED=true
RIGHTS_PACKAGE_CORE_VERIFIED=true
NORMATIVE_RESIDUAL_P0=0
DATABASE_IMPLEMENTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
RESIDUAL_B7_PROCESS=0
```

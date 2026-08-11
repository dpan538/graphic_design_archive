# v49 Phase 1D — Independent joint pre-DDL gate receipt

- Joint verifier: J1, independent of Phase 1C design and Phase 1D B1–B7/C1–C3 work
- Result: **PASS — decision-level pre-DDL closure**
- Verified worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Verified local HEAD: `2d8cde543e68169bb62af59cc46ec57eaf7b046e`
- Phase 1D decision commit: `f75ded85000749beb4735fbbddcce99e9395b0b2`
- Phase 1D entry / Phase 1C commit: `967cbe34a8f30f8e74fa117e1bdee74644f71afe`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Verification date: 2026-08-11, Australia/Brisbane

## Scope and decision

J1 read the Phase 1C authority/research package, the complete Phase 1D rights/machine package, the cleanup manifest/checksums and C3 receipt, the two Phase 1D commit boundaries, and the integrated v49 normative corpus. J1 added only this receipt. It did not add an architecture decision, repair data, alter a manifest/checksum, change frontend/package code, stage, commit, push, merge, or deploy.

No unresolved authority, identity, cardinality, state, version, serializer, or unclassified-population conflict remains at the logical pre-DDL boundary. The next phase may specify and review a physical PostgreSQL schema against these locked decisions. This receipt does **not** authorize executing DDL or claim any database, API, release, frontend, freeze, promotion, or deployment implementation.

```text
JOINT_PRE_DDL_VERIFIER=PASS
DECISION_RESIDUAL_P0=0
DECISION_RESIDUAL_P1=0
DECISION_RESIDUAL_P2=0
```

Known fail-closed holds are not unclassified facts. In particular, `TRACE_ELIGIBLE_OBJECTS=0`, positive visual-rights coverage `0.0000%`, the historical graph-regeneration gap, and later implementation gaps remain explicit downstream work; none leaves a key, FK, state, authority, release, or serialization rule undecided.

## Git and commit-boundary verification

| Check | Measured result | Gate |
|---|---|---|
| Local HEAD and branch | `2d8cde543e68169bb62af59cc46ec57eaf7b046e`, `refactor/v49-data-platform` | PASS |
| Entry ancestor | `967cbe34a8f30f8e74fa117e1bdee74644f71afe` is an ancestor of HEAD | PASS |
| Frozen ancestor | `0404c7f96f9189f576c4c5b1368061e4082e436b` is an ancestor of HEAD | PASS |
| Decision boundary | parent of `f75ded8` is exactly `967cbe3`; 33 paths; subject `docs: close v49 rights visual and machine decisions` | PASS |
| Cleanup boundary | parent of `2d8cde5` is exactly `f75ded8`; 31 paths; subject `refactor: retire browser-local AI runtime and bulk routes` | PASS |
| Cross-stage isolation | decision diff contains no frontend/runtime-cleanup path; cleanup diff contains no v49 normative file, rights-machine package, or rights verifier | PASS |
| Frozen/data diff | no change to any of the five frozen assets from `967cbe3..2d8cde5` | PASS |
| Whitespace validation | `git diff --check` is empty for each commit boundary | PASS |
| Worktree before J1 output | clean | PASS |
| Remote observation | `origin/refactor/v49-data-platform=967cbe3`; local is expected 2 ahead / 0 behind before the final receipt commit and task-owned ordinary push | INFO, no remote race |

The cleanup commit therefore cannot affect the already committed rights/machine decision result: its diff contains no normative, B-package, rights-verifier, frozen-data, Search/TRACE-data, or rights-model change.

## Audit-package integrity

### Phase 1C authority/research package

- `MANIFEST.json` parses and binds 27 artifacts plus its deterministic verifier.
- The package-local audit directory and verifier are byte-identical to commit `967cbe3`.
- Twenty-five current package-local checksum entries are exact.
- The remaining three Phase 1C checksum entries point to `ACCEPTANCE_GATES.md`, `DATA_MODEL_V49.md`, and `MIGRATION_V48_TO_V49.md`. Those files were deliberately and exclusively updated by the authorized Phase 1D decision commit. Their blobs at `967cbe3` independently reproduce the exact Phase 1C checksum values:

```text
ACCEPTANCE_GATES.md       e4c46976274e0e69cff13593296716ec10188daf16d251ec6920274ce4594ca5
DATA_MODEL_V49.md         37c2270412adadeabf65e6641ec32c8393fdcdc337e5c23116b44a1342c10041
MIGRATION_V48_TO_V49.md   f85ef0ff0286a5cc673c341895393670a0a205364557b71f40a14b5f9963927b
```

The current-head Phase 1C verifier was run once. It exited `1` only on its two wrapper checks that compare those same three old normative blobs to the current tree. Every frozen-byte/hash, SQLite integrity, candidate count/set, graph unit, raw-source, corpus, relation registry, Search/TRACE reconciliation, and fail-closed semantic check passed. The Phase 1D rights verifier correctly scopes this historical replay boundary and reports all 25 Phase 1C package-local checksum entries exact. This is authorized normative evolution, not corruption of Phase 1C evidence.

### Phase 1D rights/machine package

- `MANIFEST.json` parses; all 31 manifest artifacts match.
- All 32 `CHECKSUMS.sha256` entries match the current tree.
- `00_EXECUTIVE_RECEIPT.md`, `11_RIGHTS_MACHINE_GATE_RECEIPT.md`, B6 and B7 receipts are present and internally consistent.
- A single J1 invocation of `python3 scripts/verify_v49_rights_machine.py --json` exited `0`: **219 checks, 0 failures**, one candidate parse, `81.746465 s` total, no network, database, or file write.

### Phase 1D reversible-cleanup package

- `MANIFEST.json` parses; all 25 manifest artifacts match.
- All 26 `CHECKSUMS.sha256` entries match the current tree.
- C3's detached pre-commit run recorded **38 checks, 0 failures**; its receipt and manifest are checksummed.
- Replaying the C3 verifier after the cleanup commit exited `1` on exactly two orchestration assumptions: it expects `HEAD=f75ded8`, and its pre-commit changed-file allowlist does not include the six final cleanup wrapper files. All 36 current substantive runtime, package, Search, route, A4, archive, QA, safe-delete, data-boundary, protected-main, and diff checks passed. The current committed diff and exact cleanup manifest/checksums independently close those two post-commit wrapper conditions. This replay limitation is not a rights or physical-schema conflict.

## Frozen assets — actual current bytes and SHA-256

The J1 rights-verifier pass read and hashed each actual byte stream. The Phase 1C verifier independently reproduced the same values before its wrapper-only failure.

| Asset | Bytes | Actual SHA-256 | Gate |
|---|---:|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | PASS |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | PASS |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | PASS |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | PASS |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | PASS |

The Phase 1C verifier also returned SQLite immutable reconciliation integrity `ok`. No asset was opened for write or regenerated.

## Engineering and authority gate

Evidence supports `ENGINEERING_PRE_DDL_READY=true` at the decision boundary:

1. Candidate JSON is the only canonical migration input; SQLite is immutable reconciliation only; transfer/TRACE manifests are integrity evidence; Search, atlas, catalog, shards and caches are derived and cannot create canonical rows.
2. All 15,923 legacy input surfaces are accounted one-to-one for the conservative v49.0 object baseline. Legacy crosswalk, alias, merge, split, withdrawal and unresolved states are explicit; no automatic deduplication or silent delimiter split is authorized.
3. `core.entity` is a closed FK-backed supertype. Specific links use subtype FKs; deliberately multi-kind entity links use a real `core.entity` FK plus an allowed-kind rule. Arbitrary `target_type + target_id` is prohibited.
4. Assertion subject/value, assignment subtype, relation endpoint, rights observation/assessment subject and takedown target families are closed, exactly-one typed subtype structures. Assertion/evidence, assignment/assertion, relation/claim and claim/evidence cardinalities use explicit bridges.
5. Semantic relation, TRACE projection edge and object-relation membership have distinct identities/natural keys and count units. Unknown relations create only proposed/held workflow evidence; no relation, claim, TRACE edge or count row is inferred.
6. Owner/migrator/ingestor/reviewer/releaser/reader/auditor privileges, object ownership, `SECURITY DEFINER` allowlist and post-seal denial boundaries are fixed logically.
7. Research and visual releases have enforceable logical state, copied-projection, manifest, sidecar, post-seal immutability, CAS, compatibility and no-live-canonical-join requirements.

## Research-semantics gate

Phase 1C machine evidence and receipts agree:

```text
AUDIT_BASELINE_VERIFIED=true
LEGACY_INPUT_SURFACES=15923
ACCOUNTED_INPUT_SURFACES=15923
UNACCOUNTED_INPUT_SURFACES=0
BASELINE_ARCHIVE_OBJECTS=15923
RESEARCH_ELIGIBLE_OBJECTS=7995
TRACE_ELIGIBLE_OBJECTS=0
HELD_OBJECTS=7928
REJECTED_OBJECTS=0
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

The 2,970 scalar versus 2,971 row/set conflict is resolved in favor of the exact 2,971-member candidate/SQLite/catalog set. The candidate has 7,995 explicit `source_verified`, 2,971 explicit `metadata_supported`, and 4,957 blank-tier rows; SQLite's 12,952 normalization cannot backfill candidate semantics. The graph units remain distinct: 97,889 nodes, 255,695 projection edges, and 126,822 memberships. All graph facts are classified; positional zipping of the unequal legacy arrays is forbidden; the current strict TRACE corpus remains held at zero eligibility. These are evidence-preserving outcomes, not an unresolved research-semantic decision.

## Rights/visual gate

Evidence supports `RIGHTS_VISUAL_PRE_DDL_READY=true`:

- `external_visual_reference` is a provenance-occurrence identity, not a URL, provider object, archive object, permission or representation.
- Archive object ↔ external visual reference is N:M through a real-FK `object_visual_reference` bridge.
- Provider, provider object, policy version/evaluation, typed locator, rights observation/assessment, delivery decision, endpoint-health observation, attribution bundle, takedown event/scope/override, registry version/entry and pointer identities/cardinalities are locked.
- Rights evidence/assessment, provider-policy evidence/evaluation, delivery decision, endpoint health and takedown are five independent axes. Attribution is a positive-delivery prerequisite, not a collapsed rights status.
- Delivery has exactly five modes: `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, `REMOTE_IMAGE`. The 20-rule ordered truth table has one positive rule (`RD-080`) and no lower-mode remote-pixel leak.
- Takedown is highest-precedence and monotonic restrictive. Endpoint health can only retain or lower delivery and never establishes permission.
- The candidate baseline accounts for 15,923/15,923 visual bundles: 15,788 reference-bearing, 135 `NO_VISUAL_REFERENCE`, 15,790 locator occurrences and 15,788 distinct locator values. Inventory and typing are both 100%; unclassified is zero. All reference-bearing bundles remain conservatively `RIGHTS_UNKNOWN`, `POLICY_UNKNOWN`, and `UNMAPPED_PROVIDER`; positive-rights coverage is 0/15,788 = 0.0000%.

## Machine-contract and version gate

Evidence supports `MACHINE_CONTRACT_PRE_DDL_READY=true`:

1. Research and visual boundaries independently use `draft → candidate → validated → sealed`, immutable copied projections, canonical manifest bytes/SHA, detached post-seal sidecars and separate CAS-protected `current` pointers.
2. A visual version declares exactly one compatible research pair. A missing compatible registry produces a complete research-only response. An explicitly incompatible selected pair produces `409 RELEASE_VERSION_MISMATCH` with no fallback.
3. Every successful research response has non-null `researchReleaseId + researchManifestSha256` and atomically has either both `visualRegistryVersion + visualRegistrySha256` or two null visual fields.
4. Public stable IDs use `urn:gdarchive:{object|relation|claim|source|visual-reference}:<lowercase-uuid>`. `.example` strings are retained only as exact frozen UUIDv5 seed inputs; they are not public identities or resolver origins.
5. Public DTOs start empty and copy only closed `SAFE`/conditional `PUBLIC` fields. `INTERNAL`, `HELD`, raw and unclassified fields are structurally absent before cache and serialization. Only `REMOTE_IMAGE` may expose the v1 allowlisted `remoteImageUrl`; thumbnail/image-service fields remain absent even there in v1.
6. The public boundary is GET/HEAD/OPTIONS-only. The 39-case negative oracle covers rights/policy/health/takedown, registry absence/mismatch, serializer leakage, post-seal mutation, stale CAS and derived-to-canonical anti-write cases.

## Cleanup non-interference and measured cleanup fields

The rights/machine decision commit was complete before cleanup began, and the cleanup commit did not change its package or normative inputs. The bounded static cleanup result is therefore reported separately:

```text
AI_RUNTIME_RETIRED=true
QWEN_RUNTIME_IMPORTS=0
ACTIVE_ASSISTANT_ROUTES=0
MODEL_RUNTIME_PRODUCTION_IMPORTS=0
BULK_ROUTE_REGRESSION_BLOCKED=true
DORMANT_BULK_ROUTE_GENERATORS=0
DETERMINISTIC_SEARCH_PRESERVED=true
A4_VISUAL_COMPONENTS_PRESERVED=true
SAFE_DELETE_EXECUTED=docs/.DS_Store
DEFERRED_CLEANUP_COUNT=9
TSC_NOT_RUN=toolchain_absent
```

Seven historical Qwen probe files were moved byte-identically into a declared non-authoritative archive. The 60 QA image paths/bytes and four locked A4 component hashes match their baseline. The nine deferred cleanup scopes remain untouched.

## Readiness result

The false pre-DDL values in the Phase 1D decision manifest and normative documents are explicitly pending-this-joint-verifier states. They are not contradictory architecture values. This independent receipt is the required transition evidence.

```text
AUTHORITY_RESEARCH_DELTA_CLOSED=true

RIGHTS_VISUAL_DECISIONS_LOCKED=true
MACHINE_CONTRACT_DECISIONS_LOCKED=true
DUAL_RELEASE_MODEL_LOCKED=true
TAKEDOWN_AND_CAS_RULES_LOCKED=true

LEGACY_VISUAL_REFERENCE_INVENTORIED=100%
LEGACY_VISUAL_REFERENCE_TYPED=100%
LEGACY_POSITIVE_RIGHTS_COVERAGE=0.0000%
UNCLASSIFIED_VISUAL_REFERENCE=0

AI_RUNTIME_RETIRED=true
BULK_ROUTE_REGRESSION_BLOCKED=true
DETERMINISTIC_SEARCH_PRESERVED=true
SAFE_DELETE_EXECUTED=docs/.DS_Store
DEFERRED_CLEANUP_COUNT=9

ENGINEERING_PRE_DDL_READY=true
RESEARCH_SEMANTICS_PRE_DDL_READY=true
RIGHTS_VISUAL_PRE_DDL_READY=true
MACHINE_CONTRACT_PRE_DDL_READY=true
OVERALL_PRE_DDL_READY=true

DATABASE_IMPLEMENTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

Actual Read API routes, OpenAPI, JSON Schema, JSON-LD/Linked Art/PROV-O, DCAT, CI/deployment, frontend `ArchiveRepository` adoption, production health checks, browser/runtime QA and positive-rights adjudication remain later pre-freeze/pre-promotion gates. Their absence correctly leaves the last four implementation/readiness fields false; it does not reopen the physical-schema decisions above.

## Evidence commands

Representative read-only command families used by J1:

```text
git status --short
git rev-parse HEAD origin/refactor/v49-data-platform
git rev-list --left-right --count HEAD...origin/refactor/v49-data-platform
git merge-base --is-ancestor <required-commit> HEAD
git show -s --format=... <phase commits>
git diff --name-status / --name-only / --check <commit boundaries>
git show 967cbe3:<Phase-1C-normative-path> | shasum -a 256
python3 -m json.tool <A/B/C manifests and summaries>
shasum -a 256 -c <A/B/C CHECKSUMS.sha256>
python3 scripts/verify_v49_authority_research_delta.py --json
python3 scripts/verify_v49_rights_machine.py --json
python3 scripts/verify_v49_runtime_cleanup.py
rg -n <authority/identity/cardinality/state/version/serializer terms> <normative corpus>
```

J1 did not rerun a failed verifier, did not run two candidate parsers concurrently, and did not open a duplicate hash pass while a verifier was active.

## Process receipt and explicitly unperformed actions

- Phase 1C verifier unified session `4479` exited `1` after its wrapper-only result; no restart.
- Rights/machine verifier unified session `20605`, reported PID `26122`, exited `0`; no restart.
- Cleanup verifier unified session `4880` exited `1` after its committed-state wrapper result; no restart.
- Direct `ps` and `pgrep` process-list health checks were denied by the sandbox. All three task-owned unified sessions returned terminal exit codes, J1 launched no background task, server, compiler, browser, database, package process or generator, and `TASK_OWNED_RESIDUAL_PROCESSES=0`. The primary controller owns the final repository-wide sanitized residual-process receipt after this file is written.

Explicitly not performed: PostgreSQL/DDL, SQLite write, migration, import/export/regeneration, Docker, npm, dependency installation, Next dev/build/start, TypeScript compilation, browser automation, screenshot, HTTP/IIIF/provider probe, image download, frozen/QA-image/protected-main mutation, data repair, stage, commit, push, PR, merge or deployment.

```text
J1_EXIT=PASS
TASK_OWNED_RESIDUAL_PROCESSES=0
FILES_WRITTEN_BY_J1=docs/audits/v49-phase1d-final/00_JOINT_PRE_DDL_GATE_RECEIPT.md
```

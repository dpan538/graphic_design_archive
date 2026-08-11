# 13 — Authority/research gate receipt

- Package: v49 Phase 1C
- Baseline commit: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Frozen ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Detached independent review: **PASS**
- Final immutable-package recheck: performed by the primary task after regenerating `MANIFEST.json` and `CHECKSUMS.sha256`; its command receipt is the Git handoff, avoiding a self-referential checksum cycle

## Gate contract

This receipt closes an authority/research delta only when exact bytes, sets, units, and fail-closed dispositions verify together. A held row remains accounted; closure never means silent promotion. SQLite, manifests, Search, and TRACE are never allowed to create canonical rows or fill a candidate-JSON gap.

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
PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

## Measured acceptance evidence

| Gate | Evidence | Result |
|---|---|---|
| Five frozen bytes/hashes | one sequential SHA-256 pass over the five named assets | PASS; all exact |
| SQLite immutability/integrity | `mode=ro&immutable=1`, `PRAGMA query_only=ON`, one `integrity_check` | PASS; `ok` |
| Input accounting | 15,923 source ordinals/JSON pointers/unique surface IDs/unique source-record IDs | PASS; unaccounted 0 |
| Deterministic object seed | UUIDv5 URL namespace and exact surface-name recipe | PASS; 15,923 unique IDs |
| Metadata scalar conflict | candidate rows ↔ SQLite ↔ catalog set comparison | PASS; 2,971/2,971/2,971, symmetric diff 0; scalar 2,970 retained |
| Missing-tier normalization | candidate ↔ SQLite set delta | PASS fail-closed; exact 4,957-set is derived-only |
| Graph units | 97,889 nodes / 255,695 edges / 126,822 memberships / 30 active trees / 20 active labels | PASS as distinct units |
| Candidate edge semantics | 126,822 opaque edge IDs / 79,683 labels / 9,393 unequal arrays | PASS; authorized zip mappings 0 |
| Graph classification | per-unit closed classification and 40-entry relation registry | PASS with explicit holds; unclassified 0 |
| Unknown relation | null family/class + proposed/held/review default | PASS; silent fallback 0 |
| Influence | claimant/source/locator/wording minimum and observed count | PASS; automatic inference 0, observed 0 |
| Research corpus | versioned 15,923-row membership ledger | PASS; eligible 7,995 / held 7,928 / rejected 0 |
| TRACE corpus | accepted claim/relation eligibility | PASS fail-closed; eligible 0 / held 15,923 |
| Missingness | versioned row-level baseline and set hashes | PASS |
| Raw/source evidence | 1,599 paths, 96,019,917 bytes, all SHA/dispositioned | PASS; unclassified 0 |
| Search/TRACE reconciliation | Search 8,636; intersection 2,585; Search-only 6,051; candidate-only 13,338 | PASS; derived-only |
| TRACE integrity | 580 declared assets including 576 shards | PASS when machine verifier reports zero declared hash failures |
| 20,000 policy | normative terminology scan | PASS; historical/capacity only, never acceptance |

## Reproduction commands

The following command families are the acceptance boundary; commands that write or regenerate frozen assets are excluded.

```text
git fetch origin
git rev-parse HEAD
git rev-parse origin/refactor/v49-data-platform
git merge-base --is-ancestor 0404c7f96f9189f576c4c5b1368061e4082e436b HEAD
shasum -a 256 <the five frozen assets>
sqlite3 'file:<absolute-v48-sqlite>?mode=ro&immutable=1' 'PRAGMA query_only=ON; PRAGMA integrity_check;'
python3 scripts/verify_v49_authority_research_delta.py --json
git diff --check
```

The verifier is deterministic, stdout-only, standard-library Python. It opens no network connection, writes no database or frozen asset, and has no v47 parent in its allowed input set. It validates frozen hashes, transfer/TRACE asset declarations, candidate/SQLite/Search/catalog populations, graph/corpus/raw ledgers, package manifest, and package checksums.

## Independent verification

Detached A5 returned **PASS**. It executed the formal verifier with exit 0, 134/134 checks, and zero errors; independently parsed the JSON/TSV contracts; used artifact-tool sampling to confirm all four TSV shapes and boundary rows; found no authority/count/research contradiction; and left zero task-owned residual process. The evidence and command boundary are recorded at `agents/A5_INDEPENDENT_VERIFIER_RECEIPT.md`.

The primary task then includes the A5 receipt in the final manifest/checksum and runs the same verifier over that immutable package. The final command output is intentionally external to the hash set: embedding a post-manifest result inside a checksummed input would mutate the package being verified.

## Remaining cross-phase blockers

These are not unclassified Phase 1C facts. They are deliberate downstream gates:

1. Prompt B must close rights observations, provider policy, endpoint health, delivery mode, takedown, independent visual registry, and machine pixel exposure.
2. No accepted claimant-bound claims or semantic relations have been transformed from v48; all current TRACE projection eligibility therefore remains zero.
3. PostgreSQL physical schema, migration, roles, seals, Read API, adapters, CI, frontend cutover, freeze, promotion, and deployment are unimplemented.

## Actions explicitly not performed

No prohibited server, compiler, browser, database writer, export, image fetch, main-worktree mutation, PR, merge, force operation, deployment, or frozen-asset rewrite was performed. Final branch/process/main-fingerprint/Git receipts are owned by the primary task after detached verification.

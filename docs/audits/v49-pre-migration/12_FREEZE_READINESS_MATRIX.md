# Freeze readiness matrix

## Scope and result

This matrix separates audit coverage, architecture decisions, physical implementation, data freeze, frontend promotion, and deployment. A passing read-only audit or normative document is not evidence that PostgreSQL, releases, APIs, adapters, CI, or production behavior exist.

```text
AUDIT_COMPLETE=true
PRE_DDL_READY=false
ENGINEERING_PRE_DDL_READY=false
RESEARCH_SEMANTICS_PRE_DDL_READY=false
RIGHTS_VISUAL_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
FREEZE_READY=false
DATABASE_FREEZE_READY=false
PROMOTION_READY=false
FRONTEND_PROMOTION_READY=false
DEPLOYMENT_READY=false
```

Result: **PARTIAL**. Evidence coverage is complete across all ten packages, but pre-DDL and every later delivery state remain blocked.

## Frozen-source gate

| Asset | Bytes | Observed SHA-256 | Authority | Result |
|---|---:|---|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | only v48 migration input; raw bytes lexical authority | PASS |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | immutable reconciliation only | PASS; `integrity_check=ok` |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | integrity evidence | PASS |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | integrity/human-audit evidence | PASS |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | integrity evidence for derived TRACE product | PASS |

All five actual byte streams were checked in one primary pass. SQLite was opened exactly once for current-run integrity using `mode=ro&immutable=1`; no journal/WAL/SHM or sidecar was created. Search, TRACE shards/catalogs/atlas, and SQLite remain prohibited as canonical-row suppliers.

## Acceptance-gate matrix

| Gate | Architecture/audit state | Current implementation/evidence state | Phase 1B result | Blocking boundary |
|---|---|---|---|---|
| G0 Worktree/source recovery | initial local/remote/branch/ancestor/main fingerprints PASS; final commit/push verification is an external closeout receipt | documentation changes only | PASS subject to final Git receipt | local checkpoint/push |
| G1 Frozen byte integrity | authority roles and exact ledger complete | all five bytes/hashes plus SQLite integrity verified | PASS | source recovery |
| G2 Counts/units | canonical/graph/derived/historical taxonomy corrected; 20,000 removed from gates | population sets measured; 2,970/2,971 conflict and future PostgreSQL parity unresolved | PARTIAL | pre-DDL/migration |
| G3 Architecture corpus | nine existing documents plus ADR 0004 cross-calibrated | no code/data/visual change | PASS for documentation scope | architecture checkpoint |
| G4 Canonical normalization | object semantics, typed identity, predicates, assignment list, evidence/decision/claim bridges specified | field-level authoritative mapping and graph-fact classification incomplete | PARTIAL | pre-DDL |
| G5 Unknown relation fail-closed | registry/FK/queue/no-projection behavior specified | current code still maps unknown to `medium_context/documented`; no negative fixture | FAIL | pre-DDL/release/frontend |
| G6 Repository/Read API | dual-pair `ArchiveRepository`, adapters, GET-only endpoints, DTO/error/cursor contract specified | zero `/api/v1` routes/adapters/fixtures/conformance suite; 35 direct coupling files | PARTIAL | frontend implementation |
| G7 Immutable manifests/seals | independent research/visual lifecycle, pre-seal receipts, manifest SHA, detached sidecar, sealed copied projections, CAS specified | no v49 manifest/shard/seal/sidecar/CAS implementation | PARTIAL | database freeze |
| G8 Data/frontend CI split | ownership and receipt boundaries specified | zero CI workflows | PARTIAL | freeze/promotion |
| G9 Prototype prohibition | phase-scoped command matrix explicit | no npm/Next/full TypeScript/browser/export/Docker/PostgreSQL process run by task | PASS | Phase 1B process |
| G10 Migration parity/promotion | M1–M8 and rollback boundaries specified | no database/import/dual-read/build/browser/promotion evidence | PARTIAL | migration/promotion |
| G11 Residual process/receipt | receipt format exists | package residual sessions zero; pre-existing unrelated services segregated; final sanitized scan required at closeout | PASS subject to final scan | local checkpoint |
| G12 Repository hygiene | 14,359-row ledger, duplicate/large/LFS/generated/owner/recovery/actions complete | cleanup execution intentionally absent; one safe candidate, 186 effective holds | PASS for classification; PARTIAL for cleanup | cleanup/freeze |
| G13 Research/data-quality freeze | object/claim/relation/TRACE, four epistemic classes, corpus/missingness/concentration contract specified | graph authority, claims/corpus/missingness data and research-quality receipt absent | PARTIAL | pre-DDL/research freeze |
| G14 Machine-readable contract | URI/HTML/JSON Schema/JSON-LD/Linked Art/PROV-O/DCAT/diff/sitemap contract specified | implementation 0/18 measured features; current sole API is POST assistant evidence | PARTIAL | API/promotion |
| G15 Rights/visual federation | dual version identity, provider/endpoint types, rights axes, fail-closed delivery, takedown and CAS specified | 15,621 URLs/49 hosts lack complete governed crosswalk/policy; current remote pixels can leak | FAIL | pre-DDL/visual freeze/promotion |

No gate with `PARTIAL` or `FAIL` authorizes the boundary it protects.

## Pre-DDL readiness decomposition

### Engineering

`ENGINEERING_PRE_DDL_READY=false` because:

- current-tree v47 parent inputs used by v48 builders are absent;
- the canonical JSON cannot currently regenerate the full graph;
- the 2,970/2,971 conflict lacks a reviewed delta decision;
- legacy `db/*.sql` is an incompatible 82-table/55-view public-schema prototype and its runner is not yet execution-denied by an implemented gate;
- exact logical-to-physical mappings, roles/default privileges, negative privilege tests, backup/restore, and fresh migration namespace do not exist.

### Research semantics

`RESEARCH_SEMANTICS_PRE_DDL_READY=false` because:

- the 15,923 Browse Index is not a versioned strict corpus;
- graph facts are not fully classified as regenerable, governed evidence, or hold;
- epistemic claim/semantic relation/TRACE projection separation is normative but not populated or measured;
- influence and computed-association provenance, missingness, coverage, concentration, and research-quality receipt are absent.

The 15,923 objects, 97,889 nodes, 255,695 projection edges, and 126,822 membership projections remain important scale and portfolio evidence; visual complexity is not a deletion criterion.

### Rights and visual federation

`RIGHTS_VISUAL_PRE_DDL_READY=false` because:

- no sealed visual registry, manifest, sidecar, independent current CAS, or compatible research pair exists;
- provider object and canonical-record/IIIF manifest/viewer/thumbnail/image-service endpoints are not fully typed;
- rights observations/policies, assessment, delivery mode, endpoint health, attribution, review due, and takedown are incomplete;
- 1,266 raw/third-party files and existing QA pixels lack complete artifact-level disposition;
- legacy IMG/IIIF paths and UI code may still expose remote pixels.

Unknown, missing, conflicting, or stale evidence must produce only `LINK_ONLY` or `CITATION_ONLY`. API accessibility, IIIF presence, redirects, provider identity, or endpoint health never grants pixel authorization.

## Lifecycle dependencies

| Later phase | Required predecessor evidence | Current state |
|---|---|---|
| Physical schema design/DDL | all three pre-DDL decompositions PASS; approved mapping; legacy runner deny; exact role/dual-seal test plan | BLOCKED |
| Database migration | replayable empty-schema migrations, privilege/constraint tests, pure baseline verifier, all five frozen hashes, authority delta closure | BLOCKED; database absent |
| Data freeze | imported canonical parity, approved graph deltas, corpus/research-quality receipt, visual rights receipt, deterministic dual manifests/seals/CAS, data CI | BLOCKED |
| Frontend repository integration | sealed/fixture contract, dual-pair schema, held-pixel negative tests, bounded pagination, zero direct storage coupling | BLOCKED |
| Frontend promotion | passing data receipt plus independent frontend CI, focused contract/accessibility first, then authorized full TypeScript/build/browser/visual lane and rollback | BLOCKED |
| Final push of this documentation checkpoint | changed-file allowlist, checksums/links/terminology, main fingerprint, residual process, `git diff --check`, remote race check | allowed only after all closeout checks |

## Priority totals

The ten packages contributed 52 P0, 58 P1, and 25 P2 observations. Because findings overlap, these are evidence contributions rather than 135 unique defects. Consolidated root P0 themes are authority/reproducibility, legacy DDL isolation, research semantics, rights/visual federation, frontend/data coupling, AI runtime retirement, QA/accessibility evidence, and machine publication/CI.

## Evidence commands and validation

Evidence commands include read-only Git/ref/worktree/history/LFS/blob enumeration; full path and size/signature inventory; bounded SHA-256 duplicate confirmation; one full five-asset hash pass; immutable SQLite schema/statistics/integrity queries; static source/package/config searches; OOXML text inventory; QA MIME/dimension/hash inspection; path/link/terminology/state/count checks; changed-file allowlist; `git diff --check`; and sanitized residual-process scans. Exact commands are retained in reports 01–10 and 13.

## Risk and recommended action

The dominant risk is freezing a technically consistent but epistemically and legally invalid system: derived TRACE facts could become canonical, catalog records could be misrepresented as unique works, and reachable image endpoints could be treated as authorized pixels. The next work must close authority and rights evidence before expressing those assumptions in physical keys or release projections.

Recommended action: execute the three independent work packages in `00_EXECUTIVE_SUMMARY.md` with explicit stop conditions. Do not combine DDL/import, visual-registry research, and frontend cutover into one change.

## Actions explicitly not performed

No PostgreSQL/Docker/npm/Next/full TypeScript/browser/data-export/image-download/destructive-cleanup activity occurred. No migration, verifier, API, adapter, fixture, CI, dependency, frontend, visual, QA, frozen asset, or protected-main path was changed. No PR, merge, deploy, force push, or history cleanup occurred.

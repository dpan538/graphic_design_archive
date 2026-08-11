# v49 Phase 1C — Authority, count parity, and research-delta receipt

- Baseline branch: `refactor/v49-data-platform`
- Initial local/remote commit: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Package status: **AUTHORITY_RESEARCH_DELTA_CLOSED_WITH_EXPLICIT_HOLDS**
- PostgreSQL/database implementation: **not performed**
- Prompt B rights/visual/machine-exposure closure: **not performed**

## Outcome

Phase 1C closes the pre-migration authority, baseline-object accounting, graph-fact classification, research-corpus, missingness, raw-evidence disposition, and unknown-relation decisions. Closure means that every scoped input and graph-fact unit has an explicit authority/disposition and that no unsupported fact is silently promoted. It does not mean that a database, semantic relation, research claim, TRACE release, rights registry, API, frontend cutover, freeze, promotion, or deployment exists.

The decisive correction is that `12,952 source_verified` is not a lexical candidate-JSON population. The sole canonical input contains 7,995 explicit `source_verified` rows, 2,971 explicit `metadata_supported` rows, and 4,957 rows with no `trace.tier`. A legacy SQLite builder normalized those 4,957 missing values to `source_verified`. v49 preserves the missingness and fails those rows closed for research eligibility.

## Frozen authority boundary

| Asset | Bytes | Recomputed SHA-256 | Phase 1C role |
|---|---:|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | sole canonical migration input; lexical byte authority |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | `mode=ro&immutable=1` reconciliation only; `integrity_check=ok` |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | integrity evidence |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | integrity/human-audit evidence |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | integrity evidence for 580 derived TRACE assets |

The two absent v47 direct parents remain historical LFS recovery references. They are not restored and are not v49 migration inputs. Frozen-output verification, not legacy v48 replay, is the preservation contract. The read-only verifier has no v47 parent in its input allowlist.

## Baseline and corpus accounting

| Unit | Count | Disposition |
|---|---:|---|
| Legacy input surfaces | 15,923 | every row accounted |
| Baseline archive objects | 15,923 | deterministic one surface → one UUIDv5 object; no merge/dedup |
| Research-eligible objects | 7,995 | explicit candidate `source_verified` tier |
| Research-held objects | 7,928 | 4,957 missing tier + 2,971 metadata-only |
| Research-rejected objects | 0 | no evidence-bearing rejection was inferred |
| TRACE-eligible objects | 0 | no accepted claim/relation path is authoritative in the sole input |
| Unaccounted input surfaces | 0 | none dropped, expanded, split, or silently merged |

The versioned row ledger is `10_CORPUS_MEMBERSHIP_BASELINE.tsv`; its 15,923 rows bind source ordinal, JSON pointer, legacy IDs, candidate tier, research disposition, TRACE disposition, reason codes, and Search presence. The strict corpus policy does not treat Browse, Search, catalog, tree, edge, or accepted legacy workflow presence as research evidence.

## Metadata-supported conflict

The exact mismatch unit is the scalar `/meta/traceMetadataSupportedCount=2970`. It has no member list. Candidate row membership, immutable SQLite membership, and TRACE catalog membership each contain the same 2,971 surface IDs; their symmetric differences are zero. Therefore there is no honest “extra row” to invent. The scalar is retained as a stale historical annotation, while the 2,971 candidate row set controls membership.

## Graph and epistemic closure

| Graph unit | Count | Closed disposition |
|---|---:|---|
| Candidate opaque edge-ID references | 126,822 | crosswalk assertions only |
| Candidate independent relation-label occurrences | 79,683 | 73,843 proposed documented-source routes + 5,840 computed associations |
| Rows whose edge-ID/label arrays cannot be zipped | 9,393 | authorized positional mappings = 0 |
| Full SQLite graph edges | 255,695 | 217,554 legacy projection + 6,004 computed + 32,137 held |
| Active object-edge memberships | 126,822 | 120,982 legacy projection + 5,840 computed |
| TRACE nodes | 97,889 | legacy projection only |
| Active research trees / active labels | 30 / 20 | organizational/display reconciliation only |
| Full-graph labels | 39 | all classified; 19 full-only labels held with null family/class |
| Influence | 0 | no automatic inference; not a claim that influence never existed |

The epistemic registry contains all 39 observed labels plus reserved `influenced_by`. It structurally separates documented source statements, scholarly claims, computed associations, and causal interpretations. All current entries are non-projectable. Unknown labels resolve to `HELD_UNSUPPORTED`, null relation family, null epistemic route, and `proposed/held/review`; they create no relation, TRACE projection, publication row, or metric eligibility.

## Raw/source evidence closure

The raw-evidence ledger accounts for 1,599 tracked artifacts totaling 96,019,917 bytes: 1,561 raw-directory artifacts and 38 authored source records. All have SHA-256 and an explicit provenance/evidence/research-use disposition. Thirty transfer-selected provider responses match their declared hashes and remain legacy-reconciliation evidence only; 1,569 artifacts are `HELD_UNSUPPORTED`. Visual rights, provider policy, endpoint health, and delivery mode are deliberately not adjudicated here.

## Machine gate fields

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

`AUTHORITY_RESEARCH_DELTA_CLOSED=true` is compatible with `TRACE_ELIGIBLE_OBJECTS=0`: the former records complete classification and fail-closed policy; it does not claim promotion eligibility. `PRE_DDL_READY` remains false because Prompt B must still close rights, visual-registry, and machine-exposure decisions.

## Normative correction

Only empirically conflicting count language was changed in `DATA_MODEL_V49.md`, `MIGRATION_V48_TO_V49.md`, and `ACCEPTANCE_GATES.md`. The documents now separate 7,995 explicit source-verified rows, 4,957 missing-tier rows, 2,971 metadata-supported rows, and the derived SQLite/TRACE normalization of 12,952. The historical 20,000/4,077 values remain explicitly non-gating capacity/collection history.

## Explicitly not performed

- no PostgreSQL, DDL, migration, database write, import, export, or data regeneration;
- no v47 recovery, LFS fetch, frozen-file edit, automatic deduplication, merge, split, or delimiter parsing;
- no npm install, Next.js, TypeScript, browser, screenshot, Docker, image download, or HTTP probing;
- no rights/provider/delivery decision, frontend change, API implementation, PR, merge, deployment, or dirty-main cleanup.

Whole-package machine verification is performed by `python3 scripts/verify_v49_authority_research_delta.py --json`; the final command and independent-review result are recorded in `13_AUTHORITY_RESEARCH_GATE_RECEIPT.md` and `agents/A5_INDEPENDENT_VERIFIER_RECEIPT.md`.

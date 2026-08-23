# TRACE v49 Round 1 — Executive Decision

## Decision

`GO_FOR_PREPROGRAM_FOUNDATION_ONLY`.

The frozen v49 release supports honest empty-state TRACE contracts and renderer-neutral preprogramming. It does **not** support a public semantic graph or any of the three public domain datasets yet. No visualization implementation is authorized by this round.

The decisive count reconciliation is:

- 15,923 canonical archive objects;
- 7,995 eligible/public release objects;
- 7,928 held objects;
- 47,982 **proposed curated folder-membership assignments**;
- 0 relation types, claims, evidence items, or `research.semantic_relation` rows;
- 0 accepted or public TRACE edges;
- 0 TRACE-eligible public objects.

`database/FREEZE_V49.json` calls 47,982 `relationshipCount`, but the producer metric is `folderMembershipAssignments`. The parent `provenance.canonical_assignment` rows and typed `provenance.assignment_folder_membership` rows are the same 47,982 assignments and must not be added. The unambiguous name is `FOLDER_MEMBERSHIP_ASSIGNMENT_COUNT=47982`.

## Answers to the executive questions

| Question | Empirical answer |
|---|---:|
| True semantic relations | 0 |
| Registered relation types | 0 |
| Accepted / review / held / rejected / unknown relation rows | 0 / 0 / 0 / 0 / 0 |
| Relations satisfying required evidence | 0 |
| PUBLIC→PUBLIC / PUBLIC→HELD / HELD→HELD | 0 / 0 / 0 |
| Public TRACE-eligible objects | 0 / 7,995 |
| Public objects with a currently projected usable TRACE domain | 0 / 7,995 |
| Public objects with internal context candidates | 7,995 / 7,995 |
| Public objects with raw time candidates | 7,995 / 7,995 |
| Public objects with raw place/region candidates | 7,995 / 7,995; all 7,995 coordinate-unmapped |
| Public objects with internal raw-source bridges | 7,995 / 7,995 |
| Public objects with normalized evidence items or claims | 0 / 7,995 |
| All three domains public-projectable | 0 / 7,995 (0%) |
| No public-projectable domain | 7,995 / 7,995 (100%) |
| Accepted v49 local graph nodes P50/P95/P99/max | 1 / 1 / 1 / 1 |
| Accepted v49 local graph edges P50/P95/P99/max | 0 / 0 / 0 / 0 |

Context is the most complete **candidate** domain: every public object has raw medium/theme context and folder candidates, with median 5 combined candidate associations and maximum 9. It is still unreviewed and unprojected. Sources/evidence is least complete: only the restricted raw-record bridge exists; normalized source documents, assertions, evidence, claims, and relation evidence are all empty.

## Readiness

```text
CONTEXT_V1=READY_FOR_PREPROGRAM_ONLY
SPACETIME_V1=SEMANTIC_REVIEW_REQUIRED
SOURCES_V1=READY_FOR_PREPROGRAM_ONLY
```

What is safe now: the current zero-evidence atlas, valid empty collections, release-bound not-published singleton responses, aggregate audit statistics, public stable-ID-only development samples, and the disconnected pure-function foundation.

What needs semantic review: folder/controlled assignments, place roles, date roles and precision, candidate relation predicates, directionality, and evidence requirements.

What needs a new public read projection: every non-empty context, spacetime, source/evidence, claim, relation, or aggregate payload. Raw payloads and internal UUIDs are not public serializers.

What needs a future data release: any accepted semantic relation, governed claim/evidence chain, public relation-type registry, normalized place role/coordinate evidence, and evidence-bearing source function. Frontend work alone cannot create these facts.

## Implementation outcome

The new `frontend/src/features/trace-v49/` package enforces separate types for semantic edges, controlled assignments, curated memberships, source associations, and visual guides; validates public object endpoints and evidence policies; preserves time/place precision and unknowns; emits denominated aggregates; is deterministic and non-mutating; and provides accessible row representations. It is not imported by `/trace`.

Measured synthetic structures sized to the public v49 density envelope had maximum projection P95 0.035545 ms on Node 22 arm64; maximum serialized output was 6,954 bytes. This validates synchronous pure projection at present sizes, not future endpoint or rendering performance.

Blockers are recorded as P0=0, P1=7, P2=3. The absence of P0 means the delivered disconnected package has no known active held-data leak or accepted-edge evidence violation; it does not mean public TRACE is ready.

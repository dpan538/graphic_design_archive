# 12 — TRACE Projection Delta

- Package: v49 Phase 1C A7
- Registry: `v49.epistemic-relation-registry/1.0.0`
- Baseline commit: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Result: **PASS_WITH_EXPLICIT_HOLDS**

`PASS_WITH_EXPLICIT_HOLDS` means every frozen graph-fact unit and every observed relation label has a deterministic epistemic/authority disposition, unknown relations fail closed, and no v48 graph row is silently promoted. It does not mean that any v49 semantic relation, claim, TRACE projection, database or release has been implemented.

## 1. Scope and authority boundary

This delta reconciles the frozen v48 graph/display model with the v49 evidence → claim → semantic relation → TRACE projection model. It is based on the measured A2/A3 evidence in [03_GRAPH_FACT_CLASSIFICATION_RULES.json](./03_GRAPH_FACT_CLASSIFICATION_RULES.json), [04_GRAPH_FACT_RECONCILIATION.json](./04_GRAPH_FACT_RECONCILIATION.json), and the versioned [08_EPISTEMIC_RELATION_REGISTRY.json](./08_EPISTEMIC_RELATION_REGISTRY.json).

The authority boundary is fixed:

| Layer | Authority | Permitted use in this delta |
|---|---|---|
| v48 candidate JSON | Sole canonical migration input | Preserve exact source-row assertions and legacy crosswalk literals as proposed facts |
| Immutable SQLite | Reconciliation evidence only | Reconcile graph units and preserve legacy projection history |
| TRACE manifest | Integrity evidence | Verify the frozen derived product boundary |
| Atlas, catalog, neighborhoods and client payloads | Derived products | Display/reconciliation evidence only; never reverse-ingested |

TRACE is a release- and corpus-specific projection of eligible relations and claimant-bound claims. It is not canonical authority. A frozen v48 edge ID or directed triple is a legacy projection identity, not the natural identity of a v49 claim or semantic relation.

Visual rights, provider policy, endpoint health and delivery mode are explicitly outside this package.

## 2. Measured unit boundary

| Unit | Exact value | Interpretation limit |
|---|---:|---|
| Candidate relation-label occurrences | 79,683 | Per-surface vocabulary occurrences; not edge predicates |
| Candidate opaque edge-ID occurrences | 126,822 | Legacy crosswalks; not typed relations |
| Surfaces with unequal `edgeIds`/`edgeLabels` lengths | 9,393 | Positional zipping is prohibited |
| TRACE nodes | 97,889 | Legacy projection nodes; not archive objects or claims |
| Full graph edges | 255,695 | Frozen directed projection rows |
| Active object–relation memberships | 126,822 | Projection membership rows; not distinct claims or relations |
| Active relation labels | 20 | v48 display registry vocabulary |
| Full graph relation labels | 39 | 20 active plus 19 full-graph-only literals |
| Active research trees | 30 | Curated organizational projections |
| Influence edges/memberships | 0 / 0 | Current no-inference result; not proof that historical influence never occurred |

The 79,683 label occurrences and 126,822 edge IDs are independent arrays. In 9,393 of 15,923 source rows their lengths differ. Therefore the authorized edge-ID → label mappings reconstructed from the candidate are exactly **zero**. Zipping the arrays would manufacture predicates and invalidate both provenance and count parity.

## 3. Closed graph-fact reconciliation

### Candidate source-row layer

| Occurrence unit | Classification | Count | Promotion limit |
|---|---|---:|---|
| Non-analytical relation-label occurrence | `CANONICAL_ASSERTION_CANDIDATE` | 73,843 | Proposed source-bound literal only; no endpoint/evidence mapping |
| Cluster/theme relation-label occurrence | `COMPUTED_ASSOCIATION` | 5,840 | Held until a governed analysis run exists |
| Opaque edge-ID reference | `CANONICAL_ASSERTION_CANDIDATE` | 126,822 | Crosswalk only; cannot be assigned a predicate by array position |
| Authorized edge-ID/predicate mapping | none | 0 | Candidate schema does not contain one |

### Immutable SQLite/full-graph layer

| Full-edge disposition | Count | Meaning |
|---|---:|---|
| `LEGACY_PROJECTION_ONLY` | 217,554 | Known non-analytical display labels retained only for reconciliation/history |
| `COMPUTED_ASSOCIATION` | 6,004 | Cluster/theme analytical rows lacking governed analysis-run provenance |
| `HELD_UNSUPPORTED` | 32,137 | Nineteen labels absent from the active v48 registry; family and epistemic class remain null |
| `REJECTED` | 0 | No exact evidence-bearing rejection decision was observed |
| Unclassified | 0 | Every full-graph row has one closed disposition |
| **Total** | **255,695** | Exact full graph edge unit |

The 126,822 active object–edge membership rows remain a separate projection unit: 120,982 known non-analytical legacy memberships plus 5,840 computed-association memberships. Evidence changes do not alter this legacy membership count, and it must not be recounted as semantic relations or claims.

## 4. Epistemic relation registry

The machine registry contains all 39 full-graph labels plus the reserved zero-count `influenced_by` predicate. It does not infer a claim class from a relation label; it assigns a required evidence route that a future claim must independently satisfy.

| Route | Relation labels | Candidate occurrences | Full-graph edges | Current projectable |
|---|---:|---:|---:|---:|
| `documented_source_statement` | 18 | 73,843 | 217,554 | 0 |
| `computed_association` | 2 | 5,840 | 6,004 | 0 |
| `scholarly_claim` | 0 legacy default routes | 0 | 0 | 0 |
| `causal_interpretation` | 1 reserved, unobserved (`influenced_by`) | 0 | 0 | 0 |
| Unknown, no epistemic route | 19 | 0 | 32,137 | 0 |

`scholarly_claim` remains a first-class registered epistemic class for future claimant-bound statements, but no legacy label or v48 projection row is automatically assigned to it.

The 19 full-graph-only labels are:

```text
associated_with_community
captured_from_provider
contains_record
context_mentions_place
curated_by
dated_approximately
depicts
documents
documents_object
exposes_source_record
featured_artist
featured_designer
grows_to_version
has_version
includes_capture_batch
maintains_collection
maintains_collection_or_namespace
part_of_event
publishes_collection
```

Their literal names do not authorize a semantic guess. Each uses:

```text
classification = HELD_UNSUPPORTED
relation family = null
epistemic class = null
acceptance state = proposed
disposition = held
workflow state = review
semantic relation created = false
TRACE projection created = false
publication layer created = false
metric eligibility created = false
```

This closes the legacy fail-open paths that otherwise map unfamiliar labels to `medium_context/documented`. Those paths remain historical source code and are forbidden inputs to a v49 migration or release projection.

## 5. Evidence, claims, relations and projection delta

The v49 layers remain independent:

```text
immutable evidence item(s)
        │ supports / challenges / qualifies
        ▼
claimant-bound claim(s) with one epistemic class
        │ supports / challenges / qualifies
        ▼
typed semantic relation over core.entity endpoints
        │ selected by one versioned corpus and sealed release
        ▼
TRACE projection edge plus N:M tree/branch placements
```

The frozen candidate provides source-row label literals and opaque crosswalk IDs, but it does not contain an authoritative edge-ID/predicate map, directed endpoints, evidence bridge, accepted claim or normalized semantic relation. SQLite contains those legacy display structures but cannot fill the sole input's gaps. The exact current delta is therefore:

| v49 governed unit created from the v48 graph | Count |
|---|---:|
| Accepted research claims | 0 |
| Accepted semantic relations | 0 |
| Authoritative edge-ID/predicate mappings | 0 |
| Projectable registry relations | 0 |
| TRACE-eligible archive objects | 0 |
| v49 TRACE projection edges | 0 |

These zeros are authority conclusions for this Phase 1C baseline. They preserve the 255,695-edge v48 product as frozen research visualization and reconciliation evidence; they do not claim that the historical relations are false or valueless.

## 6. Influence and causal interpretation

`influenced_by` is reserved but unobserved. Its family is `historical_influence`, its required epistemic route is `causal_interpretation`, and its current promotion/projectability is false.

Any future influence claim must retain:

- named claimant and role;
- claimant wording, not only a generated paraphrase;
- source or citation and exact locator;
- typed subject and object, direction and scope;
- temporal qualification;
- stance, evidence chain and competing claims;
- heightened reviewer decision;
- relation-policy version and the release/corpus in which it is projected.

Chronology, geography, medium, source, similarity, cluster, theme, co-occurrence, layout or numeric score cannot infer influence. The frozen count of zero is a successful no-inference boundary, not evidence that influence never existed.

## 7. Gate result

| Gate | Result | Evidence |
|---|---|---|
| All 39 full-graph labels have a registry entry | PASS | Exact label-set comparison; no missing or extra observed label |
| Relation counts reconcile | PASS | 79,683 candidate labels; 126,822 memberships; 255,695 full edges |
| Unknown relation default is fail-closed | PASS | 19 labels / 32,137 edges held with family and epistemic class null |
| Candidate edge IDs and labels are never zipped | PASS | 9,393 unequal-array surfaces; authorized mappings 0 |
| Epistemic classes are structurally distinct | PASS | Four closed classes and class-specific evidence profiles |
| Automatic influence inference | PASS | 0 |
| Unclassified graph fact | PASS | 0 |
| Current TRACE eligibility | PASS (fail-closed) | 0 objects; no accepted relation/claim path |

```text
UNCLASSIFIED_GRAPH_FACT=0
UNKNOWN_RELATION_FAIL_CLOSED=true
SILENT_UNKNOWN_RELATION_FALLBACK=0
AUTOMATIC_INFLUENCE_INFERENCE=0
TRACE_ELIGIBLE_OBJECTS=0
```

## 8. Closed findings and remaining promotion blockers

### P0 closed by this package

- **A7-P0-01 — Manufactured edge predicates:** closed by treating all 126,822 edge IDs as opaque crosswalks and authorizing zero positional mappings.
- **A7-P0-02 — Unknown-relation fallback:** closed by a versioned null-family/null-epistemic default and explicit holds for all 32,137 occurrences.
- **A7-P0-03 — Epistemic conflation:** closed by separating documented source statements, scholarly claims, computed associations and causal interpretations from relation labels and projection styles.
- **A7-P0-04 — Influence inference:** closed by a mandatory claimant/source/locator/wording contract and zero automatic inference.
- **A7-P0-05 — TRACE authority:** closed by declaring TRACE a release/corpus projection and retaining every v48 graph row as reconciliation/history rather than canonical research input.

### Remaining explicit holds

- no authoritative candidate mapping from edge ID to predicate, endpoints or evidence;
- no accepted claimant-bound claim or normalized semantic relation derived from the v48 graph;
- no governed analysis-run identity for 6,004 cluster/theme full-graph edges;
- no approved typed registry mapping for 19 full-graph-only labels;
- no approved locator-only evidence profile for the three graph-only blank-text observations identified by A3.

These holds block graph promotion and keep `TRACE_ELIGIBLE_OBJECTS=0`; they do not leave graph facts unclassified.

## 9. Actions explicitly not performed

- No candidate JSON, SQLite, manifest, TRACE asset, shard, Search asset or frozen receipt was modified.
- No candidate or SQLite rescan, integrity check, data export, regeneration, migration, DDL or database write was performed by A7.
- No graph edge, claim, relation, corpus member or TRACE projection was created.
- No rights, provider, delivery or endpoint-health decision was made.
- No PostgreSQL, Docker, npm, Next.js, TypeScript, browser, HTTP, image, frontend, PR, merge or deployment process was started.

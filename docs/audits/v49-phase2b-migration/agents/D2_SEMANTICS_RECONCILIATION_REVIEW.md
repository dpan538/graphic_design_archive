# D2 — semantics and reconciliation review

- Queue: Phase 2B D2, read-only semantics/reconciliation review
- Reviewer: D2
- Scope: candidate-to-v49 migration meaning, not importer implementation
- Result: `PASS_WITH_IMPLEMENTATION_ORACLES`
- Database activity: none — no PostgreSQL client, cluster, migration, or fixture was started
- Candidate JSON activity: none — this reviewer did not parse, copy, hash, or otherwise expand the 190,067,852-byte candidate payload
- Frozen-asset activity: none — no frozen asset, historical receipt, Phase 2A migration, role, function, or schema file was modified

## 1. Conclusion

The Phase 1C/1D/2A normative corpus has no semantic conflict that requires a
Phase 2A schema change before the Phase 2B rehearsal.  It deliberately permits
the following exact population state:

```text
15,923 operational archive objects
 7,995 explicit source_verified research-eligible objects
 2,971 explicit metadata_supported held objects
 4,957 missing-tier held objects
 7,928 total held objects
     0 rejected objects
     0 accepted semantic relations
     0 TRACE projection edges
     0 TRACE-eligible objects
     0 positive-rights-qualified visual bundles
     0 REMOTE_IMAGE decisions
```

Those zeros are intentional fail-closed outcomes, not missing migration data.
The importer must preserve the candidate rows, their raw literals, and their
reconciliation classifications without turning a legacy display projection,
Search row, SQLite fallback, URL, IIIF signal, or endpoint observation into a
canonical fact or permission.

## 2. Evidence reviewed

The review read the current architecture, logical model, migration plan, read
contract, acceptance gates, DDL decision pack, all four ADRs, the Phase 1C
authority/research package, the Phase 1D rights/machine package, the Phase 1D
joint gate, and the Phase 2A schema receipts/physical-schema documentation.
Particularly material sources were:

- `MIGRATION_V48_TO_V49.md` — sole-input, one-object-per-surface, tier,
  visual, graph, derived-product, and release boundaries.
- `DATA_MODEL_V49.md`, `docs/architecture/DDL_DECISION_PACK_V49.md`, and
  ADR 0004 — typed identity, orthogonal state, real-FK, corpus, visual, and
  machine-boundary rules.
- `docs/audits/v49-authority-research-delta/00_EXECUTIVE_RECEIPT.md`,
  `09_RESEARCH_CORPUS_POLICY.md`, and `12_TRACE_PROJECTION_DELTA.md` —
  measured Tier/TRACE authority outcomes.
- `docs/audits/v49-rights-machine/00_EXECUTIVE_RECEIPT.md`,
  `02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md`,
  `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`, and
  `10_NEGATIVE_TEST_SPEC.md` — visual occurrence identity and zero-rights
  delivery requirements.
- `database/JSON_MIGRATION_CONTRACT.md`, `database/PHYSICAL_SCHEMA.md`,
  `database/migrations/002_raw_core_provenance.sql`,
  `database/migrations/003_research_rights.sql`, and the Phase 2A receipts —
  available physical-model capability and immutable boundary.

### Historical manifest verification routing

The current-tree command below is *not* the correct Phase 1C verification
mechanism after authorized Phase 1D normative-document changes:

```text
shasum -a 256 -c docs/audits/v49-authority-research-delta/CHECKSUMS.sha256
```

It reports only `ACCEPTANCE_GATES.md`, `DATA_MODEL_V49.md`, and
`MIGRATION_V48_TO_V49.md` as changed; every Phase 1C package-local artifact
matches.  The Phase 1D joint receipt explicitly records this historical
baseline situation and gives the historical blob hashes.  The reusable
`database/scripts/verify_historical_audit.py` must therefore be invoked with
the Phase 1C expected base commit and the current implementation commit.  It
must not cause a re-signing or alteration of the sealed Phase 1C package.

Current-tree checksum results for the Phase 1D rights/machine, Phase 1D final,
and Phase 2A packages were all successful in this review.  The preceding
Phase 1C caveat is expected provenance routing, not a data-model conflict.

## 3. Authority matrix for Phase 2B

| Asset or product | Phase 2B role | May create canonical population rows? | Required result |
|---|---|---:|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | sole lexical and semantic population input | Yes | One deterministic staging surface and one operational object baseline per source row. |
| `data/prefreeze_candidate_v48.sqlite` | immutable `mode=ro&immutable=1` reconciliation | No | Record metrics/set comparisons only; no field, tier, or row backfill. |
| transfer manifest JSON/CSV | path/hash integrity evidence | No | Register in artifact ledger only. |
| TRACE manifest/catalog/shards | legacy-product reconciliation evidence | No | Record graph counts/lineage only; no graph fact, member, relation, or projection import. |
| Search index/product | derived-population reconciliation | No | Compute the fixed set relation only; Search-only IDs must have zero canonical inserts. |
| Phase 1C authority audit | policy and expected metrics | No | Bind receipts/policy hashes; do not synthesize evidence rows. |
| Phase 1D rights audit | visual-baseline reconciliation | No | Compare typed visual outcomes; do not add positive rights. |
| Phase 2A schema manifest | schema identity | No | Verify the fixed normalized schema hash before/after rehearsal. |

The ledger must have exactly one `population_input=true` row: the candidate
JSON.  Registration of the other four frozen files in
`raw.legacy_v48_artifact` is compatible with their reconciliation/integrity
roles; it is not permission to expand their contents into canonical rows.

## 4. Tier, corpus, and held-state rules

### 4.1 Exact mutually exclusive source-tier partition

The candidate field `trace.tier` governs the Phase 2B initial corpus outcome.
It is neither a generic publication state nor an assertion-acceptance state.

| Candidate condition | Rows | Operational-object result | Research disposition | Required reason |
|---|---:|---|---|---|
| exact `source_verified` | 7,995 | retain | eligible | `EXPLICIT_SOURCE_VERIFIED_TIER` |
| exact `metadata_supported` | 2,971 | retain | held | `METADATA_SUPPORTED_BELOW_STRICT_EVIDENCE_THRESHOLD` |
| tier key missing | 4,957 | retain | held | `MISSING_EXPLICIT_EVIDENCE_TIER` |
| nonblank unregistered tier, if encountered | 0 in frozen baseline | retain | held | `UNREGISTERED_EVIDENCE_TIER_FAIL_CLOSED` |
| reviewed rejection | 0 in frozen baseline | retain evidence/history | rejected | evidence-bearing decision only |

The importer must separately preserve the field-presence class and the exact
value.  `MISSING`, `NULL`, `EMPTY_STRING`, `EMPTY_ARRAY`, `EMPTY_OBJECT`, and
`PRESENT` cannot collapse to a database `NULL` without a raw field occurrence
that proves the original distinction.

Required arithmetic and state assertions are:

```text
7995 + 2971 + 4957 = 15923
2971 + 4957 = 7928
RESEARCH_ELIGIBLE_OBJECTS = 7995
HELD_OBJECTS = 7928
REJECTED_OBJECTS = 0
```

The stale candidate scalar `/meta/traceMetadataSupportedCount=2970` is a raw
aggregate observation.  It is not a 2,970-member data set and must not create
an invented one-row symmetric difference.  The three measurable candidate,
SQLite, and catalog member sets are each 2,971 and equal.

### 4.2 SQLite fallback is prohibited

SQLite's legacy builder reports 12,952 `source_verified` rows because it
normalized the 4,957 missing candidate tiers.  The Phase 2B mapping may record
that result in the derived reconciliation ledger, but it must never write it
to a canonical tier, corpus membership, assertion, or eligibility field.
`metadata_supported` is held, not rejected, and every held object remains an
operational object.

### 4.3 Physical-model fit

The existing model has the required separation:

- `raw.source_asset`, `raw.source_record`, `raw.field_literal`,
  `raw.migration_batch`, and `raw.legacy_surface_ledger` retain the input,
  row, literal, batch, and accounting dimensions;
- `core.entity` plus `core.archive_object` expresses exactly one conservative
  operational object identity per accounted surface;
- `research.corpus`, `research.corpus_version`, and
  `research.corpus_membership` represent release/version-specific membership;
- `research.missingness_snapshot` and `research.missingness_observation`
  retain the separate missingness baseline;
- `raw.fail_closed_delta` preserves a quarantined/held classification issue.

No schema count limit should be added.  The fixed numbers are verifier
baselines, not capacity constraints.

## 5. TRACE and legacy-graph zero-import rules

TRACE is a release/corpus projection, not a write channel for canonical
research facts.  Phase 2B may preserve Candidate JSON literals, separate array
item ordinals, opaque legacy edge-root crosswalks, and a fail-closed graph
classification.  It must not create semantic relation endpoints, accepted
claims, canonical semantic relations, object-relation memberships, or TRACE
projection edges from the v48 products.

| Legacy unit | Reconcile/report | Canonical import |
|---|---:|---:|
| full legacy graph edges | 255,695 | 0 |
| active object-edge memberships | 126,822 | 0 |
| TRACE shard rows | as manifest evidence | 0 |
| accepted semantic relations | 0 | 0 |
| TRACE projection edges | 0 | 0 |
| TRACE-eligible objects | 0 | 0 |

The 126,822 candidate edge IDs and 79,683 candidate edge-label occurrences
are independent arrays.  In 9,393 surfaces their lengths differ.  Hence all
edge-ID/label positional pairings are unsafe: retain each array and each
ordinal independently, label the condition `unsafe_pairing/held`, and create
zero pairs.  The current permitted legacy crosswalk is each surface's
`trace.objectNodeId`; it does not establish a semantic relation.

Relation labels may become proposed source-bound literals or workflow cases
only.  Unknown labels must have null family/epistemic route and cannot be
coerced into a default relation, including `medium_context/documented`.
Automatic influence inference remains zero.  The schema's
`research.relation_type`, `research.semantic_relation`,
`research.claim_revision`, `research.relation_claim`, and projection tables
must consequently receive no legacy graph import in this rehearsal.

## 6. Visual and rights reconciliation rules

### 6.1 Required visual baseline

| Unit | Required value | Migration meaning |
|---|---:|---|
| visual bundles | 15,923 | one per candidate surface in the visual ledger |
| reference-bearing bundles | 15,788 | typed source-occurrence references/bridges where structurally valid |
| `NO_VISUAL_REFERENCE` bundles | 135 | explicit typed disposition; **no empty reference row** |
| locator occurrences | 15,790 | per-occurrence identity; not unique URL count |
| distinct locator values | 15,788 | reconciliation observation only |
| unclassified visual references | 0 | required baseline closure |
| positive rights coverage | 0.0000% | legal and required fail-closed outcome |
| `REMOTE_IMAGE` decisions | 0 | no remote pixel exposure |
| public pixel locators | 0 | no release/API public locator created |

An external visual reference is a source-occurrence identity with natural key
`(source_asset_id, source_record_id, source_field_or_json_pointer,
occurrence_ordinal)`.  It is not a URL, provider object, digital
representation, archive object, health result, rights assessment, or
permission.  The same raw URL appearing twice is two locator occurrences;
normalization may be diagnostic but cannot deduplicate source identity.

For a v48 reference-bearing bundle, the only supported Phase 2B baseline is:

```text
RIGHTS_UNKNOWN
POLICY_UNKNOWN
UNMAPPED_PROVIDER
delivery fail-closed to LINK_ONLY or CITATION_ONLY
```

No synthetic permissive provider/provider-object should be invented merely to
satisfy a foreign key.  A missing provider crosswalk remains an explicit
`UNMAPPED_PROVIDER` hold.  Raw rights/license/credit wording may be recorded
as an observation/proposed literal only; it does not become a positive rights
assessment or provider-policy evaluation.

### 6.2 Five axes remain independent

The importer must not produce a compressed `rights_status`.  It must retain,
or explicitly leave unadjudicated, separate records/fields for:

1. rights evidence/assessment;
2. provider policy/evaluation;
3. project delivery decision;
4. endpoint health observation; and
5. takedown event/override.

The current migration must not probe endpoints or invent health.  URL
presence, HTTP success, IIIF, thumbnail availability, a source viewer, and
provider reputation are not authorization.  `RD-020`, `RD-021`, and `RD-999`
in the truth table establish the safe unknown cases; `RD-080` is the only
positive remote-image control and has no matching v48 baseline row.

### 6.3 Physical-model fit

Phase 2A already provides `rights.external_visual_reference`,
`rights.object_visual_reference`, `rights.visual_locator`, optional provider
crosswalk fields, `rights.rights_observation`, `rights.rights_assessment`,
`rights.provider_policy_version`, `rights.provider_policy_evaluation`,
`rights.delivery_assessment`, `rights.endpoint_health_observation`, and the
takedown tables.  The importer must use the real source/record/reference FKs,
the typed locator role, exact raw locator, and occurrence ordinal.  It must
not populate a public registry, public locator, or digital representation from
a third-party URL.

## 7. Mapping and raw-preservation oracles

The mapping registry must use one reviewed version (for example
`gda-json-c14n-v1` and `mapping-v1`) and contain every source pointer/pattern,
including raw-snapshot-only fields.  For every occurrence it must record:

```text
pointer/pattern, source type, input cardinality, target kind,
transform version, null/missing/array-order/duplicate/delimiter policies,
vocabulary mapping, invalid/unknown disposition, exposure class,
provenance target, round-trip query, and raw-snapshot-only flag
```

The extractor must reject duplicate JSON keys, NaN, Infinity, unsupported
types, invalid field shapes, duplicate surface identities, and unknown fields
without a registry disposition before it opens the canonical import
transaction.  It must use UTF-8, deterministic object-key ordering for the
semantic digest, original array order, no Unicode normalization, no identity
trim/case-fold, and no internal-whitespace rewrite.  The frozen full artifact
is lexical authority; per-surface digesting may use the documented semantic
canonicalization but must not pretend it rewrites the source bytes.

The following fields are initially raw-first unless the versioned mapping has
specific reviewed normalization evidence:

- title/display title, display date/number, creator, medium, object type,
  subjects, place/region, institution/collection, provider/source label and
  source URL;
- metadata tables/rows, citations, movement/tree/branch labels, dossiers,
  registration, compound-child, review, and publication literals; and
- all TRACE raw arrays and raw visual/provider/rights literals.

Structured arrays may preserve item ordinal and expand only where the source
structure itself plus an approved mapping supports the typed target (for
example the independently verified folder memberships).  Delimiters are never
syntax by default: the source contains semicolons in creator, medium,
objectType, subjects, place, and date literals.  No `split(';')`, trim/drop,
cross-array zip, or automatic deduplication is permitted.

Required outcome counters are:

```text
UNMAPPED_SOURCE_FIELDS=0
SILENTLY_DROPPED_FIELDS=0
SILENT_DELIMITER_SPLITS=0
CROSS_ARRAY_POSITIONAL_ZIPS=0
AUTOMATIC_DEDUPLICATION=0
UNEXPLAINED_MAPPING_DELTAS=0
```

## 8. Identity, deterministic replay, and atomicity oracles

Identity must be deterministic UUIDv5 from the Phase 1C/2A approved namespace
and the exact legacy surface key.  It may not depend on sequence allocation,
clock time, database order, a URL, title, provider label, or a randomly
generated UUID.  The migration surface ledger must retain source ordinal,
RFC 6901 JSON pointer, exact `surfaceId`, exact `sourceRecordId`, raw semantic
digest, archive-object UUID, raw-record UUID, trace-root legacy ID, exact tier
presence/value, research disposition/reason, import disposition, parse error,
and quarantine ID.

The safe transaction order is:

1. verify base commit, schema hash, frozen source hash, mapping hash, and
   extractor hash;
2. strict-parse and stage Candidate JSON exactly once;
3. replay the unmodified Phase 2A schema into a fresh disposable database;
4. register the one candidate source artifact and create one matching batch;
5. write raw/source/ledger/core/corpus/visual baseline rows in one controlled
   transaction;
6. run deferred constraints, complete mapping and parity checks before commit;
7. calculate the deterministic count vector, stable-key set hash, and content
   hash after commit.

There is no `ON CONFLICT DO NOTHING`, per-row commit, failure skipping, or
post-error continuation.  Same batch identity plus identical bindings returns
a deterministic no-op/receipt; the same batch token plus a different source,
mapping, schema, extractor, or implementation binding must fail.

Failure injection must leave zero committed batch/canonical rows, zero partial
residue, no pointer advance, and no sealed release for source/schema mismatch,
post-staging failure, mid-object failure, post-corpus failure, post-locator
failure, forced parity failure, duplicate/missing/extra surface, unmapped
field/type, and batch-token/mapping-hash mismatch.

## 9. Public-boundary review

The final rehearsal must verify two distinct things:

1. `gda_v49_phase2a_api_reader` has only the approved `api_v1` positive
   allowlist and cannot `SELECT` raw/core/rights/workflow/release base tables
   or perform any write; and
2. a controlled, rollback-only release/public-view fixture demonstrates that
   objects with no visual reference remain visible while raw/internal/held
   locators and every pixel/thumbnail/image-service locator are structurally
   absent.

The second point needs a deliberately scoped test fixture because
`api_v1.current_object` is intentionally a *sealed-current* view and the
Phase 2B final state must leave no sealed rehearsal release or current-pointer
advance.  A transaction-scoped fixture that is rolled back is consistent with
the Phase 2A test strategy and the requested final values
`REHEARSAL_RELEASE_SEALED=false` and
`REHEARSAL_CURRENT_POINTER_ADVANCED=false`.  Do not weaken the view to expose
mutable migration rows solely to satisfy the test.

The public fixture must cover at minimum:

- a `NO_VISUAL_REFERENCE` object yielding normal metadata;
- an object held outside the strict research corpus;
- a zero-positive-rights visual state with no public pixel locator;
- zero accepted TRACE relations without query failure;
- denied `api_reader` raw/internal/held locator access and all DML; and
- explicit research-only/missing-registry behavior, not an empty/error object.

No release seal, current-pointer advancement, API endpoint, or frontend work
is authorized as a persistent Phase 2B outcome.

## 10. Required reconciliation receipt values

The implementation must produce or independently recompute these values
without using derived sources to repair data:

```text
CANONICAL_POPULATION_INPUT_ARTIFACTS=1
LEGACY_INPUT_SURFACES=15923
STAGED_SURFACES=15923
ACCOUNTED_SURFACES=15923
UNACCOUNTED_SURFACES=0
OPERATIONAL_ARCHIVE_OBJECTS=15923
RAW_SOURCE_RECORDS=15923
OBJECT_SOURCE_SEED_LINKS=15923

SEARCH_IDS=8636
CANONICAL_IDS=15923
INTERSECTION=2585
SEARCH_ONLY=6051
CANONICAL_ONLY=13338
UNION=21974
SEARCH_ONLY_CANONICAL_INSERTS=0

LEGACY_GRAPH_EDGES_RECONCILED=255695
LEGACY_GRAPH_EDGES_IMPORTED=0
LEGACY_MEMBERSHIPS_RECONCILED=126822
LEGACY_ACTIVE_MEMBERSHIPS_IMPORTED=0
TRACE_SHARD_ROWS_IMPORTED=0
TRACE_IMPORTED_CANONICAL_ROWS=0
ACCEPTED_SEMANTIC_RELATIONS=0
TRACE_PROJECTION_EDGES=0
TRACE_ELIGIBLE_OBJECTS=0
UNKNOWN_RELATION_COERCIONS=0
AUTOMATIC_INFLUENCE_INFERENCE=0

VISUAL_BUNDLES=15923
BUNDLES_WITH_REFERENCE=15788
BUNDLES_WITHOUT_REFERENCE=135
LOCATOR_OCCURRENCES=15790
UNCLASSIFIED_VISUAL_REFERENCE=0
POSITIVE_RIGHTS_COVERAGE=0.0000%
REMOTE_IMAGE_DECISIONS=0
PUBLIC_PIXEL_LOCATORS=0

SQLITE_BACKFILLED_ROWS=0
SQLITE_BACKFILLED_FIELDS=0
SQLITE_CANONICAL_WRITES=0
SEARCH_IMPORTED_ROWS=0
ATLAS_CATALOG_ROWS_IMPORTED=0
RAW_AUDIT_IMPORTED_EVIDENCE_ROWS=0
RIGHTS_AUDIT_PERMISSION_UPGRADES=0
```

## 11. Handoff

There is no decision-level blocker for the Phase 2B importer.  The open work
is implementation and verification: strict candidate extraction, complete
mapping registry, transactional load, deterministic two-database replay,
failure injection, access checks, and receipts.  It must not mutate the
Phase 2A schema or turn a known hold into a canonical fact.

## 12. Commands and exit state

Read-only commands executed by this reviewer included `git status`,
`git rev-parse`, `rg --files`, `rg -n`, `sed -n`, `wc -l`, and checksum checks.
No process was left running.  No PostgreSQL, Python/Node extractor, SQLite,
network, browser, Next, TypeScript, npm, or frontend command was executed.

```text
D2_REVIEW_STATUS=PASS_WITH_IMPLEMENTATION_ORACLES
D2_SEMANTIC_CONFLICTS=0
D2_SCHEMA_CHANGE_REQUESTS=0
D2_DATABASE_CONNECTIONS=0
D2_CANDIDATE_FULL_PARSE_COUNT=0
D2_TASK_OWNED_PIDS=0
```

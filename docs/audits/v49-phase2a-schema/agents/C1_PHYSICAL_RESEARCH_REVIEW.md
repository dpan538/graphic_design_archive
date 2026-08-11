# C1 — Physical schema and research semantics review

- Phase: v49 Phase 2A
- Reviewer role: independent, read-only physical/research model reviewer
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Reviewed starting HEAD: `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`
- Result: **PASS — no normative conflict; physical mapping may proceed with the mandatory oracles below**
- SQL/database implementation performed by C1: **none**

## Scope

C1 reviewed the physical mapping boundary for:

- ingest and migration control;
- `raw`, `core`, and `provenance` identity and foreign keys;
- research corpus, membership, missingness, and coverage snapshots;
- claimant-bound claims, semantic relations, evidence, and curator decisions;
- TRACE node/membership/projection separation;
- natural keys, delete policy, indexes, and deferred cross-table validation;
- preservation of the locked `15,923 / 7,995 / 7,928 / 0 accepted TRACE` baseline without encoding those numbers as capacity constraints.

Rights/delivery truth, roles/grants, seal/CAS implementation, and executable PostgreSQL tests have separate Phase 2A owners. C1 read those decisions where they constrain research/release FKs, but did not implement or edit them.

## Assets read completely

### Normative corpus

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- all four files under `docs/adr/`

### Phase 1C authority/research package

C1 read all 25 files under `docs/audits/v49-authority-research-delta/`, including every A1–A7 receipt, both manifests/checksum material, all JSON contracts, and every row of the TSV ledgers. The large ledgers were fully byte-read and structurally parsed rather than sampled:

- `06_RAW_SOURCE_EVIDENCE_DISPOSITION.tsv`: 1,599 data rows, 16 columns;
- `10_CORPUS_MEMBERSHIP_BASELINE.tsv`: 15,923 data rows, 19 columns;
- every JSON file parsed successfully.

### Phase 1D rights/machine and final packages

C1 read all 22 files under `docs/audits/v49-rights-machine/`, including B1–B7, the 20-rule delivery truth table, the visual identity/cardinality model, dual-release specification, machine exposure contract, stable-ID policy, and negative oracle. C1 also read all four files under `docs/audits/v49-phase1d-final/`.

The current Phase 1D rights package checksum verification passed in full. The final package checksum verification passed in full. The three current-tree Phase 1C normative checksum differences are the already-authorized Phase 1D evolution of `ACCEPTANCE_GATES.md`, `DATA_MODEL_V49.md`, and `MIGRATION_V48_TO_V49.md`; the joint receipt verifies their Phase 1C blobs at commit `967cbe3`. This is a verifier-orchestration concern already assigned to Phase 2A, not a physical-model conflict.

### Existing database/SQL conventions

C1 byte-read every legacy `db/*.sql` file and inspected its DDL/FK/JSONB/polymorphic-target patterns. That chain remains an excluded historical prototype, not a v49 migration prefix. In particular it contains unconstrained `target_type + target_id`, target-table text, broad JSONB state, public-schema read models, destructive/cascading behavior, and seed data that cannot satisfy the v49 subtype, evidence, release, or privilege invariants.

## Evidence commands

Read-only command families used:

```text
git status --short
git rev-parse HEAD
rg --files <normative, ADR, Phase 1C, Phase 1D and SQL scopes>
wc -lc <review scopes>
sed -n <bounded complete document ranges>
shasum -a 256 -c docs/audits/v49-rights-machine/CHECKSUMS.sha256
shasum -a 256 -c docs/audits/v49-phase1d-final/CHECKSUMS.sha256
python3 <stdlib-only complete byte/UTF-8/JSON/TSV structural reader>
rg -n <P0/P1/P2, conflict, state, target, FK and delete-policy terms>
shasum -a 256 db/*.sql
```

No command connected to PostgreSQL or SQLite, opened port 5432, imported data, or wrote a frozen asset.

## Locked evidence translated to physical rules

| Evidence unit | Locked value | Required physical consequence |
|---|---:|---|
| Operational input surfaces | 15,923 | Later migration ledger accounts one source occurrence per row and may create one conservative object per row; DDL contains no `15923` check or quota. |
| Research eligible | 7,995 | Eligibility is an explicit, versioned corpus-membership disposition; no object/table default makes a row eligible. |
| Held research objects | 7,928 | Held is preserved as workflow/corpus disposition, never an acceptance-state value and never delete-on-cleanup. |
| Rejected objects | 0 | Zero is legal; schema supports evidence-bearing rejection without requiring it. |
| Accepted/TRACE-eligible relations | 0 | Zero accepted semantic relations and zero TRACE projection edges must validate and seal successfully. |
| Legacy projection edges | 255,695 | Reconciliation/lineage only; no migration or FK path may promote them into `research.semantic_relation`. |
| Legacy memberships | 126,822 | Separate projection-membership unit; never relation, claim, or evidence count. |
| Unclassified graph/raw facts | 0 / 0 | Closed disposition registries are required; unknown remains held and creates no canonical relation. |
| Positive visual rights | 0.0000% | Zero positive delivery is legal and cannot affect research-object or release existence. |

## Recommended physical mapping

### 1. Shared conventions

1. Use versioned plain PostgreSQL SQL against a fresh namespace. Do not source, rename, or wrap the legacy `db/*.sql` chain.
2. Use `uuid` as the stable domain identifier. Deterministic v48 UUIDv5 values are supplied and verified by the later migration; do not make an extension or database-generated UUIDv5 algorithm part of source authority.
3. Use lowercase-hex SHA-256 domains and byte-length checks. Raw SHA plus byte length establishes lexical identity; parsed `jsonb` remains a non-authoritative projection.
4. Use explicit enums or closed registry tables for lifecycle/state vocabularies. No permissive default may grant acceptance, research eligibility, publication, or delivery.
5. Canonical parent FKs use explicit `ON DELETE RESTRICT` or equivalent non-cascading `NO ACTION`. PostgreSQL does not auto-index child FKs, so each join direction needed for integrity/review must have an index.
6. Cross-table completeness rules must be `DEFERRABLE INITIALLY DEFERRED` constraint triggers, exercised by `SET CONSTRAINTS ALL IMMEDIATE`. A `CHECK` constraint cannot safely inspect sibling subtype/evidence tables.

### 2. Ingest and migration control

Minimum typed records:

| Record | Natural key / invariant |
|---|---|
| `workflow.migration_batch` / `workflow.import_run` | immutable batch ID; unique idempotency key; mapping/parser versions and input artifact hash are explicit |
| `raw.source_artifact` | exact SHA-256 + byte length identity; authority role is closed (`migration_input`, `reconciliation`, `integrity_evidence`, future governed source) |
| `raw.source_record` | `(source_artifact_id, record_ordinal)`; provider keys and record fingerprints are attributes, not global keys |
| `raw.field_literal` | `(source_record_id, field_or_json_pointer, occurrence_ordinal)` with exact literal and optional byte/character span |
| legacy surface ledger | unique batch/source ordinal, unique batch `surface_id`, explicit legacy `sourceRecordId`, raw row fingerprint, import disposition, and failure/hold reason |
| mapping version | immutable mapping ID/version/hash; no silent delimiter policy |
| fail-closed delta | exact batch/row/field, expected/actual classification, reason, disposition and review case; append-only |

Important duplicate rule: identical raw record bytes/fingerprints can be legitimate distinct occurrences and therefore must not be globally deduplicated. Uniqueness belongs to occurrence identity, registered legacy identity, artifact byte identity, or another explicitly declared natural key. A negative test for a duplicate “fingerprint” must name which of those keys it violates.

`jsonb` is allowed for the validated parsed projection and manifest/diagnostic payload. It must not replace the surface ledger, field literals, dispositions, typed joins, or delta records. Missing, null, blank, empty array, and empty object remain distinct.

### 3. Core entity and identity

Use a closed `core.entity(entity_id, entity_kind, lifecycle_state, ...)` supertype and one PK/FK subtype row in exactly one of:

```text
core.archive_object
core.agent
core.place
core.concept
core.collection
core.temporal_extent
```

Mandatory controls:

- each subtype PK is also a real FK to `core.entity(entity_id)`;
- a deferred constraint verifies exactly one subtype and that it matches `entity_kind`;
- subtype parents and referenced archive objects cannot be deleted through cascading joins;
- semantically specific joins target the subtype table, not merely `core.entity`;
- deliberately multi-kind targets use a real `core.entity` FK plus an allowed-kind registry rule;
- no generic `(target_type, target_id)` or target table name exists.

`core.object_surface_identifier` is a durable typed crosswalk, not the object PK. It must express exactly one effective primary/alias object resolution or one explicit merged/split/withdrawn/unresolved terminal state. Split successors belong in a typed N:M child table; the old ID may not silently choose one successor. Effective resolution history is append-only and release-projected.

Legacy crosswalks should be type-specific (`surface → archive_object`, source record, TRACE node, TRACE edge projection, folder). A generic namespace registry may name a namespace, but its target must never be an unconstrained UUID/text pair.

Duplicate/same-work/edition/version findings need a typed object-to-object candidate or evidence-bearing relation with two archive-object FKs, directed/symmetric semantics declared by a registered predicate, and workflow review. They must not mutate the one-row-per-v48-surface baseline during import.

### 4. Provenance, assertions, assignments, and evidence

The physical graph must preserve these independent identities:

```text
source artifact/version/record
  -> exact field literal
  -> source-bound assertion
  -> shareable evidence item
  -> typed canonical assignment or claimant-bound research claim
  -> append-only review decision
```

Required structures and constraints:

- `provenance.object_source_record` is N:M with unique `(archive_object_id, source_record_id, source_role)`.
- Source versions and evidence revisions supersede prior rows; they do not overwrite historical evidence.
- `provenance.assertion` has one registered assertion predicate, exactly one closed typed subject subtype, and exactly one closed typed value subtype.
- An unknown relation label is **not** a sentinel/default `research.relation_type`. Preserve it through a registered provenance predicate such as “source relation-label literal”, an exact raw-literal value, and `workflow.relation_type_review_queue`. That assertion describes the source literal; it does not type a semantic relation.
- `provenance.canonical_assignment` has exactly one approved subtype. Adding a subtype requires a migration and an updated deferred exclusivity check.
- `assertion_evidence`, `assignment_assertion`, and `decision_evidence` are explicit N:M bridges with closed stance/support roles and uniqueness on the documented bridge natural keys.
- Accepted assertions require qualifying supporting evidence; accepted assignments require accepted assertion support or an evidence-bearing effective curator decision.

Evidence identity is the documented source-bound tuple:

```text
(source_artifact_id, source_record_id, locator_scheme, locator_value,
 byte_or_character_span, content_sha256)
```

Nullable components are a PostgreSQL trap: ordinary unique constraints treat nulls as distinct. Use `UNIQUE NULLS NOT DISTINCT` when the selected PostgreSQL version supports it, or a semantically safe equivalent, so the exact same evidence occurrence cannot be duplicated. Do not deduplicate by URL, normalized text, or content hash alone.

Raw/internal locators remain in inaccessible canonical/provenance tables. Public locators are copied by positive allowlist into sealed release projections; `api_reader` must never gain base-table access.

### 5. Research corpus and missingness

Minimum typed records:

```text
research.corpus
research.corpus_version
research.corpus_membership
research.missingness_snapshot / missingness_observation
research.coverage_snapshot
release.research_corpus_projection / release membership projection
```

Recommended invariants:

- corpus identity is stable; each version is immutable and unique on corpus/version or policy hash;
- one `(corpus_version_id, archive_object_id)` row records inclusion, exclusion, held, or rejected disposition with reason/evidence/actor/run; the state is not inferred from object existence;
- 7,995/7,928 are later migration results, not defaults or DDL checks;
- missingness and coverage identify population frame, denominator, unit, method/run, evidence confidence, input release/snapshot hash and policy version;
- source concentration remains P1 until a governed provider/source-family registry exists; no URL-host/prefix inference is encoded as canonical truth;
- release membership is a copied immutable row set and cannot query mutable corpus membership after candidate closure.

### 6. Claims and semantic relations

Claims and relations are not canonical-assignment subtypes and are not TRACE edges.

`research.claim` needs stable identity plus append-only revision/supersession, claimant FK, preserved wording/structured proposition, one active epistemic class, workflow/acceptance state, and typed temporal/spatial qualifiers. Claim evidence is N:M. A computed-association claim additionally requires a complete `research.analysis_run`; a causal/influence claim additionally requires claimant, wording, source/citation, exact locator, scope/qualification, competing-claim handling and heightened review.

Use `research.relation_endpoint` with a closed exactly-one typed endpoint family. The initial subtype points to `core.entity` with a real FK. The endpoint-entity subtype must also be unique on its target entity; otherwise duplicate endpoint wrapper rows could bypass the semantic relation natural key.

The directed semantic-relation natural key is:

```text
(subject_endpoint_id, relation_type_id, object_endpoint_id)
```

`research.relation_type` is the only semantic predicate registry. An accepted semantic relation must pass one deferred validation that checks, at minimum:

1. the relation type exists and is active;
2. endpoint kinds satisfy the relation type's domain/range rule;
3. there is an accepted supporting claim with qualifying evidence **or** an effective evidence-bearing curator decision, as allowed by the normative model;
4. class-specific evidence requirements are met;
5. no legacy-projection-only flag/source is being promoted;
6. its acceptance/review decision is effective and not superseded.

Proposed rows may be incomplete. Unknown/unmapped labels remain raw/provenance + workflow held and create no `semantic_relation` row. There is no fallback family, relation type, or epistemic class.

### 7. TRACE and release projection

Canonical/research working identities remain separate:

- `research.trace_node` is independent; legacy ID/canonical key/label/tree are descriptive/crosswalk attributes;
- `research.object_trace_node` is unique on `(archive_object_id, trace_node_id, role)`, and root-node uniqueness is separately enforced;
- `research.object_relation_membership` is unique on `(archive_object_id, semantic_relation_id, membership_role)`;
- tree, branch, placement, and membership rows have typed FKs and explicit order/role attributes.

Release projection must use copied, release-pinned rows. Recommended composite FK chain:

```text
release.trace_projection_edge
  -> (research_release_id, corpus_version_id, copied subject trace node)
  -> (research_release_id, copied semantic relation)
  -> (research_release_id, corpus_version_id, copied object trace node)

release.object_relation_membership_projection
  -> (research_release_id, copied archive object)
  -> (research_release_id, copied semantic relation)
```

The projection natural key remains the decision-pack key including release, corpus, subject node, semantic relation, object node, and projection role. Tree/branch placement is an N:M child. Sealed count queries read only these copied tables.

Legacy projection lineage belongs in a dedicated append-only reconciliation/lineage record. It may store legacy node/edge IDs and classification, but it must have no ordinary update or reverse-write path into `research.semantic_relation`. The 255,695 legacy edges are not Phase 2A fixtures and must not be imported.

An empty research release with zero accepted semantic relations and zero TRACE edges is valid. Validation may require a consistent empty copied set and passing receipts; it must not require `count(*) > 0`. The same principle applies to zero positive visual rights.

## Index and delete-policy recommendations

| Area | Required indexes beyond PKs/unique constraints | Delete policy |
|---|---|---|
| raw/import | artifact SHA/length; record artifact/ordinal; legacy surface/source IDs; batch disposition/reason; non-unique fingerprint lookup | source artifacts/records/literals restricted; corrections append |
| core identity | public/legacy identifier; entity kind/lifecycle; crosswalk current resolution; successor reverse lookup | entity/subtypes/object parents restricted |
| provenance | object-source both directions; assertion predicate/status; subject/value FKs; evidence source/fingerprint; each evidence bridge reverse direction | source/evidence/assertion parents restricted |
| workflow | open queue by kind/state/priority; effective decision by case; held/rejected reason; relation-label queue | append/supersede; no cascade from reviewed subject |
| corpus | version policy hash; membership `(corpus_version, disposition, archive_object)` and reverse object lookup; missingness reason/frame | corpus/version/member parents restricted; sealed copy immutable |
| claim/relation | claim epistemic/status/claimant; relation subject/type/status and object/type/status; relation-claim reverse lookup; analysis input hash | claims/types/endpoints/relations restricted |
| TRACE/release | object-node both directions; object-relation membership; release/corpus projection keys; placement tree/branch; release state | canonical rows restricted; candidate/sealed copied rows mutation-guarded |

No partitioning, PostGIS, graph database, full-text architecture, broad GIN, or visualization materialization is justified before representative migration/query plans.

## Deferred-validation matrix

| Validation | Timing | Failure oracle |
|---|---|---|
| `core.entity` exactly one matching subtype | deferred to transaction end | zero, multiple, or wrong-kind subtype fails |
| assertion exactly one subject and one value subtype | deferred | zero/multiple typed rows fail |
| canonical assignment exactly one approved subtype | deferred | unknown/missing/multiple subtype fails |
| relation endpoint exactly one approved subtype | deferred | arbitrary/string target or duplicate target wrapper fails |
| accepted assertion/assignment evidence | deferred | accepted without qualifying evidence/decision fails |
| accepted claim evidence/profile | deferred | missing evidence; incomplete computed/causal profile fails |
| accepted semantic relation | deferred | unknown/inactive type, invalid endpoint kinds, missing support/review or legacy projection promotion fails |
| candidate/validated/sealed copied-set immutability | state transition and child mutation trigger | post-closure row mutation fails |
| release TRACE eligibility | candidate validation | unknown/nonaccepted relation or claim fails; empty set passes |

## Adversarial tests recommended to C2

### Identity and FK

- orphan source record, field literal, object/source bridge, evidence bridge, claim, relation endpoint and projection row fail;
- entity with zero, two, or kind-mismatched subtype rows fails when constraints are forced;
- arbitrary string target cannot be represented;
- duplicate effective legacy surface identity fails, while two distinct raw occurrences with equal content remain preservable;
- duplicate source-bound evidence identity fails even when optional locator/span fields are null;
- deletion of an archive object, source record, evidence item, claim, relation type or semantic relation with dependants fails.

### Research and relation

- unknown relation literal can be stored and queued without any semantic relation row;
- unknown or inactive relation type cannot be accepted;
- accepted assertion, claim, assignment or semantic relation without its qualifying evidence/review path fails at `SET CONSTRAINTS ALL IMMEDIATE`;
- computed association without analysis-run provenance fails acceptance;
- causal/influence claim missing claimant/wording/source/locator/qualification/heightened review fails;
- the database has no automatic influence-inference trigger/function/path;
- held/rejected corpus rows remain after release construction and are not promoted by defaults;
- zero accepted relations and zero TRACE edges pass candidate validation/seal.

### Projection isolation

- legacy projection lineage cannot be updated into an accepted relation;
- TRACE/Search release roles have no canonical insert/update privilege;
- a projection edge without same-release copied nodes/relation/corpus fails its composite FK;
- a sealed projection remains unchanged after mutable canonical rows are edited through an authorized test owner path;
- counts distinguish projection edges, relation memberships, semantic relations, and claims.

## Findings and priority

### P0 implementation oracles — mandatory before Phase 2A PASS

| ID | Finding / risk | Required closure |
|---|---|---|
| C1-P0-01 | Cross-table exactly-one and evidence requirements cannot be expressed by ordinary checks. | Deferred constraint triggers exist for every closed subtype/evidence family and negative tests force them immediate. |
| C1-P0-02 | A duplicate `relation_endpoint` wrapper could defeat relation natural-key uniqueness. | Initial entity endpoint subtype is unique by target entity; relation key remains directed and non-bypassable. |
| C1-P0-03 | A sentinel/default relation type would silently convert unknown labels. | Unknown literals use provenance + workflow hold only; accepted semantic relation count remains zero in the empty baseline. |
| C1-P0-04 | Nullable evidence identity can evade ordinary unique semantics. | Exact source-bound evidence identity uses null-safe uniqueness and has a duplicate-negative test. |
| C1-P0-05 | A sealed TRACE projection could drift through live canonical joins. | Candidate/sealed projections are copied, composite release-pinned FK rows; post-seal canonical edits cannot change them. |
| C1-P0-06 | Legacy edges or derived Search/TRACE could become a backdoor canonical source. | Legacy lineage is isolated and roles/functions expose no derived-to-canonical write path. No legacy graph rows are loaded in Phase 2A. |
| C1-P0-07 | “Non-empty graph” validation would falsify the locked baseline. | Zero accepted relations/TRACE edges and zero positive rights are explicit passing fixtures. |

### P1 retained holds — not physical-schema blockers

| ID | Evidence | Required later action |
|---|---|---|
| C1-P1-01 | No authoritative v48 edge-ID/predicate/endpoints/evidence mapping; all current graph promotion stays zero. | Governed future research ingest/analysis, not schema weakening. |
| C1-P1-02 | 6,004 computed legacy edges have no governed analysis run; 32,137 edges use 19 held labels. | Preserve lineage/holds; do not seed accepted relations. |
| C1-P1-03 | Three legacy evidence observations lack an approved locator-only evidence profile. | Keep held until a versioned evidence profile is reviewed. |
| C1-P1-04 | Provider/source-family concentration is unmeasured without guessing. | Populate a governed source/provider registry in a later migration/research-quality phase. |
| C1-P1-05 | Historical Phase 1C wrappers pin three old normative blobs. | Use the new baseline-aware verifier runner; do not alter the historical receipt. |

### P2 deferred engineering choices

- partitioning and specialized indexes await representative data and query plans;
- backup/restore, performance workloads, OpenAPI/JSON-LD/DCAT and frontend repository integration remain later gates;
- historical v47 byte replay and LFS recovery are preservation work, not v49 migration authority.

## Conflict conclusion

```text
NORMATIVE_IDENTITY_CONFLICT=0
NORMATIVE_CARDINALITY_CONFLICT=0
NORMATIVE_STATE_CONFLICT=0
NORMATIVE_RESEARCH_AUTHORITY_CONFLICT=0
PHYSICAL_MAPPING_BLOCKER=0
```

The known holds are fully typed and fail closed. They preserve unsupported evidence and deliberately keep research/TRACE promotion at zero; they do not require a policy guess. C1 therefore finds no reason to stop Phase 2A before physical implementation.

## Actions explicitly not performed

- no SQL or migration file created, edited, reviewed by execution, staged, or committed;
- no PostgreSQL cluster, server, socket, port, database, role, `psql`, `initdb`, `pg_ctl`, schema replay, or system 5432 connection;
- no v48 JSON/SQLite/TRACE/Search import, regeneration, export, or mutation;
- no frontend, package, Next, TypeScript, browser, Docker, HTTP/image, CI, deployment, main-worktree, PR, merge, or push action;
- no legacy `db/*.sql` script executed;
- no agent task register modified.

All C1 shell sessions returned terminal states. C1 started no background task or database process.

```text
C1_STATUS=PASS
C1_FILES_WRITTEN=docs/audits/v49-phase2a-schema/agents/C1_PHYSICAL_RESEARCH_REVIEW.md
C1_SQL_FILES_MODIFIED=0
C1_DATABASE_CONNECTIONS=0
C1_TASK_OWNED_RESIDUAL_PROCESSES=0
```

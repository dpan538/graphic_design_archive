# v49 canonical data model

- Status: Proposed logical model accepted by the architecture checkpoint
- Physical PostgreSQL migrations: not implemented
- Source baseline: frozen v48 candidate at `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Normative pre-DDL decisions: `docs/architecture/DDL_DECISION_PACK_V49.md`

## Modeling rules

1. Canonical, queryable entities and relationships use typed tables and foreign keys.
2. `core.entity` and its closed subtypes use immutable UUIDs. Public `surface_id` values live in a typed identifier/crosswalk relation and are not object primary keys.
3. A source literal is never destroyed by normalization. Parsed values point back to an assertion and exact source field/path/span.
4. Typed assignments carry role, ordinal, confidence and validity when those semantics exist; workflow progress remains in `workflow` and supporting assertions use explicit bridges.
5. Raw bytes/length/SHA-256 are lexical authority. JSONB is a versioned parsed projection or opaque non-authoritative extension; it cannot certify source bytes or substitute for searchable entities, memberships, rights, gates, or relations.
6. Accepted rows are append-corrected or versioned with decisions; destructive history rewriting is prohibited.
7. Release projections contain stable DTO fields and do not expose canonical table layout.
8. `active`, `review`, and `auxiliary` are release publication layers. Acceptance and metric-specific count eligibility remain separate axes.

## Shared conventions

- Timestamps are `timestamptz` in UTC and serialize as RFC 3339.
- Hashes are lowercase SHA-256 hex with a domain constraint.
- Public IDs are case-sensitive text and immutable after publication.
- Confidence is a bounded numeric value plus a named evidence tier; neither silently implies acceptance.
- Soft labels from providers are literals/assertions until mapped to registered canonical IDs.
- Each import/transformation records software/query-pack version and deterministic input hashes.

## Identity model

`core.entity` is a closed supertype with internal immutable UUID `entity_id` and `entity_kind`. `core.archive_object`, `core.agent`, `core.place`, `core.concept`, `core.collection`, and `core.temporal_extent` each use that UUID as both PK and FK. A deferred invariant requires exactly one matching subtype row.

Semantically specific relationships use an FK to the required subtype. Deliberately multi-kind entity relationships use `target_entity_id` with a real FK to `core.entity` and an allowed-kind rule from the registered predicate. Non-entity targets use typed bridges. Canonical `target_type + target_id` is prohibited.

The v48 seed creates one deterministic UUIDv5 archive object per canonical JSON `surfaceId`; it performs no identity deduplication. `surface_id` is a durable public/legacy route identifier that resolves to one current object or one explicit merged/split/withdrawn/unresolved state. Merge and split history is append-only and curator-decided.

Raw source records, TRACE nodes, folders, evidence, representations, workflow cases, and releases have independent typed identities and are not entity subtypes.

## `raw`

The `raw` schema is append-only and preserves source evidence.

| Table | Purpose and key fields |
|---|---|
| `raw.source_artifact` | One immutable byte stream: `artifact_id`, provider, locator, media type, byte length, raw `sha256`, retrieval time, storage reference. The bytes/hash are lexical authority. |
| `raw.source_record` | One occurrence within an artifact, identified by `(source_artifact_id,record_ordinal)`; provider key/locator and parsed `payload jsonb` are non-unique projections. |
| `raw.capture_event` | Capture request/result metadata, HTTP status, access time, batch and software version. |
| `raw.field_literal` | Exact record field/path, original text/JSON scalar, optional byte/character span, ordinal. |
| `raw.legacy_v48_artifact` | Registers all five frozen assets with role. Only candidate JSON has role `migration_input`; SQLite is `reconciliation`; manifests are `integrity_evidence`. Bytes remain outside writable canonical tables. |

`raw` roles cannot update or delete accepted source rows. Corrections arrive as new artifacts/records linked by supersession metadata.

## `core`

The `core` schema owns normalized descriptive identity.

| Table | Purpose and key constraints |
|---|---|
| `core.entity` | Closed UUID supertype, entity kind and lifecycle. Exactly one matching subtype is required. |
| `core.archive_object` | Stable intellectual-object subtype identity, title policy and publication-neutral lifecycle. Source/surface IDs are not the PK. |
| `core.object_surface_identifier` | Durable `surface_id` → archive object or explicit terminal resolution; supports primary, alias, merge, split, withdrawal and redirect history. |
| `core.agent` | Person/organization/unknown-agent identity with preferred label and authority state. |
| `core.place` | Normalized place/region with type, parent, coordinates only when evidenced, and authority ID. |
| `core.concept` | Registered medium, object type, subject, movement, and classification concepts with scheme and concept kind. |
| `core.collection` | Collection/institution identity, not a free-text source name. |
| `core.temporal_extent` | Display literal plus optional start/end precision and uncertainty. |
| `core.object_agent_credit` | Object–agent join: role, ordinal, credited-as literal assertion, confidence, acceptance state. |
| `core.object_medium_assignment` | Object–medium concept join with ordinal, assertion, confidence, acceptance state. |
| `core.object_type_assignment` | Object–type concept join with ordinal, assertion, confidence, acceptance state. |
| `core.object_subject_assignment` | Object–subject concept join with ordinal, assertion, confidence, acceptance state. |
| `core.object_place_assignment` | Object–place join with role (`creation`, `publication`, `subject`, `collection`, `broad_region`), precision, assertion, confidence. |
| `core.object_collection_membership` | Object–collection join with role, source assertion, and validity. |
| `core.object_component` | Parent–child/compound object relation with type, ordinal, evidence, and acceptance state. |

No join is created solely because a delimiter appears in source text.

## `provenance`

The `provenance` schema explains where every accepted statement came from.

| Table | Purpose and key constraints |
|---|---|
| `provenance.source_document` | Document/source identity, canonical URL, provider, citation metadata, access history. |
| `provenance.object_source_record` | N:M object–raw-record assignment, unique on object, record and role. The v48 seed is 15,923 1:1 `seed_description` links. |
| `provenance.assertion` | Registered predicate plus exactly one row in a closed typed subject family and one row in a closed typed value family. |
| `provenance.assertion_entity_subject` | Assertion PK/FK plus subject FK to `core.entity`. |
| `provenance.assertion_source_record_subject` | Assertion PK/FK plus subject FK to `raw.source_record`. |
| `provenance.assertion_trace_node_subject` | Assertion PK/FK plus subject FK to `research.trace_node`. |
| `provenance.assertion_representation_subject` | Assertion PK/FK plus subject FK to `rights.digital_representation`. |
| `provenance.assertion_entity_value` | Assertion PK/FK plus `target_entity_id` FK to `core.entity`. |
| `provenance.assertion_literal_value` | Assertion PK/FK plus FK to the exact raw field literal. |
| `provenance.assertion_source_record_value` | Assertion PK/FK plus value FK to `raw.source_record`. |
| `provenance.assertion_trace_node_value` | Assertion PK/FK plus value FK to `research.trace_node`. |
| `provenance.canonical_assignment` | Closed identity/acceptance supertype for normalized joins and research relations; exactly one typed assignment subtype shares its PK/FK. |
| `provenance.evidence_item` | Shareable source-bound locator/span/content-hash identity; distinct from assertion and assignment. |
| `provenance.assertion_evidence` | N:M assertion/evidence join with stance and ordinal. |
| `provenance.assignment_assertion` | N:M assignment/assertion support join. |
| `provenance.transformation` | Parser/mapping rule ID and version, input/output assertion links, deterministic parameters, software hash. |
| `provenance.citation` | Citation/URL/locator with quoted span metadata where licensed. |
| `provenance.assertion_citation` | Assertion–citation join with role and ordinal. |
| `provenance.capture_branch` | Capture record–research branch join replacing delimiter-packed branch IDs. |
| `provenance.evidence_locator` | Page, field path, selector, byte/character span, or stable external locator. |

An accepted normalized join references at least one accepted assertion or an explicit curator decision whose evidence chain is queryable.

## `rights`

The `rights` schema separates object existence from representation display permission.

| Table | Purpose and key constraints |
|---|---|
| `rights.digital_representation` | Image/file identity, source URL, local asset reference, media type, dimensions, content hash. |
| `rights.object_representation` | Object–representation assignment with role, sequence, provenance and acceptance; release projection chooses publication layer separately. |
| `rights.rights_statement` | Registered rights URI/label, jurisdiction, license, credit, restrictions, evidence. |
| `rights.representation_rights` | Representation–statement join with effective dates and assertion. |
| `rights.display_policy` | Versioned policy decision: `unresolved`, `permitted`, `source_only`, `metadata_only`, or `denied`. |
| `rights.policy_evaluation` | Representation/object, policy version, decision, reason codes, reviewer/run, evidence. |

Unresolved or conflicting rights remain `unresolved`; release display behavior fails closed to metadata-only. Permission never inherits from a sibling representation.

## `research`

The `research` schema owns reviewed analytical structures, not raw provider labels.

| Table | Purpose and key constraints |
|---|---|
| `research.relation_type` | Unique registered predicate, family, status, evidence requirements, allowed statement, prohibited inference, registry version. |
| `research.trace_tree` | Research tree identity, label, description, publication state. |
| `research.trace_branch` | Tree branch with stable ID and ordered hierarchy. |
| `research.trace_node` | Independent typed node identity with non-unique canonical key, tree, label, evidence and optional FK to one core entity. |
| `research.object_trace_node` | Object–node typed join, unique on object, node and role; root node references at most one object. |
| `research.relation_edge` | Canonical assignment whose directed natural key is `(subject_trace_node_id,relation_type_id,object_trace_node_id)`; evidence/tree/branch/state are not key fields. |
| `research.relation_edge_placement` | N:M edge placement, unique on edge, tree and branch. |
| `research.object_relation_membership` | Separate assignment, unique on archive object, edge and membership role. |
| `research.object_tree_membership` | Object–tree/branch join replacing a single trace tree assumption. |
| `research.folder` | Curated folder identity, type, slug, label, narrative metadata. |
| `research.folder_membership` | Folder–object assignment, natural key `(folder_id,archive_object_id,membership_role)`; position is not identity. |
| `research.folder_relation` | Typed directed folder–folder relation with evidence. |
| `research.folder_authority_ref` | Folder–entity authority reference with `target_entity_id` FK and registered allowed entity kinds; never type plus free ID. |
| `research.object_classification` | Object–historical node/movement/other registered concept join. |
| `research.dossier` | Research dossier identity and status. |
| `research.dossier_folder` | Ordered dossier–folder join. |
| `research.dossier_page` | Ordered dossier–object/page join with role. |
| `research.dossier_appendix_reason` | Structured appendix reason rows. |
| `research.registration_card` | Registration card identity and source. |
| `research.registration_card_member` | Ordered card–page/object join. |

### Relation fail-closed constraints

`research.relation_edge.relation_type_id` is `NOT NULL` and references `research.relation_type`. A deferred constraint trigger rejects transition to `accepted` when the type is inactive/unpublished, the required evidence tier is absent, the stored family differs from the registry projection, or `historical_influence` lacks its stricter review requirements.

Raw labels that do not resolve are not inserted as accepted edges. They are recorded as assertions and routed to workflow review. There is no default relation type or default family.

## `workflow`

| Table | Purpose and key constraints |
|---|---|
| `workflow.import_run` | Input artifact hashes, parser/mapping versions, started/completed status, idempotency key. |
| `workflow.review_queue_item` | Generic queued or quarantined entity/assertion, reason code, priority, owner, state. |
| `workflow.relation_type_review_queue` | Unmapped raw predicate and occurrence context. Workflow is queued; no canonical edge, publication layer, or metric eligibility row exists until resolution. |
| `workflow.review_decision` | Append-only reviewer decision, rationale, evidence and supersession. |
| `workflow.review_case_assertion` | Typed case subject; mutually exclusive with assignment/other case-subject subtypes. |
| `workflow.review_case_assignment` | Typed case subject for one canonical assignment. |
| `workflow.decision_evidence` | N:M decision/evidence join; effective decisions require evidence. |
| `workflow.publication_gate` | Versioned gate definition and severity. |
| `workflow.gate_run` | Snapshot/release candidate, query/code hash, start/end, overall result. |
| `workflow.gate_result` | Gate result, expected/actual value, sample/evidence reference, status. |
| `workflow.promotion_attempt` | Candidate release, required receipt hashes, actor, outcome; never mutates sealed releases. |

Unknown relations, unresolved authority, rights conflicts, and reconciliation differences are represented as workflow state, not hidden as nulls or UI defaults.

## `release`

| Table | Purpose and key constraints |
|---|---|
| `release.release_version` | Unique release ID with forward state `draft → candidate → validated → sealed`, source snapshot identity and exact manifest hash committed at seal. |
| `release.source_lineage` | Release–raw artifact/hash/commit links. |
| `release.projection_set` | Migration set and projection query-pack hashes. |
| `release.count_snapshot` | Named exact count, scope/unit definition, query hash and value. |
| `release.asset` | Path, resource kind, schema, encoding, bytes, records, SHA-256, deterministic partition. |
| `release.manifest` | Canonical manifest bytes/hash and schema version. |
| `release.gate_receipt` | Required gate run/receipt hash and promotion decision. |
| `release.registry_snapshot` | Relation and rights policy registry hashes included by the release. |
| `release.current_pointer` | Mutable channel pointer updated only by CAS to an exact sealed release/manifest pair, with append-only history. |
| `release.*_projection` | Copied candidate/sealed rows keyed by release ID; never a live join to canonical tables. |

Sealed rows are protected by privileges and triggers from `UPDATE`/`DELETE`. A release projection may denormalize data for reads, but it is never canonical input to `core` or `research`.

## Orthogonal state model

| Axis | Values and owner |
|---|---|
| Workflow state | `queued`, `claimed`, `in_review`, `resolved`, `superseded` in `workflow`. |
| Acceptance state | `proposed`, `accepted`, `rejected`, `superseded` on assertions/assignments. `held` is not an acceptance state. |
| Rights decision | `unresolved`, `permitted`, `source_only`, `metadata_only`, `denied` in `rights`. |
| Publication layer | `active`, `review`, `auxiliary`, `excluded` in a release projection. |
| Count eligibility | Per `(release,metric,typed subject)` as eligible/ineligible plus reason; never one universal canonical boolean. |

No axis implies another. In particular, a workflow-queued unknown relation remains a proposed raw assertion and creates no canonical edge, publication row, or metric row.

## `api_v1`

`api_v1` contains release-scoped views or materialized views, not mutable domain tables:

- `api_v1.release_descriptor`
- `api_v1.archive_overview`
- `api_v1.folder_type_summary`
- `api_v1.folder_summary`
- `api_v1.folder_detail`
- `api_v1.folder_member`
- `api_v1.surface_summary`
- `api_v1.surface_detail`
- `api_v1.search_document`
- `api_v1.trace_atlas`
- `api_v1.trace_object_summary`
- `api_v1.trace_neighborhood`
- `api_v1.relation_type_definition`

Every row is keyed or partitioned by exact release ID. Runtime roles receive `SELECT` on these projections only. DTO validation occurs at the API/repository boundary.

## Multi-value text migration inventory

The counts below are read-only delimiter-signal counts from the frozen SQLite snapshot. They are not proof of separable values: semicolons also occur in names, date/place phrases, and physical-description punctuation. Automatic delimiter splitting is prohibited.

| Legacy field | Rows containing `;` | Canonical target |
|---|---:|---|
| `objects.creator` | 3,849 / 15,923 | `core.agent` + `core.object_agent_credit` |
| `objects.medium` | 10,791 / 15,923 | `core.concept` + `core.object_medium_assignment` |
| `objects.object_type` | 7,117 / 15,923 | `core.concept` + `core.object_type_assignment` |
| `objects.source_subjects` | 15,233 / 15,923 | `core.concept` + `core.object_subject_assignment` |
| `capture_records.branch_ids` | 9,934 / 11,413 | `research.trace_branch` + `provenance.capture_branch` |
| `capture_records.source_creator` | 2,280 / 11,413 | raw literal/assertion + agent credit joins |
| `capture_records.source_medium` | 6,563 / 11,413 | raw literal/assertion + medium joins |
| `capture_records.source_object_type` | 949 / 11,413 | raw literal/assertion + type joins |
| `capture_records.source_subjects` | 11,187 / 11,413 | raw literal/assertion + subject joins |
| `capture_records.source_collection` | 5 / 11,413 | raw literal/assertion + `core.object_collection_membership` |

For each reliable parsed value, migration records the source field/path/span, ordinal, role, confidence, assertion ID, parser/mapping version, and review state. If the parse is ambiguous, the literal remains an unresolved assertion and no entity or join is manufactured.

## Array/JSONB-to-join migration inventory

| v48/UI structure | v49 normalized target |
|---|---|
| `Folder.surfaceIds` and `Surface.folders` | `research.folder_membership` |
| `Folder.relatedFolderIds` | `research.folder_relation` |
| `Folder.authorityRefs.*Ids` | `research.folder_authority_ref` |
| `Surface.historicalNodeIds`, `movementIds` | `research.object_classification` |
| object `traceTreeId` / branch arrays | `research.object_tree_membership` and `provenance.capture_branch` |
| `Surface.images` | `rights.digital_representation` + `rights.object_representation` |
| nested `rights` object | registered `rights.rights_statement`, joins, and policy evaluation |
| `reviewGates` and `publicationGate` | `workflow.publication_gate`, `gate_run`, and `gate_result` |
| metadata/table rows with `citationIds[]` | `provenance.assertion` + `provenance.assertion_citation` |
| dossier `folderIds` and `pageSequence` | `research.dossier_folder` and `research.dossier_page` |
| dossier/appendix `reasons[]` | `research.dossier_appendix_reason` |
| registration card `memberPages[]` | `research.registration_card_member` |
| `compoundChildren[]` | `core.object_component` |
| Search `folderText`, `tableText`, combined body | derived `api_v1.search_document`; never canonical input |

The existing v48 `object_metadata_rows` table is already row-oriented and should import as assertions/ordered values rather than being repacked into JSONB.

## v48 reconciliation baseline

Migration must preserve and separately name these frozen metrics before any intentional v49 delta is accepted:

| Metric | Exact v48 value |
|---|---:|
| Active objects | 15,923 |
| Remaining to 20,000 target | 4,077 |
| TRACE nodes | 97,889 |
| Total graph edges | 255,695 |
| Active-object relation memberships | 126,822 |
| Medium/context memberships | 79,206 |
| Source/provenance memberships | 31,288 |
| Time/place memberships | 16,328 |
| Historical influence memberships | 0 |
| Active research trees | 30 |
| Source verified | 12,952 |
| Metadata supported | 2,971 |
| Review/authority hold objects | 4,425 |
| Auxiliary objects | 11 |
| Archive Search IDs | 8,636 |
| Canonical/TRACE ∩ Search | 2,585 |
| Search-only derived IDs | 6,051 |
| Canonical/TRACE-only IDs | 13,338 |
| Canonical/TRACE ∪ Search IDs | 21,974 |

`255,695` and `126,822` are different units and cannot share one label. The 8,636 Search rows are a derived legacy population, not an import cohort and not a v49 Search-row parity target. Exact file hashes and release asset counts are normative in `ACCEPTANCE_GATES.md`.

## Physical-design boundary

This logical model intentionally leaves extension choice, index strategy, partition size, UUID implementation, materialization schedule, and migration tooling to the implementation phase. Those choices require query plans and representative tests; they must not be smuggled into this architecture checkpoint as completed work.

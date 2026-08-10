# v49 Phase 1A: pre-DDL decision pack

- Status: Accepted architecture decisions; PostgreSQL DDL is not authorized by this document
- Date: 2026-08-10
- Baseline commit: `2a91c86bef7d23f05074187ffc53bd9f6a8f6213`
- Measurement authority: frozen v48 JSON; SQLite was used only for read-only reconciliation

## Purpose and boundary

This pack closes the P0 choices that would otherwise make PostgreSQL keys, foreign keys, state constraints, release sealing, or grants ambiguous. It contains no migration, verifier, import, fixture, API, adapter, frontend, or deployment implementation.

Measured v48 facts and declared v49 rules are deliberately separated. A measured 1:1 baseline does not claim that two source descriptions can never represent the same intellectual object. Conversely, a declared future N:M cardinality does not rewrite v48 history.

## 1. v48 artifact authority

The five frozen artifacts have distinct jobs:

| Artifact | Bytes | SHA-256 | Authority |
|---|---:|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | The only v48 migration input. Its raw bytes are lexical authority. |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | Reconciliation only. It may confirm counts/relationships but may never supply a missing canonical row or field. |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | Integrity and transfer evidence only. |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | Integrity and human-audit evidence only. |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | Integrity evidence for the derived TRACE product only. |

Archive Search, TRACE atlas/catalogs, and TRACE neighborhood shards are derived products. They can prove the behavior and population of v48 read products, but they are not migration inputs. If a derived product contains an ID absent from the canonical JSON, that ID is not inserted into v49 merely to preserve the product.

TRACE nodes/edges beyond fields present in the canonical JSON may enter v49 only when a versioned deterministic transformation independently regenerates them from that JSON and governed configuration. Derived assets/SQLite may then verify IDs, counts, and hashes, but cannot fill a regeneration gap. Anything not reproducible from the migration input remains excluded with a blocking delta ledger entry.

The legacy `frontend/src/data/public_surface_mock_v0.json` is the exact 8,636-ID source of `archive-search-v1.json`; it is not one of the five frozen migration-authority artifacts.

## 2. Raw bytes, JSONB, and equality

### Lexical authority

The artifact byte stream, byte length, media type, and SHA-256 define source identity. Byte equality means:

```text
same byte_length AND same sha256(raw_bytes)
```

Only byte equality can satisfy a frozen-artifact gate. Whitespace, object member order, escaping, number spelling, Unicode code points, and line endings are therefore significant at this layer.

The complete raw bytes live in immutable object/file storage addressed by hash. PostgreSQL stores the artifact identity and storage locator. Record rows point into the artifact by JSON Pointer plus source ordinal; they do not pretend that a reserialized row is the original byte sequence.

### Parsed projection

JSONB is a parsed convenience projection, not lexical authority. It may normalize whitespace, key order, numeric spelling, and duplicate-key behavior. A JSONB value cannot be hashed to reconstruct or certify the frozen file.

Strict parsing rejects duplicate object keys, invalid Unicode, non-JSON numeric values, and trailing content. The parser version and policy digest are recorded with the projection.

### Semantic equality

Semantic equality is a separate comparison used for transformation diagnostics:

- JSON object member order is ignored;
- array order is significant;
- strings compare by exact Unicode scalar sequence with no normalization;
- numbers compare by their exact mathematical JSON value after lossless parsing;
- missing, `null`, empty string, empty array, and empty object remain distinct;
- duplicate object keys are invalid, not “last value wins.”

An optional semantic digest uses RFC 8785 canonical JSON over the validated parse tree. Semantic equality never changes artifact identity and never substitutes for the raw SHA-256 gate.

## 3. Identity and cardinality ledger

### Measured v48 facts

| Subject | Measured fact | Consequence |
|---|---|---|
| Canonical surfaces | 15,923 rows and 15,923 unique `surfaceId` values. No `archiveObjectId` field exists. | v48 does not independently express intellectual-object identity. |
| Source records | 15,923 non-null and unique `sourceRecordId` values. | The seed import can account for one source record per JSON row. |
| Source object keys | 15,921 unique `(identity_scope, source_object_key)` pairs across 15,923 rows. Two pairs collide. | `source_object_key`, alone or scoped, is not a key. |
| TRACE roots | Every canonical surface has one non-null, unique `trace.objectNodeId`; all 15,923 resolve to a `trace_nodes` row of type `object`. | v48 canonical surface ↔ active TRACE root is exactly 1:1. |
| TRACE nodes | 97,889 unique `node_id`; only 82,918 unique `canonical_key`. Even `(tree_id,node_type,canonical_key)` yields 97,647 groups. | `canonical_key` is descriptive, never node identity. |
| Folder memberships | 185 folders and 47,982 unique `(folderId,surfaceId)` pairs. Folder-side and surface-side arrays are exactly equal. | The pair is the v48 natural membership identity. |
| Membership degree | All 15,923 canonical surfaces have memberships: 15,716 have 3, 201 have 4, and 6 have 5. Folder sizes range 1–10,010. | Folder ↔ member is N:M, not an embedded array or 1:N shortcut. |
| Relation edges | 255,695 edge IDs and 255,695 unique directed `(subject_node_id,edge_label,object_node_id)` triples. | The typed directed triple is the semantic edge natural key for the v48 model. |
| Object relation memberships | 126,822 unique `(surface_id,edge_id)` pairs covering all 15,923 canonical surfaces; no edge is shared by two surfaces in v48. | Membership is separate from edge identity and is counted as rows, not distinct edges. |
| Evidence | 255,247 distinct `(evidence_url,evidence_text,evidence_field)` composites. 389 composites are reused across 837 edges, with maximum reuse 7. | Evidence is a shareable entity and cannot be embedded as the edge identity. |

The two known scoped source-key collisions are retained as separate source records because their `sourceRecordId` and `surfaceId` differ. They are key `2016648591` on `SURF-CGS2026R0740` / `SURF-LOCTRACE2026R02046`, and key `96523423` on `SURF-CGS2026R0383` / `SURF-LOCTRACE2026ICC0337ACE0D517`. No automatic duplicate merge is allowed.

### v49 identifier decisions

| Identifier | Decision |
|---|---|
| `entity_id` | Internal immutable PostgreSQL `uuid`, globally unique across `core` subtypes. It is never reused or exposed as the scholarly/public route identifier. |
| `archive_object_id` | The `entity_id` of a `core.archive_object` subtype row; its PK is also an FK to `core.entity`. |
| v48 seed object ID | UUIDv5 using RFC 4122 URL namespace `6ba7b811-9dad-11d1-80b4-00c04fd430c8` and exact UTF-8 name `https://modern-gd-history.example/identity/v49/v48/surface/<surfaceId>`, with no case/Unicode normalization. Each of the 15,923 JSON rows creates one object; Phase 1 never deduplicates them. |
| future object ID | UUIDv7 generated once and persisted. Generation method does not alter UUID comparison or FK semantics. |
| `surface_id` | Case-sensitive durable public/legacy text identifier. It is an identifier/route, not a `core.entity` subtype and not the canonical object PK. |
| `source_record_id` | Internal immutable UUID of one raw record occurrence. The v48 value is retained in the legacy crosswalk, not used as a PostgreSQL PK. |
| `trace_node_id` | Internal immutable UUID in `research.trace_node`; the legacy `TRN-*` value is crosswalk data. A trace node is not automatically a `core.entity`. |
| `relation_edge_id` | Internal immutable UUID. Natural-key uniqueness is enforced separately from the surrogate ID. |
| `folder_membership_id` | The `assignment_id` of the folder-membership assignment subtype. The natural key remains the typed pair described below. |

UUIDv5 is required only for deterministic seed replay. It does not assert that the source row describes a globally unique real-world object. Other v48 legacy-ID seeds use the same URL namespace and exact names `https://modern-gd-history.example/identity/v49/v48/{trace-node|trace-edge|folder}/<legacyId>`. Raw record names are `https://modern-gd-history.example/identity/v49/raw/<artifactSha256>/record/<zeroBasedOrdinal>` so non-unique provider keys cannot collide. Names use source case and Unicode bytes unchanged.

### Object ↔ surface

`surface_id` maps to exactly one current archive object or to one explicit terminal resolution (`merged`, `split`, `withdrawn`, or `unresolved`). It never maps silently to multiple current objects.

An archive object has one primary surface ID when publicly routable and may have zero or more alias surface IDs. The v48 seed is exactly 15,923 object-to-surface mappings, all 1:1 and primary. Merges can make several legacy surface IDs resolve to one object. Splits do not choose an arbitrary successor; the old surface ID becomes a split landing identity with explicit successor links.

Release surface rows are immutable projections keyed by `(release_id,surface_id)` and contain `archive_object_id`. They are copied from the candidate snapshot and never join live canonical tables after sealing.

### Object ↔ source

`provenance.object_source_record` is N:M with a natural key `(archive_object_id,source_record_id,source_role)`. One object can have several descriptions/evidence records; one compound/bibliographic source record can support several objects.

The v48 seed is exactly 1:1: each of the 15,923 seed objects links to its one unique JSON `sourceRecordId` with role `seed_description`. Later consolidation does not delete or retarget source records.

Raw record occurrence identity is `(source_artifact_id,record_ordinal)`. Provider keys and locators are indexed attributes, not unique keys; collisions are preserved.

### Trace object/node identity

`research.trace_node` has its own surrogate identity. `canonical_key`, label, tree, and node type are attributes. A node may optionally reference one `core.entity` through a real FK; many research nodes may reference the same entity.

`research.object_trace_node` is the typed object/root join with natural key `(archive_object_id,trace_node_id,role)`. A root trace node references at most one archive object; an object may have multiple trace nodes across trees or research contexts. The v48 seed has exactly one `root` node per object and one object per root node.

### Folder ↔ member

Folder membership targets `core.archive_object`, never a presentation JSON array. Its natural key is `(folder_id,archive_object_id,membership_role)`; v48 imports use role `curated_member`. The current 47,982 `(folderId,surfaceId)` pairs become 47,982 assignments after the deterministic surface-to-object crosswalk.

Folders and archive objects are N:M. Position/order is an assignment attribute, not identity. Reordering does not create a new membership; changing role does.

## 4. Population boundary: Search versus TRACE

Define:

- `C`: canonical v48 JSON surface IDs, exactly equal to the TRACE active catalog IDs;
- `S`: legacy frontend mock surface IDs, exactly equal to archive Search item IDs.

| Population | Exact count |
|---|---:|
| `|C|` canonical JSON / active TRACE | 15,923 |
| `|S|` frontend mock / archive Search | 8,636 |
| `|C ∩ S|` | 2,585 |
| `|S − C|` Search-only legacy surfaces | 6,051 |
| `|C − S|` canonical/TRACE-only surfaces | 13,338 |
| `|C ∪ S|` distinct legacy surface IDs | 21,974 |

Consequences:

1. Search is not a subset of the v48 migration cohort.
2. Only `C` seeds v49 from v48. The 6,051 Search-only rows cannot enter `raw` or `core` from the Search artifact because Search is derived, not source authority.
3. A future provider-backed re-ingest may recover a Search-only object, but it is a new governed ingest that must establish its own raw artifact and crosswalk.
4. Migration reconciliation reports all six population values. It does not demand that a v49 Search projection reproduce 8,636 rows from non-authoritative input.
5. Search indexing in v49 is built from the sealed release cohort, not copied from `archive-search-v1.json`.

## 5. Legacy crosswalk, redirect, merge, and split policy

The identity crosswalk uses typed FK-bearing tables, one per legacy target class where necessary. A generic registry can identify the namespace, but no row stores an unconstrained `target_type + target_id` pair.

Required namespaces include `v48.surface`, `v48.source_record`, `v48.trace_node`, `v48.trace_edge`, and `v48.folder`. Each `(namespace,legacy_id)` is immutable and unique. History is append-only; an effective-resolution constraint allows at most one current resolution.

- Rename: IDs do not change; labels are versioned attributes.
- Redirect/alias: legacy surface ID remains resolvable and points to the same object as the primary ID.
- Merge: a curator decision chooses the survivor object. Losing object IDs become `merged`; all legacy IDs remain and resolve/redirect to the survivor. Assertions, sources, and decisions are not rewritten.
- Split: the original object and surface ID become `split`; successor links are N:M and ordered. Each successor receives a new public surface ID. A split landing response lists all successors and never selects one implicitly.
- Withdrawal: the ID remains a tombstone with reason/evidence; it is never reused.
- Conflicting/uncertain identity: status is `unresolved`; no merge, redirect, or split occurs until an effective curator decision exists.

Every transition records effective release, decision ID, evidence, actor, and superseded resolution. Redirect projections are sealed release assets and cannot be recomputed from mutable current identity rows at read time.

## 6. `core.entity` supertype/subtype decision

`core.entity` is a closed supertype for normalized intellectual entities. It contains the UUID, `entity_kind`, lifecycle state, and audit timestamps. Initial subtypes are:

- `core.archive_object`;
- `core.agent`;
- `core.place`;
- `core.concept`;
- `core.collection`;
- `core.temporal_extent`.

Each subtype uses `entity_id` as both PK and FK to `core.entity`. A deferred integrity check enforces exactly one subtype row matching `entity_kind` at transaction end.

Source records, TRACE nodes, folders, evidence, citations, digital representations, workflow cases, and releases are not `core.entity` subtypes. They have their own typed keys and may reference a core entity where semantically valid.

Rules for targets:

1. A semantically specific relation uses an FK directly to the required subtype, such as `archive_object_id` → `core.archive_object(entity_id)`.
2. A deliberately multi-kind semantic target uses `target_entity_id` → `core.entity(entity_id)`, plus a registered relation/predicate rule that constrains allowed `entity_kind` values.
3. Literal and entity assertion values use separate subtype tables.
4. References to non-entity classes use typed FK columns or typed bridge tables.
5. Unconstrained `target_type + target_id`, JSON references, and text IDs without an FK are prohibited in canonical, workflow, rights, research, and release tables.

## 7. Assertions, assignments, evidence, and curator decisions

### Logical records

- An assertion is a source-bounded claim with exactly one registered predicate, exactly one typed subject subtype, and exactly one typed value subtype. Initial subject subtypes are core entity, raw source record, TRACE node, and digital representation; initial value subtypes are core entity, raw literal, raw source record, and TRACE node.
- A canonical assignment is the identity-bearing supertype for an accepted/proposed normalized join or relation. Typed assignment tables use `assignment_id` as PK/FK.
- Evidence is a shareable source-bound record/locator/span. It is neither an assertion nor an assignment.
- A curator decision is an append-only outcome on exactly one review case. It can accept, reject, defer, merge, split, withdraw, or supersede according to the case kind.

### Cardinalities and bridges

| Relationship | Cardinality and invariant | Bridge |
|---|---|---|
| source record → field literal | 1:N; a record can have zero literals only if parsing failed and a workflow exception exists. | Direct FK from literal. |
| field literal → assertion | 1:N; zero assertions is valid for uninterpreted input. | Direct FK or assertion input bridge for composed claims. |
| assertion → subject | Exactly 1:1 across the closed typed subject tables. | One subject subtype row, enforced deferred. |
| assertion → value | Exactly 1:1 across the closed typed value tables. | One value subtype row, enforced deferred. |
| assertion ↔ evidence | N:M; an accepted assertion requires at least one qualifying supporting evidence row. | `provenance.assertion_evidence` with stance and ordinal. |
| assignment ↔ assertion | N:M; accepted assignment needs accepted support or an evidence-bearing effective curator decision. | `provenance.assignment_assertion` with support role. |
| evidence ↔ curator decision | N:M; every effective identity/accept/reject decision requires at least one evidence row. | `workflow.decision_evidence`. |
| review case → decision | 1:N append-only; at most one non-superseded effective decision. | Direct case FK from decision. |
| review case → reviewed subject | Exactly 1:1 across typed case-subject tables. | Separate `review_case_assertion`, `review_case_assignment`, or other typed subtype table. |

Assignments do not carry an independent opaque evidence JSONB. Evidence reaches an assignment through accepted assertions or an effective curator decision, so the provenance path is singular and auditable.

### Evidence identity and deduplication

Evidence natural identity is:

```text
(source_artifact_id, source_record_id, locator_scheme, locator_value,
 byte_or_character_span, content_sha256)
```

Exact repetition of that identity reuses one evidence row. The same URL/text from different source records is not automatically deduplicated. Text equality alone, normalized URL alone, or content hash alone is insufficient. Edge/evidence and assertion/evidence bridges are unique on `(subject_id,evidence_id,stance)`; duplicate observations update neither edge counts nor membership counts.

## 8. Relation edge and membership semantics

### Relation edge identity

`research.relation_edge` is a typed canonical assignment. Its directed natural key is:

```text
(subject_trace_node_id, relation_type_id, object_trace_node_id)
```

Direction is significant. Evidence, confidence, review state, publication layer, tree, and branch are not part of edge identity.

Tree/branch placement is N:M in a separate typed bridge with natural key `(relation_edge_id,tree_id,branch_id)`. Multiple evidence rows attach through a unique edge/evidence bridge. Contradictory evidence uses an explicit stance and does not duplicate the edge.

The 255,695 v48 triples are all unique, so this rule is lossless for the frozen model. Legacy edge IDs crosswalk to the canonical edge. If a later import repeats a triple, it adds provenance/evidence/placement rather than another edge.

### Object relation membership identity

`research.object_relation_membership` is a separate assignment with natural key:

```text
(archive_object_id, relation_edge_id, membership_role)
```

v48 imports use `membership_role='active_object_relation'`. A relation edge can be relevant to many objects in v49 even though v48 happened to map each membership edge to at most one surface. Evidence changes do not create a new membership.

### Count SQL semantics

Counts are computed only from sealed, copied release projections. They never join live canonical tables after sealing.

`total_graph_edges` means one row per included semantic edge:

```sql
SELECT count(*)
FROM release.relation_edge_projection AS edge
WHERE edge.release_id = :release_id
  AND edge.included_in_graph = true;
```

`active_object_relation_memberships` means eligible membership rows, not distinct edges:

```sql
SELECT count(*)
FROM release.object_relation_membership_projection AS membership
JOIN release.relation_membership_metric AS metric
  ON metric.release_id = membership.release_id
 AND metric.membership_id = membership.membership_id
WHERE membership.release_id = :release_id
  AND membership.publication_layer = 'active'
  AND metric.metric_code = 'active_object_relation_memberships'
  AND metric.eligible = true;
```

Family counts add a join to the sealed relation-type snapshot and group by its family. They must sum to the active membership count. `count(DISTINCT edge_id)` is explicitly wrong for this metric.

## 9. Orthogonal states

The following axes are independent and stored in their owning layer:

| Axis | Owner and values | Meaning |
|---|---|---|
| workflow state | `workflow`: `queued`, `claimed`, `in_review`, `resolved`, `superseded` | Processing progress only. It does not accept or publish data. |
| acceptance state | assertion/assignment: `proposed`, `accepted`, `rejected`, `superseded` | Epistemic/editorial outcome. `held` is not an acceptance value. |
| rights decision | `rights`: `unresolved`, `permitted`, `source_only`, `metadata_only`, `denied` | Effective use/display decision for a specific representation and policy version. |
| publication layer | sealed release projection: `active`, `review`, `auxiliary`, `excluded` | Audience/read-layer placement for that release. It is not workflow state. |
| count eligibility | sealed release metric membership: `eligible`/`ineligible` plus reason | Eligibility for one named metric in one release; never a universal canonical-object boolean. |

Implications are prohibited: accepted does not imply active; active metadata does not imply image permission; permitted rights do not imply acceptance; resolved workflow can end in rejection; review publication layer does not mean a case is currently in review; count eligibility for one metric says nothing about another.

An unknown relation label is a raw assertion with acceptance `proposed` and workflow `queued`. No canonical edge exists, no publication layer is assigned, and no metric membership exists. This is the G4/G5 fail-closed resolution.

## 10. Release state machine and seal protocol

The only forward release states are:

```text
draft → candidate → validated → sealed
```

A failed attempt remains in its current state with failed workflow receipts; remediation creates a new attempt/release ID. `superseded` is metadata on a sealed release/current pointer history, not a mutation state that relaxes sealing.

### State invariants

- `draft`: projection rows/assets may be rebuilt under the draft attempt. No manifest hash or public resolution exists.
- `candidate`: input snapshot, migration/query digests, registries, projection rows, asset paths, and cohort are closed. Canonical-table changes after this point cannot enter the candidate.
- `validated`: all required pre-seal receipts pass and the candidate projection/asset inventory is immutable. It is not yet public/current.
- `sealed`: canonical manifest bytes/hash are committed with the state transition; projection and asset inventory are immutable forever.

### Protocol

1. In a repeatable snapshot, build copied release projections under `draft`.
2. Close the cohort and transition to `candidate` using compare-and-swap on state/version.
3. Produce pre-seal receipts for all five frozen artifacts, migration/query digests, exact counts/populations, FK/orphan checks, relation registry, rights policy, unknown-relation isolation, projection fingerprints, deterministic asset inventory, and authorization matrix.
4. Transition `candidate → validated` only when every required receipt is present, immutable, passing, and hash-bound to the same candidate fingerprint.
5. Generate RFC 8785 manifest bytes from the validated inventory and receipt hashes. Compute SHA-256 over those exact bytes.
6. In one serializable transaction, verify the candidate fingerprint again, store manifest bytes/hash, and transition `validated → sealed`. Any mismatch aborts the transaction.
7. Enforce sealed immutability through ownership, revoked DML, and a defense-in-depth trigger. Sealed projections are copied rows, never views that join mutable canonical tables.
8. Write the post-seal detached sidecar containing release ID, manifest SHA-256, seal transaction identity, timestamp, and optional signature/attestation. The sidecar cannot be inside the self-hashed manifest and cannot alter its asset inventory. If sidecar creation fails, the release remains sealed but is not pointer-eligible.
9. Publish `current` only through CAS on `(channel,expected_generation,expected_release_id,expected_manifest_sha256)`. The replacement must be sealed and have a verified sidecar. Rollback is the same CAS operation to an older sealed pair.

The current pointer is mutable routing metadata with append-only history. It is never embedded in evidence, manifests, shards, or scholarly citations.

## 11. Role and privilege matrix

All schemas, tables, sequences, types, and security-definer functions are owned by `v49_owner`, a `NOLOGIN` role. `PUBLIC` receives no schema `CREATE`, table privilege, sequence privilege, or function execute privilege. Application roles own no objects and are `NOINHERIT` unless explicitly stated.

| Role | Allowed | Explicitly denied | Ownership / elevation |
|---|---|---|---|
| `owner` (`v49_owner`) | Own database objects; emergency repair under audited break-glass procedure. | Routine login/application use. | `NOLOGIN`; sole object owner. |
| `migrator` | Connect during migration window; `SET ROLE v49_owner`; create/alter/drop/seed only through reviewed migration transaction. | Runtime ingest, review, release, reader traffic; persistent credentials. | Ephemeral login; only role granted owner membership. |
| `ingestor` | Read registered source/term metadata; append raw artifacts/records/literals/import runs; call allowlisted functions that create proposed assertions/assignments and workflow cases. | Update/delete raw rows; accept/reject; direct canonical DML; rights override; release/seal/current; DDL. | Owns nothing; no owner/releaser membership. |
| `reviewer` | Read raw/provenance/canonical candidates needed for assigned cases; claim cases; append decisions/evidence through allowlisted functions. | Rewrite raw/assertions/history; direct assignment acceptance updates; release assets/state/current; DDL. | Owns nothing; decision functions record `session_user`. |
| `releaser` | Read accepted canonical state and receipts; build draft copied projections; execute candidate/validate/seal/current-CAS functions; read all release artifacts. | Change raw/core/provenance/rights/research/workflow decisions; mutate candidate after validation; update/delete sealed rows; DDL. | Owns nothing; seal/CAS only through definer functions. |
| `reader` | `SELECT` sealed `api_v1` and public release descriptors/projections; execute safe read functions. | Raw, canonical, provenance, rights internals, workflow, unsealed release data, all DML/DDL. | Owns nothing; no role inheritance. |
| `auditor` | Read-only access to all schemas through audited views, including raw hashes, receipts, grants, and pointer history; execute pure verification queries. | All DML/DDL, queue claims, decisions, release transitions, CAS, `SET ROLE`, `BYPASSRLS`. | Owns nothing; sensitive payload access uses explicit audit views, not definer bypass. |

### `SECURITY DEFINER` boundary

Only append-raw, record-decision, release-transition, seal, and current-CAS operations may use `SECURITY DEFINER`. Each function:

- is owned by `v49_owner` and has `EXECUTE` revoked from `PUBLIC`;
- is granted only to the one role named by the matrix;
- pins a safe `search_path`, schema-qualifies objects, validates state and typed FKs, and uses no caller-supplied identifiers or dynamic SQL;
- records `session_user`, transaction ID, inputs, result, and receipt hash;
- locks/CAS-checks the target row and fails closed;
- cannot disable constraints, triggers, RLS, or sealed-row protections.

Auditing and ordinary reads are `SECURITY INVOKER`. The migrator uses explicit `SET ROLE` rather than a general-purpose definer function.

## 12. Pre-DDL entry gate

All P0 decisions in this pack are closed. DDL may begin only if its review demonstrates:

- every canonical reference has a real FK or a typed bridge;
- entity subtype exclusivity is enforceable;
- the identity crosswalk can represent aliases, merge, split, withdrawal, and unresolved cases without ID reuse;
- v48 imports only the canonical JSON cohort and preserves the five-artifact integrity ledger;
- state axes are separate columns/relations in their owning layers;
- relation/membership natural keys and count queries match this pack;
- release DDL can enforce the full validated/seal/CAS protocol;
- grants match the complete role matrix with no `PUBLIC` leakage.

Index choice, partition size, storage implementation, and query-plan tuning remain physical-design decisions. They cannot weaken these P0 invariants.

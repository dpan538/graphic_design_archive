# D1 — Candidate mapping, identity, and raw-preservation review

- Task: Phase 2B Queue D1, read-only mapping review
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Baseline observed: `86ba95cae9ecf12e58fcabb8170c9020e151b386`
- Candidate input: `generated/public_surfaces_prefreeze_candidate_v48.json`
- Candidate SHA-256: `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`
- Result: **PASS WITH IMPLEMENTATION PRECONDITIONS**

## Task boundary

This review establishes implementation-facing requirements from the existing
normative model and audited, committed measurements. It did **not** open or
parse the 190 MB Candidate JSON, start PostgreSQL, modify a schema migration,
alter a historical receipt, or inspect/write the protected main worktree.

The only file written by this task is this independent receipt. The primary
Phase 2B executor remains responsible for one strict Candidate parse, actual
field-inventory generation, mapping/replay implementation, and all database
work.

## Evidence read

| Evidence | Why it was read |
|---|---|
| `database/JSON_MIGRATION_CONTRACT.md` | Sole canonical input, raw staging, fail-closed TRACE/visual rules. |
| `database/PHYSICAL_SCHEMA.md`, `database/README.md` | Physical domain and role boundaries. |
| `database/migrations/001_foundation.sql`, `002_raw_core_provenance.sql`, `003_research_rights.sql`, `005_normative_closure.sql` | Existing target tables, closed enums, natural keys, and baseline-disposition storage. |
| `database/functions/001_deferred_constraints.sql`, `004_controlled_writes.sql`, `015_final_integrity_closure.sql` | Deferred FK/state requirements relevant to a deterministic import. |
| `docs/architecture/DDL_DECISION_PACK_V49.md` | Fixed UUIDv5 and legacy-crosswalk rules. |
| `MIGRATION_V48_TO_V49.md`, `DATA_MODEL_V49.md` | Seed, raw, folder, TRACE, visual, and no-dedup policy. |
| Phase 1C receipts `05_METADATA_SUPPORTED_RECONCILIATION.md`, `09_RESEARCH_CORPUS_POLICY.md`, `10_CORPUS_MEMBERSHIP_BASELINE.tsv`, `13_AUTHORITY_RESEARCH_GATE_RECEIPT.md`, and A2 receipt | Exact field/array measurements and research disposition authority. |
| Phase 1D decision pack, visual cardinality matrix, baseline summary, and verifier source | Visual identity, occurrence semantics, and exact observed visual fields/metrics. |
| `docs/audits/v49-phase2a-schema/12_PHASE2A_GATE_RECEIPT.md` | Schema baseline is implemented; no Phase 2A DDL may be revised here. |

## Locked population and identity rules

### Input authority

`generated/public_surfaces_prefreeze_candidate_v48.json` is the only artifact
whose records may produce `raw`, `core`, `research`, `rights`, `provenance`,
or workflow population rows. It has byte length `190067852` and the frozen
SHA-256 above. SQLite, transfer manifests, TRACE assets/catalogs, Search, and
Phase 1 audit ledgers may be registered/reconciled but produce **zero**
canonical rows or backfilled fields.

`raw.source_asset` must be inserted by the migration authority with
`authority='canonical_migration_input'`; this is intentional. The runtime
`raw.register_source_asset` function permits only `governed_source`, while the
`migrator` is the only role with owner membership for frozen authority kinds.
That is a role boundary, not a schema defect and not a reason to use the
runtime ingestion path.

### Stable UUIDv5 recipes

Use the RFC 4122 URL namespace:

```text
6ba7b811-9dad-11d1-80b4-00c04fd430c8
```

Names are exact UTF-8 strings. Do not trim, case-fold, Unicode-normalize, or
rewrite whitespace before passing them to UUIDv5.

| Identity | Exact UUIDv5 name |
|---|---|
| Archive object | `https://modern-gd-history.example/identity/v49/v48/surface/<surfaceId>` |
| Raw source record | `https://modern-gd-history.example/identity/v49/raw/<candidateSha256>/record/<zeroBasedOrdinal>` |
| Legacy TRACE root | `https://modern-gd-history.example/identity/v49/v48/trace-node/<trace.objectNodeId>` |
| Legacy folder | `https://modern-gd-history.example/identity/v49/v48/folder/<folderId>` |
| External visual reference | `urn:graphic-design-archive:v49:v48:visual-reference:<surfaceId>:<RFC6901-json-pointer>:<zeroBasedOccurrenceOrdinal>` |

The `.example` component above is a frozen UUID namespace input only. It must
never appear as a public stable URI. The public identity remains the generated
`urn:gdarchive:{object|relation|claim|source|visual-reference}:<uuid>`.

For deterministic auxiliary keys (field literal, source/visual bridge,
classification, assessment and batch) derive a documented UUIDv5 name from
the fixed Candidate SHA plus the exact stable occurrence tuple. Do not use
`gen_random_uuid()`, sequences, session IDs, or timestamps as identity input.

## Strict parse and canonicalization contract

The importer should name its encoder `gda-json-c14n-v1` and must:

1. decode UTF-8 strictly and reject duplicate object keys through a pair-hook;
2. reject `NaN`, `Infinity`, unsupported values, a non-object root, or a
   non-array `/surfaces` member before connecting to PostgreSQL;
3. recursively serialize values with object keys sorted lexicographically,
   arrays in original order, compact JSON delimiters, `ensure_ascii=false`,
   and non-finite numbers disabled;
4. preserve source string code points exactly: no trim, case fold, whitespace
   rewrite, or Unicode normalization;
5. use RFC 6901 escapes (`~` → `~0`, `/` → `~1`) for every stored pointer;
6. make a per-surface semantic digest from the `gda-json-c14n-v1` bytes and
   keep the whole frozen Candidate byte stream as the lexical source asset.

The full raw record plus its parsed projection preserves distinction between
missing properties and explicit JSON values. The occurrence ledger must also
record one of `MISSING`, `NULL`, `EMPTY_STRING`, `EMPTY_ARRAY`,
`EMPTY_OBJECT`, or `PRESENT`; this cannot be collapsed into SQL `NULL`.
For present scalar/container occurrences, create `raw.field_literal` rows
with a canonical lexical JSON value (including `null`, `[]`, `{}`, and `""`),
JSON Pointer, occurrence ordinal, JSON type, presence class, and literal hash
in the staging/field ledger. For a missing path, emit no fictional literal;
the row's c14n `parsed_projection` plus the occurrence ledger is the proof of
absence.

The schema does not have a separate `presence_class` column. This is not a
blocker: `raw.source_record.raw_value` and `parsed_projection` preserve the
source object structurally, while the deterministic temporary/full occurrence
ledger provides explicit field-level presence evidence. The committed
generator must be able to recreate that ledger and its hashes.

## Audited Candidate field and array inventory

The following is a minimum exact-pattern registry. `mapping-v1.json` must
also contain a deliberate recursive `raw_snapshot_only` rule for all observed
paths not otherwise normalized, and a generated observed-pointer inventory.
An observed pointer which matches neither an exact rule nor that explicit
raw-only rule must stop the import. This makes `UNMAPPED_SOURCE_FIELDS=0`
meaningful without pretending the historical JSON has a fixed small schema.

| Pattern | Audited shape / count | Phase 2B handling |
|---|---:|---|
| `/surfaces/*/surfaceId` | 15,923 nonblank unique strings | Exact identity; one surface crosswalk and one archive object. |
| `/surfaces/*/sourceRecordId` | 15,923 nonblank unique strings | Exact legacy source ID and one deterministic raw record. |
| `/surfaces/*/sourceUrl` | 15,923 strings | Raw literal only; no URL identity or automatic source/rights inference. |
| `/surfaces/*/sourceObjectKey` | 7,711 present strings; 8,212 missing | Raw field and presence ledger; never a dedup key (two scoped collisions are known). |
| `/surfaces/*/sourceLocator` | 4,747 present strings; 11,176 missing | Raw/internal provenance literal only. |
| `/surfaces/*/{title,creator,medium,objectType}` | all 15,923 strings | Preserve literal. `title` may be a conservative object label; creator/medium/type stay raw/proposed unless an approved mapping applies. |
| `/surfaces/*/sourceSubjects` | all strings; 458 blank | Preserve one literal; never split delimiters. |
| `/surfaces/*/{placeText,dateText}` | audited delimiter-risk strings | Preserve one literal; do not synthesize place/temporal entities. |
| `/surfaces/*/dateEnd` | 15,847 numbers; 76 explicit nulls | Preserve JSON type/presence; no inferred date conversion. |
| `/surfaces/*/collectionEvidence` | 15,918 objects; 5 missing | Recursive raw preservation; no auto collection entity. |
| `/surfaces/*/{publicationRole,publicationGate}` | 15,921 present; 2 missing each | Recursive raw/workflow context only; no acceptance state inference. |
| `/surfaces/*/reviewGates/rightsReviewed` | observed optional structured value | Raw visual/review context only, never rights permission. |
| `/surfaces/*/folders/*` and the candidate folder-side array | 185 folders; 47,982 exact `(folderId,surfaceId)` pairs | The only permitted structured membership expansion. Recompute both sides independently, compare pair-set hash, then create 47,982 `curated_member` assignments; otherwise fail before canonical import. |
| `/surfaces/*/compoundChildren/*` | 15 parents; 132 elements | Preserve ordered raw literals. Do not create canonical parent/child joins absent a dedicated approved mapping/identity proof. |
| `/surfaces/*/tables/*` and `/rows/*` | 95,538 tables; 808,809 rows | Preserve ordered raw literals/containers. No table/citation/assertion normalisation in this phase. |
| `/surfaces/*/trace/*` | 15,923 objects | See separate TRACE gate below. |
| `/surfaces/*/{image,images,rights}` | 15,923 visual bundles | See separate visual mapping below. |
| any other observed pointer | dynamic historical schema | Recursive c14n raw field occurrence, explicit `raw_snapshot_only` mapping/disposition, no silent drop. |

Important delimiter incidence confirms why the raw-only policy is required:
`creator` (3,849 semicolons), `medium` (10,791), `objectType` (7,117),
`sourceSubjects` (15,233), `placeText` (864), and `dateText` (47). Semicolon,
pipe, slash, newline, or blank text are not a permission to split, trim,
deduplicate, zip, or create entities.

## Direct population map

| Source occurrence | Physical target / required result | Safety condition |
|---|---|---|
| frozen Candidate bytes | `raw.source_asset` | one `canonical_migration_input` asset with exact bytes/SHA; all other frozen artifacts can be ledger-only evidence. |
| mapping declaration | `raw.mapping_version` | `version_token`, mapping SHA, extractor version; delimiter policy exactly `preserve_no_automatic_split`. |
| deterministic bundle | `raw.migration_batch` | UUID/token binds Candidate SHA, mapping SHA/version, Phase 2A schema SHA, extractor SHA, and base implementation commit in the sidecar/receipt; `input_sha256` exactly matches the asset. |
| each `/surfaces/<i>` | `raw.source_record`, `raw.field_literal` | raw record UUID uses zero-based ordinal; semantic c14n digest and raw literal occurrence evidence are reproducible. |
| each accounted surface | `raw.legacy_surface_ledger`, `core.entity`, `core.archive_object` | 15,923 one-to-one mappings; archive object UUID uses exact `surfaceId`; no deduplication. Set `accounted` for the 7,995 strict-eligible rows and `held` for the 7,928 strict-held rows, each with object FK and explicit reason. |
| object → raw source | `provenance.object_source_record` | exactly 15,923 `seed_description` links. |
| `surfaceId`, `sourceRecordId` | `core.legacy_identity` + typed resolution | namespaces `v48.surface` and `v48.source_record`; no polymorphic string target. |
| `trace.objectNodeId` | `research.trace_node`, `research.object_trace_node`, `core.legacy_identity`/resolution | exactly 15,923 root crosswalks only; no legacy edge, semantic relation, membership, tree placement, or projection edge. |
| exact folder pair | `research.folder`, folder identity/resolution, `provenance.assignment_folder_membership` | only after dual-side Candidate pair-set verification; role `curated_member`, ordinal preserved but not identity. |
| explicit `trace.tier=source_verified` | strict `research.corpus_membership` | exactly 7,995 eligible rows, reason `EXPLICIT_SOURCE_VERIFIED_TIER`. |
| explicit `metadata_supported` / missing tier | raw ledger / fail-closed delta + tier/corpus audit ledger | 2,971 + 4,957 held; do not use SQLite's 12,952 fallback. If a corpus table represents only strict membership, do **not** insert held rows there. |

The Phase 1C policy permits no rejected source rows: all 15,923 operational
objects are retained; `REJECTED_OBJECTS=0`. It also fixes the stale
`/meta/traceMetadataSupportedCount=2970` as raw/reconciliation-only metadata,
not a fabricated 2,970-member set.

## TRACE gate

Populate only source-supported root crosswalk data and raw literals:

```text
trace.tier, trace.state, trace.reviewState, trace.influenceState,
trace.treeId, trace.objectNodeId, trace.edgeCount,
trace.branchIds[], trace.edgeIds[], trace.edgeLabels[]
```

Known limits are binding:

- `trace.edgeIds[]`: 126,822 occurrences, all unique;
- `trace.edgeLabels[]`: 79,683 occurrences / 20 labels;
- 9,393 surfaces have unequal `edgeIds` and `edgeLabels` lengths;
- `trace.edgeCount == len(edgeIds)` for all input rows;
- 30 tree IDs and 15,923 unique root node IDs.

`edgeLabels` is a per-surface vocabulary summary, not a positional mapping to
`edgeIds`. Store each array and its own item ordinals. Record
`unsafe_pairing/held` for the 9,393 mismatch rows; create no pair, semantic
relation, accepted claim, legacy projection fact as canonical relation, TRACE
membership, or TRACE projection edge. Required imported values remain:

```text
ACCEPTED_SEMANTIC_RELATIONS=0
TRACE_PROJECTION_EDGES=0
TRACE_ELIGIBLE_OBJECTS=0
UNKNOWN_RELATION_COERCIONS=0
AUTOMATIC_INFLUENCE_INFERENCE=0
```

## Tier and strict-corpus disposition

| Exact Candidate state | Count | Operational disposition | Strict corpus result |
|---|---:|---|---|
| `trace.tier == source_verified` | 7,995 | accounted | eligible; the only inserted strict-corpus memberships |
| `trace.tier == metadata_supported` | 2,971 | held | not in strict corpus; reason `METADATA_SUPPORTED_BELOW_STRICT_EVIDENCE_THRESHOLD` |
| `trace.tier` missing/blank | 4,957 | held | not in strict corpus; reason `MISSING_EXPLICIT_EVIDENCE_TIER` |
| unregistered nonblank tier | 0 in frozen baseline | held | fail closed; import must reject/hold rather than promote |

The matching immutable SQLite/TRACE 2,971 set is reconciliation evidence only.
The SQLite 12,952 `source_verified` value is a legacy builder fallback and
must yield `SQLITE_BACKFILLED_ROWS=0` and `SQLITE_BACKFILLED_FIELDS=0`.

## Visual raw mapping and fail-closed delivery

The Candidate visual bundle is per surface, not a URL set. The audited fields
are:

| Pattern | Observed count | Required treatment |
|---|---:|---|
| `/image/url` | 15,621 valid locator occurrences | one exact typed locator occurrence per source occurrence; preserve value without normalization/dedup. |
| `/image/viewerUrl` | 165 occurrences | typed viewer/source locator occurrence, not permission. |
| `/image/evidenceImageUrl` | 2 occurrences | raw/internal typed occurrence, not an image license. |
| `/image/sourceViewerUrl` | 2 occurrences | typed source-viewer occurrence, not remote-display permission. |
| `/image/{state,credit,licenseLabel,displayMode,expectation,parserStatus,placeholderText,routeEvidence,hasImageFrame}` | audited structured fields | raw field literals and baseline classification inputs only. |
| `/rights/{state,label,displayPolicy}` | all bundles | observed wording/raw context; use a rights observation/unknown assessment, never a positive grant. |
| `/images/*` | observed empty secondary-image key set | preserve if present in a future strict parse; it remains an array, never positional-zipped with `/image`. |

The exact baseline is 15,923 bundles: 15,788 with one external visual
reference and 135 `NO_VISUAL_REFERENCE`; 15,790 locator occurrences across
the four roles above, 15,788 distinct lexical values, zero malformed external
locators, zero positive rights evidence, and zero unclassified bundles.

For each reference-bearing bundle:

1. create one provenance-occurrence `rights.external_visual_reference` and a
   `rights.object_visual_reference` in `proposed` state;
2. preserve every locator occurrence in `rights.visual_locator` with
   `visibility='held'` or `internal`; do not use public locator storage;
3. retain raw rights wording as an observation, record an unknown assessment,
   and an unknown provider-policy evaluation with no fabricated provider;
4. create the required fail-closed delivery assessment as `citation_only`
   with an applicable unknown rights assessment and unknown policy evaluation,
   no health qualification, no public locator, and the locked fail-closed
   reason code;
5. add `rights_unknown`, `policy_unknown`, and `unmapped_provider` baseline
   classifications; do not turn an unknown reference into a provider object.

`citation_only` is the correct conservative initial assessment: a
`link_only`, `source_viewer`, or `remote_image` assessment would require an
appropriately healthy qualifying locator under the Phase 2A deferred rules,
which this no-HTTP rehearsal must not invent. For the 135 no-reference
surfaces, insert the explicit `no_visual_reference` classification only; do
not create an empty external-reference row. No representation binary, pixel,
thumbnail, image service, health observation, provider policy version, active
takedown, or `REMOTE_IMAGE` decision is implied.

## Mapping verifier requirements

The implementation should fail before transaction commit unless all of these
are true:

```text
SURFACE_ID_UNIQUE=15923
SOURCE_RECORD_ID_UNIQUE=15923
OBJECT_SOURCE_SEED_LINKS=15923
UNMAPPED_SOURCE_FIELDS=0
SILENTLY_DROPPED_FIELDS=0
SILENT_DELIMITER_SPLITS=0
CROSS_ARRAY_POSITIONAL_ZIPS=0
AUTOMATIC_DEDUPLICATION=0
UNEXPLAINED_MAPPING_DELTAS=0
```

The generated field/occurrence ledger must supply per-pointer type,
cardinality, original array ordinal, presence class, c14n literal hash,
mapping rule ID/version, target kind, public/internal exposure, and
round-trip query. Its full temporary form may remain outside Git, but the
committed generator, schema, aggregates, set hashes, samples, and reproduction
command must be enough to prove it. A full byte-for-byte per-field lexical
slice is not needed when the frozen source asset provides lexical authority;
the source-record c14n bytes, exact JSON Pointer, original structural
projection, and literal hash make the transformation reviewable.

## P0 blocker assessment

No normative identity, cardinality, or state conflict was found in the
evidence reviewed.

The following are **preflight blockers only if the implementation cannot
prove them**, not new DDL decisions:

1. strict Candidate parse does not reproduce the fixed Candidate SHA and
   15,923 unique surface/source IDs;
2. observed JSON paths cannot be matched by the versioned exact-or-raw-only
   mapping registry;
3. candidate folder-side and surface-side membership pair sets differ from
   each other or from the fixed 47,982-pair evidence;
4. a loader attempts to use `edgeLabels[i]` with `edgeIds[i]`, imports a
   legacy graph fact, creates an accepted relation, or promotes a held tier;
5. a visual loader creates a public/pixel locator, `REMOTE_IMAGE`, provider
   permission, or health observation from Candidate strings;
6. the migration role cannot load the canonical input asset with the reserved
   authority kind (the correct response is to use the approved migrator/owner
   path, not the runtime ingestion function).

## Non-blocking implementation recommendations

- Use a preflight-only extractor to emit deterministic staging TSV/JSONL and
  a compact bundle manifest before PostgreSQL connects; record its extractor
  hash and candidate-parse count.
- Insert all canonical tables inside one import transaction after preflight;
  defer constraints only within that transaction and issue `SET CONSTRAINTS
  ALL IMMEDIATE` before commit.
- Keep rows for all 7,928 strict-held objects in `raw.legacy_surface_ledger`
  and the tier/reconciliation ledger; never turn a held row into an absent
  operational object just because it is excluded from the strict corpus.
- Treat source URL, source object key, raw label, Search ID, and locator URL
  as attributes/occurrences only. None is an identity or permission upgrade.
- Bind the batch UUID/name to candidate SHA + mapping version/hash + schema
  normalized SHA + extractor SHA + base commit. Same identity/hash tuple may
  be a no-op; the same batch ID with any differing component must fail.

## Commands executed

All commands used the target worktree and were read-only except creating the
parent directory and this receipt:

```text
git status --short --branch
git rev-parse HEAD
rg --files …
wc -l …
sed -n … database/JSON_MIGRATION_CONTRACT.md MIGRATION_V48_TO_V49.md …
rg -n … database/migrations database/functions docs/audits scripts
jq … docs/audits/v49-rights-machine/06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json
```

No database process, Candidate parse, network access, Node/Next/TypeScript,
browser, Docker, SQLite connection, image request, migration, or production
data write occurred. No task-owned process remains.

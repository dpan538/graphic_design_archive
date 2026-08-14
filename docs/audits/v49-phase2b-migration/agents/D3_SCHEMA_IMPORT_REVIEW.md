# D3 — Schema/import compatibility review

## Assignment and boundary

**Task:** read the Phase 2A physical schema, roles/functions, and the current
Phase 2B mapping/extractor; identify the exact safe insert ordering and any
schema-forward blocker for the staged TSVs.

**Mode:** read-only.  I did not start PostgreSQL, parse Candidate JSON, alter a
frozen asset, alter Phase 2A, or edit Phase 2B implementation files.  This
file is the only file written by D3.

**Result:** `NO_PHASE2A_SCHEMA_FORWARD_MIGRATION_REQUIRED` for the safe
minimal no-release mapping. During this review the primary agent corrected all
three observed extractor defects: it no longer writes live legacy-resolution
rows, it propagates array ordinal, and it uses `node_role='root'` for the
object/TRACE bridge while retaining `node_type='legacy_root'` as descriptive
provenance.

## Evidence read

The review read, in full, the Phase 2A migration chain
`database/migrations/001_foundation.sql` through
`008_final_integrity_closure.sql`; all Phase 2A function files
`001_deferred_constraints.sql` through `015_final_integrity_closure.sql`; the
role grants and API views; `database/PHYSICAL_SCHEMA.md`; the Phase 2A fixture
and tests; and the current Phase 2B `mapping-v1.json`,
`expected-baseline.json`, `README.md`, and `extract.py`.  Relevant normative
cross-checks included `MIGRATION_V48_TO_V49.md`, `DATA_MODEL_V49.md`, and
`docs/architecture/DDL_DECISION_PACK_V49.md`.

The inspected staging writer produces these files: source asset, mapping and
batch, 15,923 source records, entities, objects, surface ledgers, object/source
links, three legacy identities per surface, trace nodes, corpus/version and
eligible memberships, held deltas, visual references/bridges/locators, visual
dispositions/classifications, and temporary field/TRACE/folder/visual ledgers.

## Normative fit

The physical model is compatible with the intended Phase 2B scope:

- `raw.source_asset` permits exactly one
  `canonical_migration_input`; its byte and SHA checks preserve the Candidate
  JSON lexically.  `raw.migration_batch` has a deferred authority trigger, so
  the canonical asset must be inserted first and must carry the exact Candidate
  SHA.
- `raw.source_record`, `raw.legacy_surface_ledger`,
  `core.archive_object`, and `provenance.object_source_record` express the
  required 15,923 raw/object/seed-link rows without a release.
- `research.corpus` / `research.corpus_version` / `corpus_membership` can hold
  only the 7,995 `eligible` rows; the 7,928 held rows belong in
  `raw.fail_closed_delta`, not as accepted research facts.
- `research.trace_node` plus `research.object_trace_node` provide the exact
  object-to-legacy-root crosswalk without creating a semantic relation,
  projection edge, claim, or release.
- `rights.external_visual_reference`, `rights.object_visual_reference`,
  `rights.visual_locator`, and the legacy visual disposition tables accept the
  complete 15,923/15,788/135/15,790 baseline while leaving provider policy,
  rights assessment, delivery assessment, health, takedown, registry release,
  and public pixel locator rows at zero.

This is consistent with the decision pack: a v48 seed has exactly one `root`
node per object (`DDL_DECISION_PACK_V49.md`, Trace object/node identity), and
the Candidate may seed the 15,923 object-to-TRACE-root crosswalk but cannot
promote edges or derived graph facts.  It is also consistent with
`MIGRATION_V48_TO_V49.md`: the 15,923 seed objects link to their unique raw
records and TRACE roots, while derived TRACE edges remain excluded.

## Required transaction / insert order

All imports must use the approved migration path, not runtime ingest functions:
connect as `gda_v49_phase2a_migrator`, begin one transaction, and use its
membership in `gda_v49_phase2a_schema_owner` only for the approved data
migration.  The runtime `raw.register_source_asset` function deliberately
rejects `canonical_migration_input` and therefore cannot be used here.

After strict staging-manifest/hash checks and `COPY` into transaction-local
staging tables, the safe order is:

1. `raw.source_asset` (the single Candidate bytes row), then
   `raw.mapping_version`, then `raw.migration_batch`.
2. `raw.source_record` (all 15,923 exact raw surface bytes and parsed JSONB),
   then `core.entity` (`archive_object` rows).
3. `core.archive_object` with its future
   `created_from_surface_ledger_id`; then `raw.legacy_surface_ledger`.
   The archive-object-to-ledger FK and reciprocal checks are deferred, whereas
   the ledger's FK to the archive object is immediate.  Thus reversing these
   two bulk inserts is invalid.
4. `provenance.object_source_record` (`seed_description`); then
   `core.legacy_identity` for the exact surface/source/TRACE legacy keys.
   Do **not** load the diagnostic `legacy-resolutions.tsv`; see the initial
   blocker and safe remedy below.
5. `research.trace_node`, then `research.object_trace_node` using
   `node_role='root'`, not `legacy_root`.
6. `research.corpus`, `research.corpus_version`, and only the 7,995 eligible
   `research.corpus_membership` rows.  Insert the 7,928 `raw.fail_closed_delta`
   rows after their batch and raw-record parents exist.
7. `rights.external_visual_reference`, then
   `rights.object_visual_reference`, then `rights.visual_locator`; then
   `rights.legacy_visual_surface_disposition` and its classifications.
   No provider, policy version, observation, assessment, health, delivery,
   takedown, visual registry, release, pointer, or public locator is needed.
8. Run the importer parity checks and `SET CONSTRAINTS ALL IMMEDIATE` before
   commit.  A failure at this point must roll back the entire transaction.

This order deliberately leaves `research.semantic_relation`,
`release.trace_projection_edge`, `research.object_relation_membership`,
`rights.delivery_assessment`, and all release/current tables empty.  It does
not use `ON CONFLICT DO NOTHING`, sequences, random UUIDs, or a runtime clock
to establish canonical identity.

## Exact table / FK / trigger hazards

| Area | Constraint that matters | Consequence for loader |
|---|---|---|
| Candidate asset | `raw.source_asset` has byte-length and `sha256(raw_bytes)` checks; `raw.migration_batch` uses the `(source_asset_id, sha256)` composite FK and `migration_batch_authority_exact` deferred trigger. | Decode the exact Candidate bytes, do not reserialize them, and insert source asset before batch. |
| Raw-to-object reciprocal | `raw.legacy_surface_ledger` has immediate FKs to raw record/object; `core.archive_object.created_from_surface_ledger_id` is deferred; `legacy_surface_lineage_exact` and `archive_object_surface_reciprocal` are deferred. | Insert object before ledger, include the same ledger ID on both rows, make source fingerprint equal `raw.source_record.raw_fingerprint`, then validate deferred constraints. |
| Core subtype | `core.enforce_entity_subtype` requires exactly one subtype at deferred validation. | Every staged `core.entity(entity_kind='archive_object')` must have exactly one `core.archive_object`; no bare entity rows. |
| Object/source | `provenance.object_source_record` is keyed `(archive_object_id, source_record_id, source_role)`. | Use exactly one `seed_description` link per seed surface, no accidental de-duplication. |
| Legacy identity | Natural key is `(identity_kind, namespace, legacy_id)`; `legacy_identity_resolution_exact` has stronger lineage/release requirements. | Insert `core.legacy_identity` safely; see below before adding any resolution. |
| TRACE roots | `research.trace_node.entity_id` is a real FK after migration 006; partial unique index applies only where `object_trace_node.node_role='root'`. | Insert trace node after object entity; use exact node key and `root` role to activate the 1:1 root guard. |
| Corpus | Membership FK requires corpus version/object and `membership_disposition` is closed. | Insert only `eligible` members; preserve held tiers as fail-closed delta rather than a corpus member. |
| Visual reference | External reference has `(source_asset_id, source_record_id, pointer, ordinal)` uniqueness; locator has the analogous occurrence uniqueness and SHA-of-UTF8 check. | Preserve URL occurrence and pointer, never URL-deduplicate; exact locator string must hash to staged fingerprint. |
| Proposed visual bridge | `rights.validate_one_object_visual_reference` permits a proposed bridge with no review decision; it rejects an accepted/rejected/superseded bridge lacking an evidence-bound decision. | Stage all bridges as `proposed`, evidence null, with no delivery assessment. |
| Legacy visual typing | `rights.legacy_visual_surface_disposition` is one row per surface ledger and classifications are a closed enum. | Reference-bearing rows need the three typed conservative classifications; 135 no-reference rows need `no_visual_reference`; no unclassified row may be omitted. |
| Public boundary | `api_v1.current_object` reads only a verified sealed research-current release and compatible sealed visual-current release. | A migration rehearsal with no current pointer should return no public release rows; public-boundary positive-object checks need a transaction-scoped fixture followed by rollback. |

## Initial staging blocker: legacy-resolution rows (remediated during review)

The initially inspected extractor emitted three `core.legacy_identity_resolution`
rows per surface (`archive_object`, `source_record`, and `trace_node`) with
`resolution_state='primary'`, typed targets, and no
`decision_evidence_item_id` or `effective_release_id` columns.

That cannot pass the Phase 2A deferred trigger:

- `core.enforce_legacy_identity_resolution()` requires one current typed
  resolution for every inserted primary identity; and
- for every state other than `unresolved` or `withdrawn`, it raises
  `LEGACY_IDENTITY_RESOLUTION_REQUIRES_EVIDENCE_AND_RELEASE` if either the
  evidence or effective release is null.
- `effective_release_id` is a real FK to `release.research_release` (migration
  004).  Inventing a draft/sealed release merely to make the trigger pass would
  blur rehearsal, review, and release semantics and is not a safe workaround.

### Safe minimal no-release remedy

The primary agent adopted this remedy during the review: the current extractor
keeps a diagnostic header but emits no resolution rows. The loader must not
load that empty diagnostic file. Preserve the
47,769 exact legacy identity rows in `core.legacy_identity`, preserve the
surface/source keys in the raw ledger and raw source record, and express the
15,923 TRACE-root crosswalk through the real-FK
`research.object_trace_node` bridge.  This preserves identity and the exact
typed object-to-root mapping without claiming an evidence-reviewed,
release-effective identity resolution.

This is an **implementation adjustment**, not a Phase 2A schema-forward
migration: it avoids an invalid write rather than weakening any constraint or
rewriting history.  A later separately authorized review/release workflow can
create evidence-bound `primary` resolutions.  Do not replace the known
crosswalks with `unresolved` rows; that would discard their deterministic
typed mapping merely to satisfy a constraint.

## Remediations confirmed and remaining receipt conditions

1. **Root-role remediation confirmed.** The extractor now writes
   `node_type='legacy_root'` only as descriptive provenance and writes
   `research.object_trace_node.node_role='root'`. This activates the Phase 2A
   partial unique root guard and matches the normative seed.
2. **Field-array ordinal remediation confirmed.** The initially inspected code
   computed an ordinal but emitted `arrayOrdinal: null`. The current code now
   passes each array's own ordinal to the occurrence ledger. Preserve this
   behavior in verification as the proof that no cross-array positional zip
   occurred.
3. **State folder disposition explicitly.**  The current mapping intentionally
   writes only the temporary 47,982-pair reconciliation ledger.  This is
   technically safe for the no-release rehearsal, and avoids inventing
   accepted provenance assignments, but it differs from the broader model's
   eventual 185-folder/47,982 typed assignment target.  The importer/receipt
   must label it `RECONCILIATION_ONLY_DEFERRED`, report the independently
   recomputed set hash, and create zero canonical folder-assignment rows.  It
   must not imply that a front-end or SQLite asset supplied those pairs.

The folder disposition is a declared deferred mapping decision, not a schema
conflict. The rehearsal receipt should additionally state that the current
tier transformation treats present `null` or an empty string as the same
effective held path as an absent tier, while the occurrence ledger preserves
their distinct `NULL`/`EMPTY_STRING`/`MISSING` presence classes. The frozen
baseline's expected three categories can pass only if it contains no such
additional values; a generic importer should reject them or give them a
separate explicit held disposition rather than reporting them as `MISSING`.

## Negative import cases to exercise

- Insert a ledger before its archive object: immediate FK failure; insert a
  mismatched reciprocal ledger/object pair: deferred lineage failure.
- Insert a duplicate `(source_asset_id, record_ordinal)`, legacy identity, or
  visual locator occurrence: unique violation, never ignore it.
- Attempt the current primary legacy-resolution row: expect the exact deferred
  evidence/release failure; verify full transaction rollback.
- Use `node_role='legacy_root'` in a fixture with two roots for one object:
  demonstrate why it does not activate the intended root unique index; use
  `root` for the production rehearsal.
- Set a visual bridge to `accepted` without decision/evidence, or create a
  delivery assessment from unknown rights: expected constraint failure.
- Attempt any `remote_image`, public-candidate pixel locator, semantic
  relation, TRACE projection edge, release/current pointer, or non-Candidate
  canonical write: expected zero-row / permission / parity failure.

## Conclusion and exit status

`PHASE2A_SCHEMA_CONFLICT=false`.

The Phase 2A schema has the necessary tables, real FKs, deferred checks,
append-only guards, and fail-closed visual path for the requested Phase 2B
rehearsal. The recommended no-release load order above requires no schema
drift. The loader must retain the confirmed remediations, ignore the empty
diagnostic legacy-resolution file, and state its folder/tier deferred
conditions accurately. D3 completed after this record; no process was started
and no further task resource is held.

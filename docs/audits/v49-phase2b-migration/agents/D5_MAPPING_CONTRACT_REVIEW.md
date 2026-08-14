# D5 — Phase 2B mapping and field-coverage contract review

- Task: independent Queue D1 mapping/field-coverage review
- Mode: read-only static review
- Review snapshot: 2026-08-12, while the primary implementation was still moving
- Result: `BLOCKED_FOR_MIGRATION_REHEARSAL_VERIFIED_PENDING_P0_REMEDIATION`

## Boundary and status

This review inspected the current Phase 2B extractor, staging/import loader,
verifier, mapping registry, and the Phase 1C/1D/2A normative materials.  It
did **not** start or connect to PostgreSQL, open or parse the frozen Candidate
JSON, open SQLite, contact a network service, alter a schema migration, alter
a frozen receipt, or touch the protected main worktree.  The only file written
by this review is this record.

The implementation directory was untracked and being actively assembled at
the time of review.  Findings below are therefore a precise static snapshot,
not a claim about a later remediation.  A fresh D6/final verifier must rerun
the cited checks after the implementation is settled.

## Normative reading used

The review read the relevant current contracts and receipts, including:

- `ARCHITECTURE.md` (raw-byte/literal authority and provenance links);
- `DATA_MODEL_V49.md` (the independent `raw.field_literal` identity and
  raw/core/research/rights boundaries);
- `MIGRATION_V48_TO_V49.md` (sole Candidate input, literal preservation,
  zero TRACE import, and Phase 1D sequence/set-hash reproduction);
- `READ_API_V1.md`, `ACCEPTANCE_GATES.md`, and all current ADRs;
- `docs/architecture/DDL_DECISION_PACK_V49.md`, especially §§3.4 and 7
  (folder natural key, source-record-to-field-literal cardinality, typed
  assignment boundary);
- Phase 1C authority/research receipts and Phase 1D rights/machine receipts,
  including `06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`; and
- the Phase 2A physical schema, raw/core/research/rights functions, role
  boundary, manifest, and gate receipt.

These sources are consistent on the central Phase 2B policy: Candidate JSON
is the only population input; SQLite/Search/TRACE/transfer assets can only
reconcile; raw values and unresolved states must remain accountable; no
legacy graph fact becomes a canonical semantic relation; zero positive rights
and zero accepted TRACE are valid.

## Positive controls observed

- `mapping-v1.json` has 12 declared rules and each rule has the required
  mapping-contract properties.
- `extract.py` uses strict UTF-8 decoding, duplicate-key rejection,
  non-finite-number rejection, deterministic key-sorted semantic digests,
  source-order arrays, and UUIDv5 identities.
- The current importer consumes a manifest bound to Candidate SHA, mapping
  SHA, extractor SHA, base commit, and normalized schema SHA.  It contains no
  SQLite/Search/TRACE population writer and does not use `ON CONFLICT DO
  NOTHING`.
- Root-level raw/reconciliation occurrences and the dual-sided 47,982 folder
  pair-set check are present.  The controlled runner now exists and passes
  shell syntax validation; it refuses cluster/database creation itself.

Those controls do not cure the open contract failures below.

## P0 findings

### D5-P0-01 — surface field pointers do not resolve against their declared raw record

`extract.py` emits every surface occurrence with:

```text
raw.source_record.raw_value#/surfaces/<ordinal><relativePointer>
```

at lines 529–541.  The corresponding `raw.source_record.raw_value` written at
line 640 is the individual surface object, not the Candidate root object.  A
pointer such as `#/surfaces/42/title` therefore cannot resolve against that
record.  This breaks the promised exact-value/provenance round trip even
though the raw source record itself exists.

**Required remedy:** use the raw-record-relative pointer
`raw.source_record.raw_value#<relativePointer>` or use the full Candidate
asset location `raw.source_asset.raw_bytes#/surfaces/<ordinal><relative>`.
Keep both the full Candidate `jsonPointer` and the record-relative pointer
explicitly, and validate resolution/digest correspondence in the staged-ledger
test.

### D5-P0-02 — emitted folder mapping rule is not declared, and raw-only flags disagree with the registry

`path_rule()` in `extract.py` returns
`folder-membership-assignment` for `/folders/*` (line 227).  The registry
declares `folder-membership-reconciliation`, not that ID.  A static
declared-versus-returned check produced:

```text
undeclared_returns=['folder-membership-assignment']
unreachable_declared=['folder-membership-reconciliation', 'top-level-reconciliation-raw']
```

(`top-level-reconciliation-raw` is intentionally emitted by a separate root
function; the folder mismatch is not intentional.)  As a result, emitted
occurrences can claim `UNMAPPED_SOURCE_FIELDS=0` while carrying a rule ID with
no reviewed policy.

There is a second inconsistency at line 539: the ledger sets
`rawSnapshotOnly` true only for `recursive-raw-snapshot-only`.  The mapping
registry also marks `trace-arrays-held-no-zip` and
`folder-membership-reconciliation` raw-snapshot-only.  TRACE array occurrences
are consequently emitted with an incorrect false flag.

**Required remedy:** select the rule from one validated registry lookup;
derive `rawSnapshotOnly` from that rule metadata; reject any emitted rule not
in the registry; and derive coverage/mapping-delta metrics from that check
rather than hard-coded zeroes.  Add an adversarial staged occurrence with an
undeclared rule/pointer so the rejection is demonstrated rather than merely
raised by an option before validation.

### D5-P0-03 — parsed records have no durable `raw.field_literal` rows

The extractor creates a temporary `field-occurrence-ledger.jsonl`, but no
`field-literals.tsv`; `prepare-staging.sql`, `import.py`'s allowlist, and
`load.sql` contain no staging/load path for `raw.field_literal`.  The load
therefore leaves every successfully parsed `raw.source_record` with zero
durable field literals.

This conflicts with the Phase 2A physical-model decision in
`DDL_DECISION_PACK_V49.md`: source record → field literal is 1:N and a source
record can have zero literals only when parsing failed with a workflow
exception.  Here parsing succeeds for the intended 15,923 records.  It also
falls short of the Phase 2B requirement that every present occurrence retain
its exact value, type, pointer, presence, ordinal, and digest.

The user permits the *full occurrence ledger* to remain temporary when its
generator/schema/hash/sample/reproduction/deletion evidence is committed.  It
does not remove the normative durable raw-literal link.

**Required remedy:** stage and append deterministic `raw.field_literal` rows
for present occurrences, with source record FK, RFC 6901 pointer, occurrence
ordinal, and a raw value representation linked back to the immutable lexical
source record.  Retain missing paths only in the occurrence ledger (do not
invent a literal).  The held-tier delta should reference the tier literal when
one exists; an actually missing tier may retain a null literal FK plus the
explicit missing occurrence.  Verify no parsed source record has zero field
literals and retain the ledger hash/row-count/deletion receipt.

## High-risk proof/receipt gaps (P1 until a final gate claims success)

### D5-P1-01 — no Phase 2B reconciliation implementation for non-population assets

`expected-baseline.json` pins SQLite, transfer-manifest, TRACE-manifest and
Search/graph metrics, but the reviewed Phase 2B directory has no read-only
reconciliation generator/verifier for them.  The task requires a derived
reconciliation ledger and a fresh report of SQLite/Search/TRACE/raw/rights
metrics, including the Search set relation and the zero canonical
write/backfill proof.  Reusing Phase 1 receipts or hard-coded numbers is not
a fresh Phase 2B recomputation.

Add a read-only reconciler (SQLite only with `mode=ro&immutable=1`) or an
equally reproducible explicitly invoked existing verifier.  It must write no
canonical rows and record `canonical_rows_created=0` and
`fields_backfilled=0` for every non-Candidate authority source.

### D5-P1-02 — visual parity is count-only, not the committed sequence/set proof

Phase 1D requires migration to reproduce committed visual sequence/set hashes,
not merely `15788/135/15790` counts.  The reviewed extractor and verifier
compute aggregate visual counts and local staging hashes but do not recompute
and compare the Phase 1D surface ordinal/ID sequence, raw visual-bundle
sequence, locator-occurrence sequence, locator-value set, and classified
surface sequence hashes.  Count parity can conceal changed occurrence order
or substituted values.

Add comparison against the frozen Phase 1D summary/hash contract, with a
receipt that distinguishes occurrence count from distinct URL value count and
continues to report zero positive-rights promotion and zero public pixels.

### D5-P1-03 — folder mapping scope must be explicit, not silently described as final normalization

The current mapping deliberately emits the independently checked 47,982
Candidate folder pairs only to a temporary reconciliation ledger.  That is a
safe no-release rehearsal route under the Phase 2B wording, but the broader
DDL decision pack describes 185 folders and 47,982 assignments as the
eventual typed target.  This is a scope/deferred-decision issue rather than a
reason to amend Phase 2A DDL.

The final receipt must say `RECONCILIATION_ONLY_DEFERRED`, prove the two
Candidate sides and set hash, report zero canonical folder-assignment rows,
and avoid claiming the temporary ledger is the final membership migration.
If the authorized scope instead requires durable assignments now, they need a
reviewed evidence/assignment path rather than a silent direct promotion.

### D5-P1-04 — full occurrence-ledger retention evidence remains to be produced

The staged JSONL file/hash is a promising generator output, but the final
audits must record its schema, row count, byte size, SHA-256, representative
samples, reproduction command, and verified deletion from the isolated
temporary location.  The imported database content hash should cover durable
field literals and relevant raw record fingerprints without treating a
runtime staging path as a canonical identity.

## Commands and static evidence

All commands below operated in the target worktree and only read files:

```text
git status --short
rg --files database/data-migrations/v48-to-v49 docs/audits/v49-phase2b-migration/agents | sort
sed -n / nl -ba on mapping-v1.json, extract.py, import.py, load.sql,
  prepare-staging.sql, prepare-runtime.sql, verify.py, and run-rehearsal.sh
rg -n -C 8 'field_literal|folder_membership|rawSnapshotOnly|exactRawValueLocation|reconcil'
  database/data-migrations/v48-to-v49 database/migrations database/functions
  docs/architecture/DDL_DECISION_PACK_V49.md DATA_MODEL_V49.md
python3 -c '<AST/static mapping rule declared-versus-returned check>'
sh -n database/data-migrations/v48-to-v49/run-rehearsal.sh
python3 -c '<mapping required-property check; ast.parse extractor/importer/verifier>'
```

Static results:

```text
MAPPING_RULE_COUNT=12
MAPPING_REQUIRED_PROPERTIES_MISSING=0
PYTHON_AST_PARSE=PASS
RUNNER_SHELL_SYNTAX=PASS
EMITTED_UNDECLARED_MAPPING_RULE=folder-membership-assignment
RAW_FIELD_LITERAL_STAGING_PATH=ABSENT
POSTGRES_STARTED=false
POSTGRES_CONNECTED=false
CANDIDATE_PARSED=false
SQLITE_OPENED=false
FROZEN_DOCUMENTS_MODIFIED=false
```

## Exit condition for this review

`D5_STATUS=BLOCKED_PENDING_P0_REMEDIATION` at the static snapshot.  Do not
claim `MIGRATION_REHEARSAL_VERIFIED` until D5-P0-01 through D5-P0-03 are
fixed and exercised in two fresh replays, and the P1 reconciliation/visual
proofs are present in the Phase 2B receipts.  This review itself performed no
population and asserts no production or persistent-database state.

## POST_REMEDIATION_STATIC_REREAD — 2026-08-12

This is a deliberately narrow reread of the three former D5 P0 findings.  It
read only the current `extract.py`, `mapping-v1.json`, field-occurrence schema,
`README.md`, `prepare-staging.sql`, `load.sql`, and `import.py`; it did not
parse Candidate JSON, open SQLite, start or connect PostgreSQL, or modify the
migration implementation.  The extractor was treated as the frozen running
snapshot requested by the coordinator.

`POST_REMEDIATION_D5_P0_REMAINING=0`

| Former D5 P0 | Current static evidence | Result |
| --- | --- | --- |
| D5-P0-01: source-record pointer was rooted at a nonexistent `/surfaces/<ordinal>` child | `extract.py` now emits `raw.source_record.raw_value#{relative_pointer}`.  `import.py` preflight rejects any occurrence whose exact raw location does not equal that source-record-relative form. | Cleared at static-review level. |
| D5-P0-02: folder rule was undeclared and `rawSnapshotOnly` was inconsistent | `mapping-v1.json` declares `folder-membership-assignment`, with target `research.folder;provenance.canonical_assignment;provenance.assignment_folder_membership` and `rawSnapshotOnly: false`.  `extract.py` returns that declared rule for `/folders/*`, obtains the flag from the registry rather than hard-coding it, and rejects an emitted rule absent from the registry; `import.py` rechecks both rule declaration and flag equality.  The static declared-versus-returned rule check reported no undeclared return values. | Cleared at static-review level. |
| D5-P0-03: field occurrences had no durable `raw.field_literal` path and folder memberships were not typed proposed assignments | The occurrence schema requires `fieldLiteralId`.  For each present scalar or JSON null occurrence, `extract.py` produces one deterministic field-literal identity keyed by source record, relative pointer, and occurrence ordinal, with canonical raw bytes; `import.py` requires an exact paired TSV row and validates ID, byte hash, pointer, ordinal, mapping rule, and count.  `prepare-staging.sql` and `load.sql` stage and insert those rows into `raw.field_literal`, whose source-record FK and `(source_record_id, json_pointer, occurrence_ordinal)` uniqueness preserve pairing.  Containers remain recoverable from the exact parent raw source record, while missing values remain occurrence-ledger facts rather than invented literals.  For folders, the extractor independently compares the two Candidate-side pair sets, fails on a missing object crosswalk, emits deterministic folder and assignment IDs, and assigns `status=proposed`; the loader inserts into `research.folder`, `provenance.canonical_assignment`, and the direct `provenance.assignment_folder_membership` subtype. | Cleared at static-review level. |

The existing Phase 2A assignment validator requires supporting evidence only
for `accepted` assignments, so the explicitly `proposed` folder assignments do
not fabricate acceptance or evidence.  The 47,982-folder-pair assertion and
the corresponding staged/loaded count paths are present in the current static
implementation.

No remaining D5 P0 was found in this focused reread.  This supersedes the
earlier P0 exit condition only for the reviewed implementation snapshot; the
Phase 2B final gate still needs its separate fresh-replay and database-backed
evidence.

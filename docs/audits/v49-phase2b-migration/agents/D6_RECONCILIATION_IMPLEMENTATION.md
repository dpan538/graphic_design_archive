# D6 — Read-only reconciliation implementation record

## Scope and exit status

- Task: implement the Phase 2B reconciliation CLI only.
- Files written: `database/data-migrations/v48-to-v49/reconcile.py` and this record.
- PostgreSQL started: **no**.
- Candidate JSON parsed by this task: **no**.
- SQLite opened by this task: **no**.
- Network, frontend, frozen assets, Phase 2A DDL, and existing Phase 2B files modified: **no**.
- Exit status: `IMPLEMENTED_STATICALLY_NOT_EXECUTED`.

## Implemented boundary

`reconcile.py` is standard-library-only and has no PostgreSQL dependency or
output-file option. Its normal invocation will emit one JSON receipt to stdout
and return non-zero on any failed assertion.

It requires all of the following explicit inputs:

```sh
python3 database/data-migrations/v48-to-v49/reconcile.py \
  --repo-root /Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform \
  --surface-ledger /private/tmp/gda_v49_phase2b_stage/staging/surface-row-ledger.tsv \
  --stage-manifest /private/tmp/gda_v49_phase2b_stage/staging/staging-manifest.json
```

`--visual-hashes <json>` is the mutually exclusive alternative to
`--stage-manifest`. The selected JSON must contain all seven exact Phase 1D
visual-parity hash keys; ambiguous or absent keys fail closed.

The tool uses the supplied surface ledger rather than reopening the Candidate
JSON. The only Candidate operation is a streaming SHA-256/byte-count check.
It requires exactly these ledger columns and rejects count, ordinal, duplicate,
empty-ID, ragged-row, and header failures:

```text
source_ordinal
surface_id_exact
```

## Read-only evidence and classifications

| Artifact / product | Validation | Authority class | Canonical output from this CLI |
| --- | --- | --- | --- |
| Candidate JSON | frozen bytes/SHA-256 only | sole population input, but not parsed here | 0 |
| v48 SQLite | fixed `file:...?...mode=ro&immutable=1`, then `PRAGMA query_only=ON`, integrity and fixed SELECTs | reconciliation only | 0 |
| transfer JSON/CSV | frozen bytes/SHA-256; JSON declared-file/byte totals | integrity only | 0 |
| TRACE manifest / graph audit | frozen manifest bytes/SHA-256, manifest metrics and historical graph reconciliation metrics | legacy-product reconciliation only | 0 |
| Search index | recomputed ID set comparison against supplied ledger | derived reconciliation only | 0 |
| Phase 1D visual hashes | supplied stage/JSON comparison with seven locked values | visual parity reconciliation only | 0 |

The JSON receipt binds the explicit non-write proof:

```text
CANONICAL_POPULATION_INPUT_ARTIFACTS=1
CANONICAL_ROWS_CREATED=0
FIELDS_BACKFILLED=0
SQLITE_CANONICAL_WRITES=0
SEARCH_IMPORTED_ROWS=0
SEARCH_ONLY_CANONICAL_INSERTS=0
TRACE_IMPORTED_CANONICAL_ROWS=0
LEGACY_GRAPH_EDGES_IMPORTED=0
RIGHTS_AUDIT_PERMISSION_UPGRADES=0
```

The code has no PostgreSQL import/client and accepts no output path. SQLite is
the only database connection and is URI-read-only plus `query_only`; all other
operations are local file reads followed by stdout JSON serialization.

## Reused authoritative measurements

The tool directly follows the fixed read-only queries and Search schema access
used by `scripts/verify_v49_authority_research_delta.py`. It compares the
historical graph-audit metrics from
`docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json`
without treating that audit as row-creation authority. The seven locked visual
hashes are the Phase 1D values from `scripts/verify_v49_rights_machine.py`.

It validates these reconciliation measurements rather than importing them:

```text
SEARCH_IDS=8636
CANONICAL_IDS=15923
INTERSECTION=2585
SEARCH_ONLY=6051
CANONICAL_ONLY=13338
UNION=21974
LEGACY_GRAPH_EDGES_RECONCILED=255695
LEGACY_MEMBERSHIPS_RECONCILED=126822
TRACE_SHARDS=576
TRACE_ASSETS_EXCLUDING_MANIFEST=580
```

## Static checks performed

No reconciliation invocation was run. The implementation was inspected by
parsing its source with Python `ast.parse` and by checking the Git diff for
whitespace errors. These checks exercise neither Candidate parsing nor SQLite
opening. The controller must run the actual command once final staging includes
the visual-parity hash block, then preserve its JSON stdout in the Phase 2B
receipt generator.

## Limitations / handoff conditions

1. The extractor stage manifest must expose all seven Phase 1D visual parity
   hashes exactly. This tool deliberately does not recompute them from the
   Candidate JSON, so it does not create a second Candidate parser.
2. The full SQLite integrity check is intentionally retained for the final
   run. It can be slow but does not alter the immutable database.
3. The tool reports only reconciliation/integrity observations. It cannot
   attest to PostgreSQL row creation; `import.py`/`verify.py` and the replay
   harness remain responsible for population parity, transaction rollback, and
   public-boundary tests.
4. The final controller must record the exact command, output SHA-256, SQLite
   URI, and whether the external staging bundle was deleted after receipt
   generation.

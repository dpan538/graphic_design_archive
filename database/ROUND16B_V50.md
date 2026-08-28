# Round 16B v50 PostgreSQL research contract

This forward-only layer adds first-class pair and higher-order Exploration
associations after the complete frozen v49 replay. It is a research-schema
capability only: it imports no Round 16B production facts, activates no product
record, mutates no v49 object, deploys nothing, and does not alter `/api/v1`.

## Additive sequence

1. `migrations/014_exploration_v3_higher_order_associations.sql`
2. `functions/020_exploration_v3_integrity.sql`
3. `views/003_exploration_v3_read_contract.sql`
4. `roles/008_exploration_v3_grants.sql`

The replay driver verifies the SHA-256 of the freeze manifest, its checksum
ledger, every one of its 126 file hashes, and each frozen sequence array. It
then derives the 40-file database replay prefix directly from those verified
arrays before applying the four manifest-governed additive files. Cluster
roles are still initialized once with the separately verified frozen
`roles/001_cluster_roles.sql`; no new login role is introduced. Replay uses a
static preflight because the execution receipt is necessarily finalized only
after both fresh runs. The final verifier resolves every receipt command ID
against the governed command ledger, metadata, and hash-bound stdout; requires
the exact replay/test/race/residue/schema-hash markers; and then requires two
distinct passing database names, zero fixture residue, and one identical
normalized schema hash.

## Isolated replay

Use a fresh database whose name begins `gda_v50_round16b_`, a dedicated Unix
socket, and a non-default port:

```sh
PGHOST=/absolute/disposable/socket \
PGPORT=59417 \
PGDATABASE=gda_v50_round16b_contract \
GDA_PSQL=/absolute/path/to/psql \
database/scripts/replay_v50_round16b.sh
```

Then run the transaction-scoped adversarial suite:

```sh
PGHOST=/absolute/disposable/socket \
PGPORT=59417 \
PGDATABASE=gda_v50_round16b_contract \
GDA_PSQL=/absolute/path/to/psql \
database/scripts/run_v50_round16b_tests.sh
```

The test must report the SQL-suite marker, both real concurrency schedules,
both unsupported-isolation guards, disposal of the dedicated race database,
and the final contract marker, including
`V50_EXPLORATION_V3_HIGHER_ORDER_ASSOCIATION_TESTS=PASS` and
`V50_ROUND16B_CONTRACT_TESTS=PASS SEAL_RACE_MATRIX=PASS
ISOLATION_GUARDS=PASS FIXTURE_RESIDUE=0`.

## Fail-closed facts

- A higher-order association always carries `pair_projection_policy=NONE`.
- Stable association identity is the exact Checkpoint 008 compact-JCS
  projection over association kind, canonical participants, immutable bounded
  scope identity, order semantics, and meaningful-role policy. Successor
  revisions must retain that identity and form one non-forking chain. API and
  product gates expose only the unsuperseded head.
- `scope_context_qualifications` is a complete association-revision snapshot:
  revision one equals the source governed scope, while a qualification-only
  successor may change the snapshot and aggregate semantic content without
  changing the stable association ID. The revision-specific snapshot is
  exposed with the active association; immutable `active_scope` remains the
  identity-bearing scope surface.
- Explicit internal-pair links reference already governed pair revisions and
  never create pair rows.
- Active revisions require exact incidence arity, bounded senses, locator-
  bearing evidence, final authority and review, global coherence, resolved
  conflict and uncertainty, and support-mode/disposition parity.
- Active concepts and bounded senses independently require association
  eligibility and final authority, including when no association references
  them; production vocabulary authority can never be synthetic.
- Evidence, bounded-sense, association-revision, composition-revision,
  navigation-state, workflow, and export aggregates are explicitly sealed
  after their child sets are complete. A seal stores the compact-JCS SHA-256
  of the complete canonical parent-and-child aggregate, with UTC timestamp
  normalization and C-ordered membership. Seal and child INSERT triggers take
  the same fail-fast advisory lock and parent-row lock at READ COMMITTED;
  concurrent membership loses with `40001`, post-seal membership loses with
  `55000`, and REPEATABLE READ or SERIALIZABLE membership writes lose with
  `25000`. Post-seal correction requires a new governed revision.
- A higher-order realization covers its complete incidence set and cannot be
  a pair edge.
- A `COHERENT` composition review always has exact final/pass gate parity,
  whether or not the composition is product eligible. Navigation paths are
  continuous and end at the declared focus node.
- Product transitions, workflows, and exports cannot outrun their governed
  association and composition dependencies; transition association traces are
  either complete and exact or absent. Workflow revision/realization sets are
  exact for every state composition and `reachable` is recomputed from the
  stored graph; exports preserve that exact realization set and policy.
- `api_v3` is a production-only positive allowlist and is empty for the
  committed synthetic contract controls. Its allowlisted scope surface covers
  both association scopes and exact participant scopes without exposing source
  notes, retained bytes, or raw-source identities. Navigation nodes/path steps,
  workflow states/revisions/realizations/transitions, and export-preservation
  rows are exposed only through positive parent allowlists.
- The adversarial suite also constructs a complete transaction-local
  production-positive chain and compares exact ordered row/relationship sets
  through every API view. An inactive association successor must dynamically
  remove the superseded association and every dependent composition,
  navigation, transition, workflow, export, and child-trace surface.

See `database/schema-manifest-v50-round16b.json` for the exact additive file
inventory and `docs/adr/0006-v50-exploration-v3-database-contract.md` for the
decision boundary. Execution-only PostgreSQL version, replay identities,
fixture residue, command IDs, and normalized schema evidence live in the
manifest-bound `v50-round16b-replay-receipt-checkpoint011.json`.

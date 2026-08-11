# v49 Phase 2A — Fresh replay receipt

## Isolation

- PostgreSQL: Homebrew PostgreSQL `16.13`
- cluster: `/private/tmp/gda_v49_phase2a.bCIwb6/cluster`
- socket: `/private/tmp/gda_v49_phase2a.bCIwb6/socket`
- port: `58649`
- external listen: disabled
- system/default port `5432`: never contacted
- final databases: `gda_v49_phase2a_final1`,
  `gda_v49_phase2a_final2`

## Procedure

For each database, `database/scripts/replay.sh` created the empty schema and
roles in the versioned order, followed by `database/scripts/run_tests.sh`.
Tests ran inside rollback-only fixture transactions. `schema_hash.sh` then
performed a schema-only dump and deterministic normalization.

## Results

| Replay | Suite result | Project rows after tests | Fixture residue | Log SHA-256 |
|---|---|---:|---:|---|
| final1 | PASS | 0 | 0 | `d02e97d6787b620843c663ab6bdcd9d83a7668e6fe1eabcca726fec0c40dcb80` |
| final2 | PASS | 0 | 0 | `dc7fe9aa97402d796593f9d070dbe597883e5f742223bb6d2322f45f009e5b64` |

Both logs terminate with:

```text
CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0
```

`FRESH_REPLAY_COUNT=2`

`FRESH_DATABASE_REPLAY=true`

`PRODUCTION_ROW_COUNT=0`

`TEST_FIXTURE_RESIDUE=0`

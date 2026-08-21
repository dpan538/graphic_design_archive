# Frozen PostgreSQL v49

The v49 PostgreSQL implementation, canonical release inputs, release/API contracts, and expected output fingerprints are frozen. `database/FREEZE_V49.json` enumerates each frozen file and SHA-256; `scripts/repository/verify_v49_database_freeze.py` verifies it without modifying data.

Frozen facts:

- Schema SHA-256: `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`
- Release projection digest: `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`
- Canonical Candidate JSON SHA-256: `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`
- Objects / assignments: 15,923 / 47,982
- Eligible / held: 7,995 / 7,928
- Accepted TRACE / positive rights: 0 / 0
- Source release anchor: `v49-data-api-closure-20260821`

Do not edit a frozen file in place. Legal database development must set `database/VERSION` to 50 or later, add a new forward-only migration or versioned object, leave all manifest-listed v49 hashes unchanged, and add a v50 ADR. Frontend design may not modify `database/**` or canonical release inputs. API adapters must conform to the frozen read contract.


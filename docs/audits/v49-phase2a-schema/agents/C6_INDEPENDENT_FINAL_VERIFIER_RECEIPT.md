# v49 Phase 2A — C6 independent final verifier receipt

## Verdict

`C6_STATUS=PASS`

`C6_FAILURE_COUNT=0`

C6 did not participate in schema design, SQL authoring, migration replay,
fixture execution, catalog export, or C1–C5 review. This verification was
limited to the frozen implementation, provisional audit package, retained
replay evidence, read-only catalogs in the two final disposable databases,
and Git scope. C6 wrote only this receipt.

The package presented to C6 deliberately had
`status=PENDING_INDEPENDENT_FINAL_VERIFIER`,
`gateAssertions.independentFinalVerifier=false`, and no C6 entry in its
provisional manifest/checksum set. That is the expected self-reference
boundary: the controller must add this receipt, update the pending C6/process
fields, and regenerate the final manifest/checksum set after this PASS. C6
made no edit to those controller-owned files.

## 1. Frozen package and implementation identity

The first provisional package was explicitly withdrawn by the controller
after it found a hand-transcription error in the digest for
`database/scripts/verify_historical_audit.py`. C6 had not signed that package.
After the `REFROZEN_MANIFEST` signal, C6 discarded all earlier package
conclusions and recomputed the following from the new bytes:

| Evidence | Independently observed |
|---|---|
| Phase2A provisional `MANIFEST.json` SHA-256 | `3dd10625219e98f4d8037f2f8f0ec80a40c858678d2ca20cbb2f3609e3ef3dee` |
| `database/schema-manifest.json` SHA-256 | `dcad48a38b66b9f42f19a3a2b78fcca2c3610182b2704f61dcdc5b3a0a7530ea` |
| Provisional `CHECKSUMS.sha256` SHA-256 | `a4c9f1c32185a8b1ecc893c18c3df4cdce53733b88c33497bb33c3fb0c27a001` |
| Initial base commit | `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d` |
| Physical-schema commit | `9f3c20dc84212b40b0e29f85a93d96fc3b9da476` |
| Test/verification HEAD read by C6 | `7f4838401b420f71bc76d8478ed2a454b4b20d78` |
| Branch | `refactor/v49-data-platform` |

All 21 provisional checksum entries verified. They are sorted and unique,
cover 20 audit artifacts plus `MANIFEST.json`, exclude `CHECKSUMS.sha256`
itself, and intentionally exclude C6. Independent manifest traversal found:

```text
IMPLEMENTATION_ARTIFACTS=42
AUDIT_ARTIFACTS_PRE_C6=20
INPUT_PACKAGES=3
MISSING_ARTIFACTS=0
DIGEST_MISMATCHES=0
```

The refrozen manifest contains the corrected verifier-runner digest
`8eec31661574ddc6e846617cc9d6d906561858861221be836c1dd85d2c24a342`.

### Historical inputs

The current Phase 1C, rights/machine, and Phase 1D manifest/checksum file
digests exactly match the three `inputPackages` entries. The baseline-aware
historical verifier also passed against the immutable Git blobs rather than
conflating later normative edits with historical evidence:

| Input package | Historical base | Entries checked | Result |
|---|---|---:|---|
| authority/research delta | `967cbe34a8f30f8e74fa117e1bdee74644f71afe` | 28 | PASS |
| rights/machine | `f75ded85000749beb4735fbbddcce99e9395b0b2` | 32 | PASS |
| Phase 1D final | `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d` | 3 | PASS |

A naive current-tree `shasum -c` of Phase 1C reports the three normative files
that were legitimately changed after its historical freeze. That result is
not used as a gate. The new runner proved the pinned historical blobs and
recorded both the historical baseline and current implementation identity.

## 2. Stable5 and deterministic schema evidence

`database/schema-manifest.json` contains 37 sorted, unique Stable5 entries.
C6 recomputed every member digest, recreated the exact two-space checksum
serialization, and compared it byte-for-byte with the retained Stable5 list.

```text
STABLE5_FILE_COUNT=37
STABLE5_MEMBER_HASHES_MATCH=true
STABLE5_LIST_BYTE_IDENTICAL=true
STABLE5_LIST_SHA256=23d2e588c78de7a6756d5fe57117bb972dde453ba44c7b9eb3b4a9373d6f4473
```

Retained replay evidence independently verified as follows:

| Evidence | final1 | final2 |
|---|---|---|
| Replay/test log bytes | 10,977 | 10,977 |
| Replay/test log SHA-256 | `d02e97d6787b620843c663ab6bdcd9d83a7668e6fe1eabcca726fec0c40dcb80` | `dc7fe9aa97402d796593f9d070dbe597883e5f742223bb6d2322f45f009e5b64` |
| Raw schema dump bytes | 946,983 | 946,983 |
| Raw schema dump SHA-256 | `24cb8faf12dc9f1db535f25c5f9860263052b885b5c2465ad345596ee8639499` | `b2c7247aff01ad0529de15d89594dee4a9842a608ab963437c227de84156c348` |
| Normalized schema bytes | 738,816 | 738,816 |
| Normalized SHA-256 | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` |

The two normalized files are byte-identical. Both log files end with:

```text
CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0
```

## 3. Machine-readable TSV verification

C6 performed an independent strict standard-library parse. The controller's
separate artifact-tool import evidence was not repeated: it observed sheet
dimensions `3934x18`, `2963x28`, `15486x19`, and `40x22`, including headers.

For every TSV, C6 verified UTF-8 without BOM, LF-only bytes, a terminal LF,
no blank lines, the exact closed header and width, the expected data-row
count, sorted and unique primary keys, lowercase booleans, replay equality,
and row `PASS` status. Definition hashes, test-file hashes, referenced line
numbers, and named negative-oracle markers were also reconciled.

| Artifact | Data rows | Columns | SHA-256 | Result |
|---|---:|---:|---|---|
| `01_SCHEMA_OBJECT_INVENTORY.tsv` | 3,933 | 18 | `960e9d92ddde321e46ef3c6962fdb6aef9bc862ccbd5a4deff1612a7ddca14c4` | PASS |
| `02_TABLE_CONSTRAINT_MATRIX.tsv` | 2,962 | 28 | `f0a53125ff2dc11625e6b71f99d78e40b506d8333359dfa10121b0972674433c` | PASS |
| `03_ROLE_GRANT_MATRIX.tsv` | 15,485 | 19 | `b55a42b6df5148e9a506ad9c2c956aae6cd7703884701f509ebe5d3807c93b9a` | PASS |
| `05_NEGATIVE_TEST_REGISTER.tsv` | 39 | 22 | `de8cad93900ac74504ba99c1bf8190d2d9a8929a7210f5ebfa83c36bb0de77d6` | PASS |

`actual_direct=\\N` is valid and distinct from a boolean for role-attribute
rows where direct object ACL semantics do not apply; effective and expected
values remain closed booleans.

## 4. Read-only final-database catalog verification

C6 connected only to the task-owned PostgreSQL 16.13 cluster at:

```text
socket=/private/tmp/gda_v49_phase2a.bCIwb6/socket
port=58649
databases=gda_v49_phase2a_final1,gda_v49_phase2a_final2
```

Every successful psql sequence used `BEGIN READ ONLY`, fixed the verification
search path to `pg_catalog`, and ended with `COMMIT`. C6 did not connect to
5432, issue DDL/DML, create a temporary object, rerun a migration/test, or
start a PostgreSQL process. Both databases returned the same catalog and
data-boundary result:

| Check | final1 | final2 |
|---|---:|---:|
| Project schemas | 9 | 9 |
| Base/partitioned tables | 223 | 223 |
| Views/materialized views | 15 | 15 |
| Installed project functions | 183 | 183 |
| Constraints (including 3 domains) | 1,200 | 1,200 |
| User triggers | 335 | 335 |
| Indexes | 465 | 465 |
| Project roles | 7 | 7 |
| Exact rows across all 223 project base tables | 0 | 0 |
| Accepted semantic relations | 0 | 0 |
| `remote_image` delivery assessments | 0 | 0 |

`listen_addresses` is empty and `inet_server_addr()` is null in both sessions.

### Role, PUBLIC, and machine boundary

Both databases independently returned:

```text
RUNTIME_PRIVILEGED_ATTRIBUTES=0
SCHEMA_OWNER_NOLOGIN=true
RUNTIME_LOGIN_ROLES=6
PUBLIC_DATABASE_PRIVILEGES=0
PUBLIC_SCHEMA_PRIVILEGED=0
PUBLIC_RELATION_PRIVILEGED=0
PUBLIC_SEQUENCE_PRIVILEGED=0
PUBLIC_FUNCTION_EXECUTE=0
API_READER_BASE_TABLE_SELECT=0
API_READER_ANY_WRITE=0
API_READER_API_VIEWS=3
API_READER_RAW_SCHEMA_USAGE=false
API_READER_RIGHTS_LOCATOR_SELECT=false
API_READER_RELEASE_PUBLIC_LOCATOR_SELECT=false
```

The Stable5 SQL contains 83 `SECURITY DEFINER` declarations. Because later
`CREATE OR REPLACE FUNCTION` statements deliberately replace earlier
definitions, the final live catalog contains 66 distinct security-definer
functions. Every live definition has exact `search_path=pg_catalog`; zero are
unpinned, and the catalog source scan found zero dynamic `EXECUTE` tokens.
Some functions additionally fix `TimeZone=UTC`.

An initial C6 diagnostic incorrectly counted the six intentional login roles
as unsafe and only accepted `search_path=pg_catalog,pg_temp`. Those two
diagnostic labels were discarded. A focused read-only query corrected the
predicate to the locked role matrix and exact `pg_catalog` policy, producing
the values above; no implementation change was made.

## 5. Gate-to-oracle traceability

All 39 registered adversarial rows are hash-pinned to six executable files,
their line/marker references resolve, both replay results are `PASS`, and no
row is unclassified. The principal gate trace is:

| Gate | Executable/catalog evidence | C6 result |
|---|---|---|
| Fresh replay and constraints | two terminal PASS logs; 2,962 controls replay-match | true |
| Role matrix | 15,485 rows PASS; direct catalog grants above | true |
| Post-seal mutation denied | `P2A-SEAL-POST-001/002/003` | true |
| Stale CAS denied | `P2A-CAS-STALE-001/002` | true |
| Unsealed promotion denied | `P2A-CAS-UNSEALED-001/002` | true |
| Research/visual current independent | named generation assertions in `002_release_seal_cas.sql` | true |
| Unknown relation fail-closed | `P2A-REL-UNKNOWN-001`, inactive/evidence companions | true |
| Legacy projection cannot promote | `P2A-TRACE-LEGACY-001` | true |
| Rights/policy/health fail-closed | `P2A-RIGHTS-UNKNOWN-001`, `P2A-POLICY-VIEWER-001`, `P2A-HEALTH-DEAD-001` with exact SQLSTATE `23514` where specified | true |
| Takedown precedence | `P2A-TAKEDOWN-001/002` | true |
| Raw/held locator hidden | role catalog plus `P2A-REDACTION-001` | true |
| PUBLIC/API write denied | `P2A-SEC-PUBLIC-001`, `P2A-SEC-API-001`, direct catalog | true |
| Empty TRACE state supported | `P2A-TRACE-ZERO-001`; live accepted count 0 | true |
| Zero positive rights supported | `P2A-RIGHTS-ZERO-001`; live remote count 0 | true |
| Fixture rollback | `P2A-RESIDUE-001`; both exact table totals 0 | true |

The exact gates claimed in `12_PHASE2A_GATE_RECEIPT.md` are supported. Its
`PENDING_C6` marker is the expected pre-signature state, not a failed gate.

## 6. Independent review and Git scope

C1–C5 receipt bytes match the provisional manifest. C1 and C2 are PASS
design/security reviews; C2's six conditional pre-implementation P0 items are
subsequently closed by the executable package. The later hash-pinned C3 and
C4 reviews report residual `P0=0` and `P1=0`; C5 reports `EXIT_STATUS=PASS`.

The base commit is an ancestor of the observed HEAD. The 40 committed Phase2A
paths and 24 pre-C6 untracked package paths are confined to `database/` and
`docs/audits/v49-phase2a-schema/`. The 42 non-audit implementation paths are
exactly the manifest implementation set. No frontend, v48 payload, SQLite,
TRACE shard, media, QA image, or other forbidden asset is changed. The
committed diff passes `git diff --check`.

## 7. Command and exception ledger

C6 used bounded read-only invocations of `git`, `jq`, `shasum`, `cmp`, `rg`,
`sed`, `wc`, Python standard-library parsers, the baseline-aware historical
verifier, and `/opt/homebrew/opt/postgresql@16/bin/psql`.

- A workspace-dependency locator produced no output and was explicitly
  terminated; it created no repository or database state. Existing
  controller artifact-tool evidence was used instead of repeating a long TSV
  import.
- The first escalated psql attempt passed literal `\\n` characters in a
  one-line `-c` argument and failed at parse time before any SQL statement or
  session-side change executed. The corrected bounded command then completed
  once for both databases; the later focused predicate correction also
  completed read-only. All successful psql sessions exited normally.
- C6 did not rerun `replay.sh`, `run_tests.sh`, or `schema_hash.sh`.

At handoff, the controller's single disposable cluster remains alive solely
so the controller can perform its prescribed normal shutdown after C6. C6
owns no PostgreSQL, Node, Next, TypeScript, browser, Docker, generator, or
background process, and has no open psql session.

```text
C6_TASK_OWNED_RESIDUAL_PROCESS=0
C6_OPEN_PSQL_SESSION=0
C6_DATABASE_WRITES=0
C6_SQL_OR_SCHEMA_EDITS=0
CONTROLLER_CLUSTER_EXPECTED_AT_HANDOFF=1
```

## 8. Final C6 gate state

```text
C6_STATUS=PASS
C6_FAILURE_COUNT=0

PHYSICAL_SCHEMA_IMPLEMENTED=true
FRESH_DATABASE_REPLAY=true
FRESH_REPLAY_COUNT=2
SCHEMA_HASH_DETERMINISTIC=true
SCHEMA_CONSTRAINT_TESTS=true
ROLE_GRANT_MATRIX_VERIFIED=true

POST_SEAL_MUTATION_DENIED=true
STALE_CAS_UPDATE_DENIED=true
UNSEALED_CURRENT_PROMOTION_DENIED=true
RESEARCH_VISUAL_CURRENT_INDEPENDENT=true
UNKNOWN_RELATION_FAIL_CLOSED=true
RAW_HELD_LOCATOR_HIDDEN=true
PUBLIC_WRITE_DENIED=true
EMPTY_TRACE_STATE_SUPPORTED=true
ZERO_POSITIVE_RIGHTS_STATE_SUPPORTED=true

PRODUCTION_ROW_COUNT=0
TEST_FIXTURE_RESIDUE=0

DATABASE_POPULATED=false
MIGRATION_EXECUTED=false
TRACE_RESEARCH_RELEASE_READY=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

No C6 failure blocks the controller from finalizing the receipt package,
stopping the disposable cluster, regenerating the final manifest/checksums,
and performing the prescribed Git checks. C6 authorizes no population
migration or later phase.

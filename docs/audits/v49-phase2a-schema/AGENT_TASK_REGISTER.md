# v49 Phase 2A — Agent task register

The primary controller is the sole migration author and sole disposable-PostgreSQL-cluster operator. Review agents may read the repository and add only their assigned receipt; they must not edit SQL, start PostgreSQL, connect to port 5432, or run a competing replay.

| Wave | Agent | Independent scope | Exclusive output | PostgreSQL / SQL-write authority | Status |
|---|---|---|---|---|---|
| C1 | C1 physical/research reviewer | Physical FK model, ingest/core/provenance/corpus/assertion/relation/TRACE mapping | `agents/C1_PHYSICAL_RESEARCH_REVIEW.md` | None | COMPLETE — PASS |
| C1 | C2 security/release reviewer | Roles, grants, visual/public boundary, release/seal/CAS and negative oracle | `agents/C2_SECURITY_RELEASE_REVIEW.md` | None | COMPLETE — PASS |
| C2 | C3 SQL model reviewer | Hash-pinned full physical-model and release-copy review | `agents/C3_SQL_MODEL_REVIEW.md` | None | COMPLETE — PASS |
| C2 | C4 security oracle reviewer | Grants, definer hardening, rights/seal/CAS/public-boundary adversarial review | `agents/C4_SECURITY_ORACLE_REVIEW.md` | None | COMPLETE — PASS |
| C2 | C5 artifact design reviewer | TSV row units, closed headers, catalog completeness and package rules | `agents/C5_AUDIT_ARTIFACT_DESIGN_REVIEW.md` | None | COMPLETE — PASS |
| C3 | C6 independent final verifier | Fresh DB, logs, schema hashes, artifacts, package and final gate | `agents/C6_INDEPENDENT_FINAL_VERIFIER_RECEIPT.md` | Read-only connection to isolated final DBs | COMPLETE — PASS |

The controller authored SQL, started the one disposable cluster, ran both
fresh replays and tests, generated catalog artifacts, stopped the cluster, and
created the package manifest/checksums. C1–C5 did not connect to PostgreSQL.
C6 read only the two final databases and wrote only its receipt. The controller
then stopped the cluster normally and removed the exact disposable paths.

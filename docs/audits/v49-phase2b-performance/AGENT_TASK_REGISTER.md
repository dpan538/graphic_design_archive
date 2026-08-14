# Phase 2B-P agent task register

| Queue | Task | Scope | Database/process authority | Output | Status |
|---|---|---|---|---|---|
| A | A1 | Deferrable constraints, triggers, dependency SCCs, FK index coverage | Read-only; no PostgreSQL processes | `agents/A1_CONSTRAINT_DEPENDENCY_INDEX_AUDIT.md` | COMPLETE |
| A | A2 | Importer staging/COPY/order/transaction/rollback and repeated-scan audit | Read-only; no PostgreSQL processes | `agents/A2_IMPORTER_TRANSACTION_PATH_AUDIT.md` | COMPLETE |
| A | A3 | Recovery SHA, staging attestation inheritance, probes and Git safety | Read-only; no full staging rehash | `agents/A3_RECOVERY_STAGING_GIT_SAFETY_AUDIT.md` | COMPLETE |
| B | B1 | Forward remediation and no-constraint-weakening review | Read-only after remediation | `agents/B1_REMEDIATION_INDEPENDENT_REVIEW.md` | COMPLETE; P0/P1=0 |
| B | B2 | Scale curve, EXPLAIN/BUFFERS, parity and A/B digest review | Read-only after scale ladder/replays | `agents/B2_SCALE_CURVE_DIGEST_INDEPENDENT_REVIEW.md` | COMPLETE; P0/P1=0; GO |
| B | B3 | Atomicity, roles, Seal/CAS, public boundary, residue, Git/process cleanup | Read-only after final verification | `agents/B3_ATOMICITY_BOUNDARY_CLEANUP_REVIEW.md` | COMPLETE; P0/P1=0 |

Only the primary agent may start or stop PostgreSQL, run an importer, write core
implementation, or clean task-owned resources.  Queue A agents were dispatched
after the isolated worktree was proved clean at recovery SHA
`6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320`.

# Risks and residuals

Final counts: `P0_COUNT=0`, `P1_COUNT=1`, `P2_COUNT=0`.

The one P1 is the API search adapter failure described in `23_API_READ_SMOKE.md`. The database closure itself is green, but overall `PHASE_STATUS` cannot be `DB_CLOSURE_COMPLETE` because API read smoke is a required success condition. Recovery must either authorize the minimal server-adapter change under `frontend/` or provide a non-frontend server adapter that implements the existing contract, then rerun the required permission/schema/fresh/API gates.

All task-owned PostgreSQL/importer/builder/controller processes exited, the cluster fast-stopped, and the exact scratch root was removed. `TASK_OWNED_RESIDUAL_PROCESS_COUNT=0`. The audit package is the only formal evidence source.

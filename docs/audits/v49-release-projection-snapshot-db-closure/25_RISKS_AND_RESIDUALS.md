# Risks and residuals

Final P0/P1/P2 counts: `FINAL_PENDING`.

Known boundary: the production composition root intentionally has no configured PostgreSQL provider; the smoke injects the existing server-side provider through the route's test seam. Any defect that requires changing a `frontend/` path remains subject to the explicit frontend stop rule and cannot be hidden by a harness substitute.

All residual task processes and scratch database state must be removed after evidence capture. The audit package remains the only formal evidence source.

# Frontend design handoff

Frontend design begins from the closed 18-template Read API contract. It must preserve release identity, deterministic pagination, missing/null/empty semantics, fail-closed held and rights states, and zero-relation/zero-positive-rights behavior.

Frontend work must not modify `database/**`, frozen v49 inputs, release evidence, API grants, or permit direct browser-to-PostgreSQL access. Visual design and assets remain governed by `FRONTEND_DESIGN_LICENSE.md`.


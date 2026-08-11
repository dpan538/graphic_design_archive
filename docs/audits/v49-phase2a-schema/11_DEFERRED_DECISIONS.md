# v49 Phase 2A — Deferred decisions

No Phase 2A P0 identity, cardinality, state, seal, CAS, permission or public
serialization decision remains open. The following are deliberately deferred
and do not block the physical schema:

1. Import and reconcile the 15,923 v48 candidate rows in a separately
   authorized migration phase. This includes the 7,995 eligible and 7,928
   held population; no row has been imported here.
2. Measure production query plans before considering partitioning, PostGIS,
   broad GIN/full-text indexes, graph storage or materialized visualization
   tables.
3. Implement the HTTP Read API, OpenAPI, JSON Schema, JSON-LD, DCAT,
   Repository/frontend adapter, CI and deployment in later gates.
4. Add a dedicated two-session concurrency harness for seal versus restrictive
   rights/takedown writes. Phase 2A already shares transaction/advisory locks
   and executable single-session state oracles; the extra harness is P2
   hardening.
5. Extend RFC 8785/JCS boundary vectors beyond the currently tested manifest
   domain, and optionally compute every caller-supplied audit digest inside its
   controlled function for uniform ergonomics. Existing digests are verified
   before acceptance.
6. Run real migration/workload capacity measurements at 20k, 50k, 100k and
   million-scale bridge/evidence volumes. These are engineering capacity
   observations, never collection targets or DDL checks.

`DATABASE_POPULATED=false`, `FREEZE_READY=false`,
`PROMOTION_READY=false`, and `DEPLOYMENT_READY=false` remain intentional.

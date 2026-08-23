# Round 4 decision

## Closed decisions

- Context production runtime uses the committed `trace-context-v1` projection, validates it once per process, and passes all-public/all-held rehearsal.
- Context semantics and governance remain unchanged; engineering logic is frozen.
- Geography is governed as `recorded_region_context` through a 93-row explicit registry.
- Time is governed as `recorded_date_context` with corrected precision, 23 decades, and interval-overlap membership.
- Natural Earth Admin 0 Countries 5.1.1 at 50m is the pinned geometry foundation.
- Equal Earth is the default projection; Natural Earth 1 is the alternative.
- Map geometry, anchors, period filtering, aggregation, selection, dots, and patterns are function-derived.
- One dot equals one record within a bounded deterministic aggregate field; dot positions never claim object locations.
- Texture.js 1.2.3 is rejected for runtime; the small native deterministic pattern helper is retained.
- The read model has periods, one-period atlas, and selected-geography paged records resources.
- Unmapped and aggregate-only data remain visible in the atlas/table and denominator reporting.
- The functional route is unlinked/noindex; final visual design remains deferred.
- Exploration Field remains open-ended data mining with no implementation.

## Readiness at this checkpoint

| Gate | Status |
| --- | --- |
| Context runtime closed | Ready |
| Geography governance | Ready on generated projection candidate |
| Temporal governance | Ready on generated projection candidate |
| GIS functions | Ready on standalone verifier/benchmark |
| Timeline functions | Ready on generated bucket/cube artifacts |
| Public read-model architecture | Ready; exact and built-output API guards pass |
| Functional renderer | Ready; production build and integrated benchmark pass |
| Final visual design | Not ready by design |

## Remaining finalization work

The projection is resealed at SHA-256 `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06`, and the governance/full-cohort verifier passes all 7,995 public records, 7,928 held IDs, 23 periods, 373 period-region cells, 20 invariants, and 10 pure-function adversaries. The final typecheck/API/build/regression, functional performance, bundle, Project Log, changed-file, and whitespace gates pass. The audit package is checksum-sealed.

No PR, merge, deployment, or final visual acceptance belongs to this round.

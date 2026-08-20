# Concurrency

One controller runs the dedicated session matrix with 120-second statement timeout, 30-second lock timeout, 15-second observed barrier timeout, and five-minute whole-harness cap.

- Same release: exactly one candidate transition; peer returns serialization/state conflict.
- Different releases: both complete under the one-builder global mutex.
- Canonical writer overlap: builder begins only after `pg_stat_activity` shows the writer backend in `PgSleep`; accepted result is serialization failure or a consistent pre-state projection.

Diagnostic harness passed; final ordered result: `FINAL_PENDING`.

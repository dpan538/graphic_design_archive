# Concurrency

One controller runs the dedicated session matrix with 120-second statement timeout, 30-second lock timeout, 15-second observed barrier timeout, and five-minute whole-harness cap.

- Same release: exactly one candidate transition; peer returns serialization/state conflict.
- Different releases: both complete under the one-builder global mutex.
- Canonical writer overlap: builder begins only after `pg_stat_activity` shows the writer backend in `PgSleep`; accepted result is serialization failure or a consistent pre-state projection.

The final ordered harness passed in 3,352.423 ms. Same-release results were one `00000` and one `40001` with exactly one candidate event/protocol/receipt. Different-release results were two `00000`. Writer overlap observed the named backend at `PgSleep` and produced a consistent 128-membership pre-state projection. Peak was two database sessions under one controller. `CONCURRENCY=PASS`.

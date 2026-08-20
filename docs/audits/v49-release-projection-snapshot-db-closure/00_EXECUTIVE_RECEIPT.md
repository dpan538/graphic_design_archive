# v49 release projection snapshot database closure

Status: `STOPPED_RECOVERABLE_CHECKPOINT`.

This successor starts at `321e89f954fc32eae91a124afe83af9b8b2f32a3`. It confines changes to PostgreSQL release projection performance, forward-only object cleanup, database verification, and a final server-side Read API smoke. No page, component, CSS, animation, visual asset, browser matrix, deployment, staging, or production database is in scope.

The controlled checkpoint baseline reproduced an exponent above the `1.35` gate. The first superlinear stage was copy parity reconciliation: its incomplete join omitted `member_ordinal`, removed 6,002,671 rows at 2k, and consumed 963.142 ms. The forward-only fix binds the complete tuple; the final optimized plan removes zero rows and runs in 4.562 ms at 2k. The final 1k/2k builders were 365.130/789.425 ms, exponent 1.112392. All database scale, replay, digest, schema, stable-ID, concurrency, missingness, permission, fault, and cleanup gates passed.

The first failed gate was `API_READ_SMOKE`: five reads passed, then the first search request returned HTTP 503 instead of 200 because the existing server adapter calls an unexported `pageByKey`. The only fix site is under `frontend/`, while this task requires `FRONTEND_FILES_CHANGED=0`; the checkpoint therefore stops without modifying frontend code. There was no database, permission, process, staging, or production pollution.

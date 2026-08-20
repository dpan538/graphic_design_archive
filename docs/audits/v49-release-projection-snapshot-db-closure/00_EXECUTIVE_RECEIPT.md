# v49 release projection snapshot database closure

Status: `FINAL_PENDING`.

This successor starts at `321e89f954fc32eae91a124afe83af9b8b2f32a3`. It confines changes to PostgreSQL release projection performance, forward-only object cleanup, database verification, and a final server-side Read API smoke. No page, component, CSS, animation, visual asset, browser matrix, deployment, staging, or production database is in scope.

The controlled checkpoint baseline reproduced an exponent above the `1.35` gate. The first superlinear stage was copy parity reconciliation: its incomplete join omitted `member_ordinal`, removed 6,002,671 rows at 2k, and consumed 963.142 ms. The forward-only fix binds the complete tuple; the corresponding optimized diagnostic plan removes zero rows and runs in 4.511 ms at 2k. Final-tree gate results are recorded in `24_FINAL_TREE_RERUN.md`.

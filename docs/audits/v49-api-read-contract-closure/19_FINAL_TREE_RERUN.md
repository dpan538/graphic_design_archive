# Final-tree rerun

The candidate tree passed typecheck, repository contract, `pageByKey` module contract, 22-vector fixture/HTTP parity, exhaustive 18-path FRESH_C integration, 558-request runtime profile, read-only statistics, OpenAPI parse, official post-test schema hash, and production build.

Before finalization this package is intentionally marked pending. The final procedure is:

1. commit the complete candidate tree;
2. rebuild FRESH_C from empty using the formal runner on that commit;
3. rerun focused database gates, sealed release generation, exhaustive API contract, statistics, typecheck, and build;
4. stop the single cluster and prove residual process count zero;
5. generate manifest/checksums and commit the audit-only refresh;
6. run minimal typecheck/module/OpenAPI/build verification on the audit-only final commit so `FINAL_TREE_EXECUTION_SHA` equals final local/remote SHA.

The exact SHA binding is reported only after execution because a Git commit cannot contain its own hash.

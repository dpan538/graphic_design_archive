# API read-only smoke

This stage runs only after all database gates. It creates a fresh verified v5 sealed release, promotes it through CAS, connects as `gda_v49_phase2a_api_reader`, and invokes the existing server-side route/provider contract without a browser.

Coverage includes current/exact metadata, overview/counts, surface detail/not-found, deterministic filtered keyset pagination, empty results, folder fail-closed behavior, TRACE/relation fail-closed behavior, unknown route, HEAD, OPTIONS, four denied write methods, content type, internal-schema leakage, and direct role denial probes.

No browser, visual regression, accessibility matrix, UI build, or deployment was run. The sealed/current fixture, read role, and first five checks passed: current metadata, exact metadata, archive overview, surface detail, and not-found behavior. The sixth attempted endpoint, filtered search page 1, returned HTTP 503 instead of 200 with `(0 , _pagination.pageByKey) is not a function`.

The exact defect is in the existing server adapter: `frontend/src/lib/read-platform/server/postgres-repository.ts` imports/calls `pageByKey`, while `frontend/src/lib/read-platform/pagination.ts` exports `keysetPage` and no `pageByKey`. Because success requires `FRONTEND_FILES_CHANGED=0`, no source fix was made. Write-method negative checks and all later endpoints are `NOT_RUN_STOP_RULE`; the already-completed 36/36 database role matrix remains PASS. Schema hashes before/after the read attempts match and no data or permission pollution exists. `API_READ_SMOKE=FAIL`, first failed gate.

The raw directory also preserves two resolved harness prerequisites rather than misclassifying them as API failures: the direct runner needed the normal Next.js `server-only` marker, and the psql executor needed stdin (`-f -`) for variable expansion rather than `-c`. The tree-contained `psql-stdin-wrapper.zsh` makes that invocation correction auditable. Attempt 4 reached the real adapter and its response tracer records five 200/404 contract successes followed by the search 503.

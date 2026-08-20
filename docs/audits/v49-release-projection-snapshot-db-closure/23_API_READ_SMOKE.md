# API read-only smoke

This stage runs only after all database gates. It creates a fresh verified v5 sealed release, promotes it through CAS, connects as `gda_v49_phase2a_api_reader`, and invokes the existing server-side route/provider contract without a browser.

Coverage includes current/exact metadata, overview/counts, surface detail/not-found, deterministic filtered keyset pagination, empty results, folder fail-closed behavior, TRACE/relation fail-closed behavior, unknown route, HEAD, OPTIONS, four denied write methods, content type, internal-schema leakage, and direct role denial probes.

No browser, visual regression, accessibility matrix, UI build, or deployment is run. Final result: `FINAL_PENDING`.

# Production Load Method

All online measurements use the built Next.js production server and the actual `/api/trace/v2/exploration/` HTTP routes. Direct service calls, if retained, are labelled `IN_PROCESS_MICROBENCHMARK` and are not API latency.

The workload matrix contains JSON/API concurrency 1, 5, 10, 25, and 50; PNG concurrency 1, 2, 5, and 10; cold startup and first request; warm steady state; burst load; sustained mixed load; and concurrent PNG load. Each workload records request, success, failure, timeout, P50/P95/P99/maximum latency, throughput, response bytes, CPU, RSS, heap used/total, event-loop delay, client errors, and server errors.

Sustained load uses its recorded dual termination criterion: both minimum request volume and minimum runtime/stability duration must be satisfied. No post-hoc marketing SLO is inferred. Closure is based on absence of crashes, deadlocks, state/hash corruption, unexpected 5xx, ordinary-load timeouts, PNG corruption, and unbounded memory growth.

Offline build-time measurement separately covers vocabulary, pair/evidence, graph, canonical composition, state, transition, workflow, and export generation plus peak process memory and storage. This keeps offline research/build cost distinct from online request cost.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/production-http-results.json`, `docs/audits/v49-exploration-full-space-closure-round1/raw/concurrency-results.json`, `docs/audits/v49-exploration-full-space-closure-round1/raw/runtime-memory-results.json`, `docs/audits/v49-exploration-full-space-closure-round1/raw/build-time-computation-results.json`, and `docs/audits/v49-exploration-full-space-closure-round1/raw/sustained-load-results.json`.

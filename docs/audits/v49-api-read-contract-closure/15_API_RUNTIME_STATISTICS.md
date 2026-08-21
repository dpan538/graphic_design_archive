# API runtime statistics

No formal repository API latency threshold exists, so the performance source is observational only. Every path received one first/cold-order request, 20 sequential warm requests, and ten controlled concurrent requests through the API reader role.

```text
API_PERFORMANCE_GATE_SOURCE=OBSERVATIONAL_ONLY
API_RUNTIME_PROFILE=PASS
PUBLIC_ENDPOINTS_PROFILED=18
API_RUNTIME_REQUEST_COUNT=558
API_RUNTIME_SUCCESS_COUNT=558
API_RUNTIME_TIMEOUT_COUNT=0
API_RUNTIME_5XX_COUNT=0
MAX_CONCURRENT_READ_SESSIONS=10
```

The profile records per-path min/median/p95/max, bytes, returned rows, pagination size, query count, status distribution, timeouts, 5xx, and response digest in `docs/statistics/v49-api-runtime-profile.{md,json,csv}`. Repeated bodies were deterministic and process RSS did not exhibit growth in the measured run.

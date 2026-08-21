# Exhaustive Read API smoke

```text
API_READ_SMOKE=PASS
API_READ_ENDPOINTS_DISCOVERED=18
API_READ_ENDPOINTS_TESTED=18
API_READ_ENDPOINTS_PASSED=18
ALL_DISCOVERED_READ_ENDPOINTS_TESTED=true
CONTRACT_REQUEST_CASES=170
API_5XX_COUNT=0
SEARCH_HTTP_503_COUNT=0
SEARCH_CANONICAL_REQUEST_HTTP_STATUS=200
```

Each template received a primary case, deterministic repeat, content type/schema/release checks, actual example coverage, and the uniform negative method matrix. Valid empty collections remained 200; unpublished singletons remained 404. No adapter/database failure was converted to an empty success.

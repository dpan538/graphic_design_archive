# Permission and negative methods

```text
API_WRITE_METHOD_NEGATIVE_CHECK=PASS
NEGATIVE_METHOD_CASES=72
API_ROLE=gda_v49_phase2a_api_reader
API_ROLE_DIRECT_WRITE_CHECK=PASS:DENIED
API_ROLE_DDL_CHECK=PASS:DENIED
POST_TEST_RELEASE_DIGEST_UNCHANGED=true
POST_TEST_SCHEMA_HASH_UNCHANGED=true
```

POST, PUT, PATCH, and DELETE returned 405 with the expected `Allow` header for all 18 paths. API-visible descriptor/surface counts and digest were unchanged. Direct INSERT/UPDATE/DELETE probes against core and research, release-state write, DDL, and raw select all failed under the API role. The official schema hash remained `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`.

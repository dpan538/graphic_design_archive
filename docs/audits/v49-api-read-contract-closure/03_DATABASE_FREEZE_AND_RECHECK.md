# Database freeze and focused recheck

```text
DATABASE_FROZEN=true
DATABASE_FILES_CHANGED=0
MIGRATION_FILES_CHANGED=0
DATABASE_FUNCTIONS_CHANGED=0
DATABASE_GRANTS_CHANGED=0
DATABASE_INTEGRITY_RECHECK=PASS
SCHEMA_SHA256=df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd
NORMALIZED_CONTENT_SHA256=a0fa7aaeb84b383371c20340afa2c2a5c7f12408102767de189225cc93e478b9
STABLE_KEY_SET_SHA256=9bf3491b9c6603f3a7f8f141f2d9abac915ec1b91cd442b9248190263a8835a0
```

The official verifier reported no schema drift or integrity failures. Current-leaf, missingness, DML permissions, and stable-ID reconciliation all passed. The focused performance rerun measured 36.124 ms at 32, 359.999 ms at 1k, and 795.578 ms at 2k; exponent 1.144010483028889 remained below 1.35. The 15,923 / 47,982 digest-only build was 6,864.760 ms and reproduced `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`.

Evidence: `raw/fresh-c/fresh-c-verifier.json`, `raw/fresh-c/focused-performance-summary.json`, and `raw/fresh-c/reconciliation/`.

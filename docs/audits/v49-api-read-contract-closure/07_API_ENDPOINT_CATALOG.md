# API endpoint catalog receipt

```text
API_ENDPOINT_CATALOG=PASS
API_INTERFACE_MAP=PASS
OPENAPI_3_1_SPEC=PASS
API_EXAMPLE_RESPONSES=PASS
OPENAPI_PATH_COUNT=18
API_UNDOCUMENTED_ENDPOINT_COUNT=0
```

Formal artifacts:

- `docs/api/v49-read-api-catalog.md`
- `docs/api/v49-read-api-openapi.yaml`
- `docs/api/v49-read-interface-map.md`
- `docs/api/v49-read-api-examples.json`

The YAML parses as OpenAPI 3.1.0 and contains exactly the 18 discovered paths. Examples are emitted from actual FRESH_C dispatch results. A resource type with no published singleton records its real 404 and explicitly marks success unavailable instead of inventing data.

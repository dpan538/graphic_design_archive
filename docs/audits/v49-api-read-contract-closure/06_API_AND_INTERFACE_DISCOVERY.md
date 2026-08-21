# API and interface discovery

Static source discovery found one catch-all HTTP route, its server-only controller, 18 implemented GET resource templates, 15 `ArchiveRepository` methods, one provider `open` operation, and named `pageByKey` pagination. The internal read-interface count is therefore 17. The route exports uniform HEAD/OPTIONS and negative write methods but those methods do not create additional resource templates.

```text
API_DISCOVERY=PASS
PUBLIC_READ_ENDPOINT_COUNT=18
INTERNAL_READ_INTERFACE_COUNT=17
API_UNDOCUMENTED_ENDPOINT_COUNT=0
```

Prospective baseline paths without actual controller branches were not invented. UI fixture helpers in `frontend/src/lib/archive-data.ts` were classified as UI helpers, not HTTP APIs. See `docs/api/v49-read-interface-map.md` and the embedded endpoint inventory in `raw/api/api-contract-results.json`.

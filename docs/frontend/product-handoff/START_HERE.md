# Product handoff — start here

This is the bounded cross-product handoff for Global Search, System Suggestions, and TRACE. It is a functional reference implementation, not final visual design or a deployment instruction.

## Read in this order

1. `../../search/SEARCH_PRODUCT_CONTRACT.md` — one public-object Search, desktop/mobile workflow, ranking, field, and evidence boundary.
2. `../../operations/SYSTEM_SUGGESTIONS_SETUP.md` — server-only provider/fallback setup and secret handling.
3. `PRODUCT_STRUCTURE.md` — homepage hierarchy, Search-to-object flow, and TRACE’s three desktop functions.
4. `../trace-v49-handoff/START_HERE.md` — bounded, evidence-specific TRACE handoff.
5. `../../api/PRODUCT_API_MAP.md` — complete 91-template, 275 method-route-pair product API table.
6. `FRONTEND_STATE_MATRIX.md` — loading, zero/empty, partial, failure, fallback, and mobile states.
7. `SOURCE_MANIFEST.json` — bounded paths for implementation verification.

```text
SEARCH_MOBILE_FUNCTIONAL=true
TRACE_MOBILE_FULL_RUNTIME_ENABLED=false
PUBLIC_SEARCH_DOCUMENT_COUNT=7995
HELD_SEARCH_DOCUMENT_COUNT=0
SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT=0
PUBLIC_UI_AI_LABEL_COUNT=0
FRONTEND_FINAL_VISUAL_DESIGN_STARTED=false
DEPLOYMENT_PERFORMED=false
```

Provider guidance never participates in Search retrieval/ranking or TRACE/evidence state. Open Inquiry remains unresolved, fixed-disclosure, and isolated from Validated Exploration.

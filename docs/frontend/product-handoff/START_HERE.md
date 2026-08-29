# Product handoff — start here

This is the bounded cross-product handoff for Global Search, System Suggestions, and TRACE. It is a functional reference implementation, not final visual design or a deployment instruction. Do not scan the entire repository. Begin with this frontend handoff and expand into implementation only through `SOURCE_MANIFEST.json` or explicit source paths referenced by the master census.

## Read in this order

1. `FRONTEND_FUNCTIONAL_ARCHITECTURE_AND_SCALE_CENSUS.md` — authoritative functional hierarchy, bounded design brief, complete route/API disposition, scale, rights, state, and platform census.
2. `PRODUCT_STRUCTURE.md` — homepage hierarchy, Search-to-object flow, and TRACE’s three desktop functions.
3. `FRONTEND_STATE_MATRIX.md` — loading, zero/empty, partial, failure, fallback, and mobile states.
4. `../../api/PRODUCT_API_MAP.md` — start with the frontend-required sections, then use the complete 91-template, 275 method-route-pair appendix only when needed.
5. `../../search/SEARCH_PRODUCT_CONTRACT.md` — one public-object Search, desktop/mobile workflow, ranking, field, and evidence boundary.
6. `../trace-v49-handoff/START_HERE.md` — bounded, evidence-specific TRACE handoff.
7. `SOURCE_MANIFEST.json` — the only bounded path list for implementation verification.

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

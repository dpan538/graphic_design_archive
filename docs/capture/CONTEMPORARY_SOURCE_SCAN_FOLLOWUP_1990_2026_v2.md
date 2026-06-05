# Contemporary Source Scan Follow-up 1990-2026 v2

Derived follow-up queues from the v2 source scan. This document is source planning only: no pages were fetched, no raw probe bodies were read, no image files were downloaded, and no image state was upgraded.

## Safety Rules

- Source discovery only until item-level source and rights review exists.
- Do not capture image binaries from these queues.
- IMG01 and IMG03 require authoritative item-level source evidence; heuristic, platform, ToS, LLM, IIIF, OpenGraph, or JSON-LD image signals are not enough.
- IMG04 remains a real text/no-image-frame state, not a parser-failure fallback.
- Priority is internal triage only.

## P1 Protocol Queue

- Rows: 97
- WordPress REST / HTML: 30
- IIIF/source-viewer metadata: 19
- Static JS/headless metadata: 15
- RSS/Atom source feed: 13
- Search interface/manual source registry: 8
- JSON-LD page metadata: 5
- PDF text/link extraction: 2
- HTML/manual source registry: 2
- CONTENTdm source metadata: 1
- Kramerius / IIIF source metadata: 1
- Omeka source metadata: 1

## Regional Priorities

- 1. East Asia: score 104; total 27; ok 19; P1 adapter 6; P1 text 13
- 2. Global: score 85; total 33; ok 29; P1 adapter 10; P1 text 14
- 3. Southeast Asia: score 84; total 17; ok 11; P1 adapter 4; P1 text 4
- 4. Africa: score 81; total 12; ok 9; P1 adapter 2; P1 text 6
- 5. South Asia: score 79; total 11; ok 6; P1 adapter 2; P1 text 4
- 6. MENA: score 78; total 12; ok 8; P1 adapter 2; P1 text 4
- 7. Latin America / Caribbean: score 66; total 9; ok 4; P1 adapter 4; P1 text 0
- 8. Latin America: score 60; total 8; ok 6; P1 adapter 4; P1 text 2

## Retry Registry

- Rows: 37
- dns_or_domain: 11
- forbidden_403: 9
- ssl_certificate: 6
- connection_reset: 3
- timeout: 3
- not_found_404: 3
- auth_required_401: 1
- rate_limited_429: 1

## Adapter Queue

- Rows: 148
- P1B_text_source_enrichment: 52
- P1A_protocol_adapter: 45
- P2_retry_or_alternate_endpoint: 37
- P2_discovery_source_resolution: 8
- P2_manual_source_review: 6

## Next Implementation Order

1. Build WordPress/RSS/JSON-LD source adapters for text, canonical source links, tags, dates, and rights text.
2. Build IIIF/CONTENTdm/Kramerius/DSpace metadata adapters as source-hosted display-route probes only.
3. Run headless/static metadata probes for high-priority regional sources after source terms review.
4. Resolve retry rows through canonical endpoint checks or manual source-registry notes without bypassing access controls.

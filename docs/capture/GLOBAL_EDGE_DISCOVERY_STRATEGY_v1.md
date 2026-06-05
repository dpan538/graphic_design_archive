# Global Edge Discovery Strategy v1

Generated: 2026-06-05

This registry turns broad research notes into a conservative source-discovery layer.
It is not an object ingest, not a rights clearance list, and not permission to
download or republish source images. Every candidate still needs source review,
rights review, field provenance, and citation review before publication use.

## Safety boundary

- No module may automatically upgrade image state to IMG01 or IMG03 from LLM,
  visual analysis, ToS parsing, social-platform metadata, or similar-image search.
- IIIF discovery can support IMG02 because it is a source-hosted display route,
  not a local reuse claim.
- Social platforms, Pinterest boards, portfolio platforms, and repost networks
  are discovery leads only unless the original source is reviewed.
- Proxy/geobypass and authenticated database scraping are excluded from production
  automation. Those sources must remain manual or institutionally authorized.
- Impact scores may rank review priority, but cannot decide historical inclusion
  or image rights.

## Test calculation

- total_candidates: 81 — Global edge-source candidates generated in this pass.
- non_us_western_europe_candidates: 79/81 (97.5%) — Counts candidates outside North America and dominant Western/Central Europe; Eastern/Central Europe is counted as edge coverage.
- manual_or_access_restricted_candidates: 11/81 (13.6%) — Requires source contact, institutional access, protocol review, or manual handling.
- discovery_only_candidates: 6/81 (7.4%) — Can generate leads but not object-level evidence or image permission.

### Macro-region coverage

- Asia: 26
- Global: 19
- Latin America: 10
- Africa: 8
- Middle East and North Africa: 8
- Europe: 5
- Oceania: 4
- North America: 1

### Priority queue

- P1: 46
- P2: 25
- P3: 9
- P4: 1

### Adapter families

- html_metadata_adapter: 27
- bibliographic_adapter: 4
- social_discovery_adapter: 4
- manual_source_adapter: 3
- source_registry_context_adapter: 3
- bibliography_adapter: 2
- manual_database_adapter: 2
- text_enrichment_adapter: 2
- newspaper_ocr_adapter: 2
- manual_social_source_adapter: 2
- wordpress_adapter: 2
- global_router_adapter: 1
- oai_or_bibliographic_adapter: 1
- internet_archive_adapter: 1
- academic_graph_adapter: 1
- oai_router_adapter: 1
- rdf_api_adapter: 1
- finding_aid_adapter: 1
- manual_or_oai_adapter: 1
- museum_api_adapter: 1
- ndl_adapter: 1
- iiif_or_catalog_adapter: 1
- source_hosted_adapter: 1
- regional_library_adapter: 1
- library_api_adapter: 1
- manual_bibliography_adapter: 1
- collectiveaccess_adapter: 1
- figgy_iiif_adapter: 1
- manual_network_adapter: 1
- iiif_or_html_adapter: 1
- manual_bibliographic_adapter: 1
- network_map_adapter: 1
- kramerius_adapter: 1
- polona_adapter: 1
- iiif_or_bibliographic_adapter: 1
- catalog_adapter: 1
- trove_adapter: 1
- digitalnz_adapter: 1
- platform_metadata_adapter: 1

## P1 source directions

- Africa: ArchiveAfrica; African Activist Archive
- Asia: China International Design Museum; CADAL; M+ Collections; National Diet Library Digital Collections; DNP Graphic Design Archives; Tokyo ADC; Tokyo TDC; Ginza Graphic Gallery; CIViC Archive; Priya Paul Collection; Tasveer Ghar; Design Dashtahjaat; +5 more
- Europe: Graphic Front; SCOMUS; Kramerius Czech Digital Library; POLONA
- Global: World Digital Library; Internet Archive; OpenAlex; WorldCat and ArchiveGrid; Another Graphic; Design Reviewed
- Latin America: Fundacion IDA; Diseno Nacional; Grafica Latina; Archivo de Ilustracion Argentina; Princeton Latin American and Caribbean Ephemera; La Patria Uruguay; Hemeroteca Digital Brasileira; Hemeroteca Nacional Digital de Mexico
- Middle East and North Africa: Arabic Design Archive; Syrian Design Archive; SALT Research; Palestinian Museum Digital Archive
- North America: Letterform Archive
- Oceania: AIATSIS Collections; Trove; DigitalNZ; NAIDOC Poster Collections

## Discovery-only modules held behind review

- CORAA African Archive Network: map records are leads, not object evidence Initial policy: IMG04 source registry.
- Are.na: platform aggregation is not source evidence Initial policy: IMG00 discovery only.
- Pinterest: do not store images or treat pins as rights evidence Initial policy: IMG00 discovery only.
- Tumblr: repost provenance is weak; use only as lead Initial policy: IMG00 discovery only.
- Instagram public accounts: platform access and image rights are high risk Initial policy: IMG00 discovery only.
- Reddit design communities: community comments are leads, not evidence Initial policy: IMG04/IMG00 discovery only.

## Next implementation route

1. Convert P1 protocol families into bounded adapter queues: IIIF/source viewer,
   OAI/catalog, WordPress/HTML metadata, CollectiveAccess, newspaper/OCR, and
   manual source-registry records.
2. Use this registry to expand `source_prospect_registry_v2` after source checks,
   not before.
3. Run capture only against sources whose robots/terms and access route have been
   reviewed. Store source links, metadata, citations, and rights evidence first.
4. Treat platform crawlers as outbound-source discovery. They should not write
   images, infer open licenses, or mint final object sheets on their own.

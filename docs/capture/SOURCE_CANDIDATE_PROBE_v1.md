# Source Candidate Probe v1

Source-level probe for edge/community/university/government candidates. This does not create public surfaces; it decides which source families deserve item-level adapters next.

- Access date: 2026-06-01
- Selected candidates: 60
- Probe rows written: 60

## Probe Status

- ok: 51
- http_error: 6
- failed: 3

## Next Capture Priority

- P1_adapter_candidate: 27
- P2_html_source_candidate: 16
- P3_manual_source_candidate: 8
- hold_http_error: 6
- hold_probe_failed: 3

## Region Mix

- Eastern Europe: 14
- Latin America: 11
- East Asia: 8
- Africa: 6
- Middle East and North Africa: 6
- Southeast Asia: 5
- Oceania and Pacific: 4
- South Asia: 4
- Latin America and the Caribbean: 2

## Adapter Hints

- html_text_source_adapter: 20
- manual_review_or_alternate_endpoint: 9
- html_jsonld_adapter: 8
- iiif_manifest_adapter: 8
- pdf_text_or_link_adapter: 6
- kramerius_adapter: 3
- dspace_oai_or_rest_adapter: 3
- html_source_probe_then_manual_rules: 2
- omeka_api_adapter: 1

## P1 Adapter Candidates

- ESC001 | AHIRA Archivo Historico de Revistas Argentinas | Latin America | RSS/Atom;PDF | pdf_text_or_link_adapter
- ESC002 | Fundacion IDA Investigacion en Diseno Argentino | Latin America | JSON-LD | html_jsonld_adapter
- ESC005 | CeDInCI Archivo | Latin America | RSS/Atom;JSON-LD | html_jsonld_adapter
- ESC017 | University of Cape Town Digital Collections | Africa | Omeka | omeka_api_adapter
- ESC018 | Mayibuye Archives | Africa | JSON-LD | html_jsonld_adapter
- ESC030 | Arab Image Foundation | Middle East and North Africa | PDF | pdf_text_or_link_adapter
- ESC050 | National Diet Library Digital Collections | East Asia | IIIF | iiif_manifest_adapter
- ESC061 | National Central Library Taiwan | East Asia | PDF | pdf_text_or_link_adapter
- SEM021 | POLONA | Eastern Europe | IIIF | iiif_manifest_adapter
- SEM062 | NDL Digital Collections | East Asia | IIIF | iiif_manifest_adapter
- ESC003 | Biblioteca Nacional Mariano Moreno Digital | Latin America | IIIF | iiif_manifest_adapter
- ESC006 | Biblioteca Brasiliana Guita e Jose Mindlin | Latin America | IIIF;DSpace | dspace_oai_or_rest_adapter
- ESC011 | Biblioteca Nacional del Peru Digital | Latin America | PDF | pdf_text_or_link_adapter
- ESC015 | UNAM Repositorio Institucional | Latin America | DSpace;RSS/Atom;JSON-LD | dspace_oai_or_rest_adapter
- ESC034 | Ataturk Library Digital Archive | Middle East and North Africa | JSON-LD | html_jsonld_adapter
- ESC052 | Kyoto University Rare Materials Digital Archive | East Asia | IIIF;JSON-LD | iiif_manifest_adapter
- ESC059 | HKUL Digital Initiatives | East Asia | ArchiveSpace/EAD | html_text_source_adapter
- ESC070 | Ateneo Rizal Library Digital Archives | Southeast Asia | RSS/Atom;JSON-LD | html_jsonld_adapter
- ESC077 | Slovak Digital Library | Eastern Europe | Kramerius | kramerius_adapter
- ESC083 | DIGAR Estonian Articles and Digital Archive | Eastern Europe | JSON-LD | html_jsonld_adapter
- SEM024 | Czech Digital Library | Eastern Europe | Kramerius | kramerius_adapter
- SEM027 | DIGAR | Eastern Europe | JSON-LD | html_jsonld_adapter
- SEM029 | Slovakiana | Eastern Europe | IIIF | iiif_manifest_adapter
- SEM085 | National Library of India | South Asia | PDF | pdf_text_or_link_adapter
- SEM086 | National Digital Library of India | South Asia | JSON-LD;PDF | html_jsonld_adapter

## Next Rule

Promote only `P1_adapter_candidate` and selected `P2_html_source_candidate` rows into item-level capture scripts. Failed or HTTP-error rows stay in the registry as link-only or manual-review sources; they should not be removed because the archive index must still acknowledge source territories that are difficult to automate.

# Item Capture Queue v1

This queue converts source-level probe evidence into the next item-level capture plan. It should be treated as a work queue, not as public archive content.

- Queue rows: 65
- Q1 protocol/adapter rows: 45
- Q2 HTML/text rows: 20

## Adapter Mix

- html_jsonld_adapter: 15
- html_text_source_adapter: 13
- pdf_text_or_link_adapter: 11
- html_source_probe_then_manual_rules: 10
- iiif_manifest_adapter: 7
- dspace_oai_or_rest_adapter: 5
- kramerius_adapter: 2
- omeka_api_adapter: 1
- contentdm_source_adapter: 1

## Region Mix

- Latin America: 13
- East Asia: 13
- Eastern Europe: 11
- Africa: 8
- Southeast Asia: 7
- Oceania and Pacific: 5
- South Asia: 5
- Middle East and North Africa: 3

## First 15 Queue Rows

- ICQ001 | Q1 | Biblioteca Nacional Mariano Moreno Digital | Latin America | iiif_manifest_adapter | target 12
- ICQ002 | Q1 | Archivo General de la Nacion Argentina | Latin America | iiif_manifest_adapter | target 12
- ICQ003 | Q1 | National Diet Library Digital Collections | East Asia | iiif_manifest_adapter | target 12
- ICQ004 | Q1 | Kyoto University Rare Materials Digital Archive | East Asia | iiif_manifest_adapter | target 12
- ICQ005 | Q1 | POLONA | Eastern Europe | iiif_manifest_adapter | target 12
- ICQ006 | Q1 | Slovakiana | Eastern Europe | iiif_manifest_adapter | target 12
- ICQ007 | Q1 | NDL Digital Collections | East Asia | iiif_manifest_adapter | target 12
- ICQ008 | Q1 | Biblioteca Brasiliana Guita e Jose Mindlin | Latin America | dspace_oai_or_rest_adapter | target 12
- ICQ009 | Q1 | UNAM Repositorio Institucional | Latin America | dspace_oai_or_rest_adapter | target 12
- ICQ010 | Q1 | University of Ghana Digital Collections | Africa | dspace_oai_or_rest_adapter | target 12
- ICQ011 | Q1 | University of Lagos Institutional Repository | Africa | dspace_oai_or_rest_adapter | target 12
- ICQ012 | Q1 | National Repository of Nigeria | Africa | dspace_oai_or_rest_adapter | target 12
- ICQ013 | Q1 | Slovak Digital Library | Eastern Europe | kramerius_adapter | target 12
- ICQ014 | Q1 | Czech Digital Library | Eastern Europe | kramerius_adapter | target 12
- ICQ015 | Q1 | University of Cape Town Digital Collections | Africa | omeka_api_adapter | target 8

## Execution Rule

Run one adapter family at a time. Each family must write raw source payloads, source-level evidence, image policy, text excerpts, and failure rows. The goal is not to maximize rows; the goal is to prove that each source can produce readable, rights-aware archive surfaces without collapsing back into large-institution sampling.

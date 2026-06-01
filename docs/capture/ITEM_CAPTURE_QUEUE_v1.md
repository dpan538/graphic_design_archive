# Item Capture Queue v1

This queue converts source-level probe evidence into the next item-level capture plan. It should be treated as a work queue, not as public archive content.

- Queue rows: 39
- Q1 protocol/adapter rows: 27
- Q2 HTML/text rows: 12

## Adapter Mix

- html_text_source_adapter: 12
- html_jsonld_adapter: 8
- iiif_manifest_adapter: 6
- pdf_text_or_link_adapter: 6
- dspace_oai_or_rest_adapter: 3
- kramerius_adapter: 2
- omeka_api_adapter: 1
- html_source_probe_then_manual_rules: 1

## Region Mix

- Latin America: 9
- East Asia: 8
- Eastern Europe: 8
- Africa: 5
- South Asia: 3
- Middle East and North Africa: 2
- Southeast Asia: 2
- Oceania and Pacific: 2

## First 15 Queue Rows

- ICQ001 | Q1 | Biblioteca Nacional Mariano Moreno Digital | Latin America | iiif_manifest_adapter | target 12
- ICQ002 | Q1 | National Diet Library Digital Collections | East Asia | iiif_manifest_adapter | target 12
- ICQ003 | Q1 | Kyoto University Rare Materials Digital Archive | East Asia | iiif_manifest_adapter | target 12
- ICQ004 | Q1 | POLONA | Eastern Europe | iiif_manifest_adapter | target 12
- ICQ005 | Q1 | Slovakiana | Eastern Europe | iiif_manifest_adapter | target 12
- ICQ006 | Q1 | NDL Digital Collections | East Asia | iiif_manifest_adapter | target 12
- ICQ007 | Q1 | Biblioteca Brasiliana Guita e Jose Mindlin | Latin America | dspace_oai_or_rest_adapter | target 12
- ICQ008 | Q1 | UNAM Repositorio Institucional | Latin America | dspace_oai_or_rest_adapter | target 12
- ICQ009 | Q1 | National Repository of Nigeria | Africa | dspace_oai_or_rest_adapter | target 12
- ICQ010 | Q1 | Slovak Digital Library | Eastern Europe | kramerius_adapter | target 12
- ICQ011 | Q1 | Czech Digital Library | Eastern Europe | kramerius_adapter | target 12
- ICQ012 | Q1 | University of Cape Town Digital Collections | Africa | omeka_api_adapter | target 8
- ICQ013 | Q1 | Fundacion IDA Investigacion en Diseno Argentino | Latin America | html_jsonld_adapter | target 8
- ICQ014 | Q1 | CeDInCI Archivo | Latin America | html_jsonld_adapter | target 8
- ICQ015 | Q1 | Mayibuye Archives | Africa | html_jsonld_adapter | target 8

## Execution Rule

Run one adapter family at a time. Each family must write raw source payloads, source-level evidence, image policy, text excerpts, and failure rows. The goal is not to maximize rows; the goal is to prove that each source can produce readable, rights-aware archive surfaces without collapsing back into large-institution sampling.

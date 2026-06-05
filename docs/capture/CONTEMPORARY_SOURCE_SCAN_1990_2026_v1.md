# Contemporary Source Scan 1990-2026 v1

Rights-safe source-level probe. This report records reachability, protocol signals, adapter hints, and next capture priority. It does not create public archive surfaces and does not download or possess source images.

- Access date: 2026-06-05
- Probe rows: 65
- Metrics rows: 85

## Safety Constraints

- IMG01 and IMG03 are never assigned from heuristic, visual, social, or LLM signals.
- IIIF/CONTENTdm/Kramerius evidence can recommend IMG02 only as source-hosted viewing, not reuse.
- Platform and social sources are discovery leads until original sources and rights are reviewed.
- Impact or priority signals are internal triage only, not public authority or inclusion claims.

## Probe Status

- ok: 50
- failed: 11
- http_error: 4

## Next Capture Priority

- P1 adapter build: 22
- P1 text/source enrichment: 18
- P2 retry/manual verification: 15
- P2 discovery lead queue: 8
- P2 manual source review: 2

## Region Mix

- Global: 13
- East Asia: 12
- Southeast Asia: 10
- Latin America: 8
- South Asia: 5
- MENA: 5
- Africa: 5
- Oceania: 3
- Eastern Europe: 2
- Europe: 1
- North America: 1

## Detected Protocols

- Static JS App: 17
- JSON-LD: 15
- RSS/Atom: 14
- WordPress REST: 14
- IIIF: 13
- PDF: 5
- GraphQL: 3
- ArchiveSpace/EAD: 2
- OAI-PMH: 1

## Adapter Hints

- manual_review_or_alternate_endpoint: 15
- wordpress_rest_or_html_adapter: 11
- iiif_manifest_adapter: 9
- discovery_signal_only_no_item_image_ingest: 8
- html_source_probe_then_manual_rules: 7
- headless_metadata_probe_only: 3
- rss_atom_source_adapter: 2
- static_js_or_html_probe: 2
- html_jsonld_adapter: 2
- pdf_text_or_link_adapter: 2
- oai_pmh_adapter: 1
- graphql_schema_probe_then_adapter: 1
- archive_search_probe: 1
- digitalnz_api_or_html_probe: 1

## P1 Candidates

- CSS0001 | Another Graphic | Global / Independent web | RSS/Atom;JSON-LD;WordPress REST;Static JS App | wordpress_rest_or_html_adapter
- CSS0002 | It's Nice That | Global / Independent web | IIIF;RSS/Atom;WordPress REST | iiif_manifest_adapter
- CSS0004 | Slanted | Global / Independent web | RSS/Atom;JSON-LD;WordPress REST;Static JS App | wordpress_rest_or_html_adapter
- CSS0005 | The Brand Identity | Global / Independent web | IIIF;GraphQL;Static JS App | iiif_manifest_adapter
- CSS0006 | BP&O | Global / Independent web | JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- CSS0007 | Fonts In Use | Global / Typography | RSS/Atom | rss_atom_source_adapter
- CSS0008 | People's Graphic Design Archive | Global / Community archive | IIIF;RSS/Atom;PDF | iiif_manifest_adapter
- CSS0009 | Design Reviewed | Europe / Independent archive | RSS/Atom;JSON-LD;WordPress REST;Static JS App | wordpress_rest_or_html_adapter
- CSS0010 | Letterform Archive Blog | North America / Independent archive | JSON-LD;WordPress REST;Static JS App;PDF | wordpress_rest_or_html_adapter
- CSS0016 | JAGDA | East Asia / Japan | WordPress REST | wordpress_rest_or_html_adapter
- CSS0017 | Tokyo Type Directors Club | East Asia / Japan | JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- CSS0018 | Tokyo ADC | East Asia / Japan | Static JS App / HTML | html_source_probe_then_manual_rules
- CSS0019 | Ginza Graphic Gallery | East Asia / Japan | Static JS App / HTML | html_source_probe_then_manual_rules
- CSS0020 | ddd Gallery | East Asia / Japan | Static JS App / HTML | html_source_probe_then_manual_rules
- CSS0022 | Seoul Design Foundation / DDP | East Asia / Korea | Static JS App / HTML | static_js_or_html_probe
- CSS0023 | Korea Design Foundation / Design DB | East Asia / Korea | HTML / Static JS App | html_source_probe_then_manual_rules
- CSS0024 | National Library of Korea Digital Collections | East Asia / Korea | OAI-PMH | oai_pmh_adapter
- CSS0025 | Taiwan Design Research Institute | East Asia / Taiwan | JSON-LD | html_jsonld_adapter
- CSS0027 | M+ Collections | East Asia / Hong Kong | RSS/Atom;GraphQL;Static JS App | graphql_schema_probe_then_adapter
- CSS0028 | DesignSingapore Council | Southeast Asia / Singapore | JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- CSS0029 | National Library Board Singapore / BiblioAsia | Southeast Asia / Singapore | Static JS App | headless_metadata_probe_only
- CSS0030 | Roots.sg | Southeast Asia / Singapore | Static JS App | headless_metadata_probe_only
- CSS0031 | Malaysian Design Archive | Southeast Asia / Malaysia | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- CSS0032 | Grafis Nusantara | Southeast Asia / Indonesia | IIIF;RSS/Atom;JSON-LD;WordPress REST | iiif_manifest_adapter
- CSS0037 | Design Center of the Philippines | Southeast Asia / Philippines | HTML / Static JS App | html_source_probe_then_manual_rules
- CSS0039 | Priya Paul Collection | South Asia / India | IIIF;JSON-LD;Static JS App | iiif_manifest_adapter
- CSS0042 | SADAA | South Asia / Diaspora | IIIF | iiif_manifest_adapter
- CSS0043 | Arabic Design Archive | MENA / Arab world | IIIF;Static JS App | iiif_manifest_adapter
- CSS0046 | Arab Image Foundation | MENA / Levant | RSS/Atom;PDF | rss_atom_source_adapter
- CSS0049 | African Activist Archive | Africa / Pan-African / diaspora | HTML / Search | html_source_probe_then_manual_rules
- CSS0050 | SAHA South African History Archive | Africa / Southern Africa | PDF | pdf_text_or_link_adapter
- CSS0053 | Fundación IDA | Latin America / Southern Cone | IIIF;JSON-LD | iiif_manifest_adapter
- CSS0054 | Diseño Nacional | Latin America / Southern Cone | RSS/Atom;JSON-LD;WordPress REST | wordpress_rest_or_html_adapter
- CSS0055 | Gráfica Latina | Latin America / Latin America | PDF | pdf_text_or_link_adapter
- CSS0056 | La Patria | Latin America / Southern Cone | JSON-LD | html_jsonld_adapter

## Failed Or Manual Retry

- CSS0003 | AIGA Eye on Design | failed | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
- CSS0021 | DNP Graphic Design Archives | http_error | HTTP Error 404: Not Found
- CSS0026 | Taiwan Cultural Memory Bank | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0033 | IVAA Indonesian Visual Art Archive | http_error | HTTP Error 403: Forbidden
- CSS0034 | ASEAN Digital Library | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0036 | Thai Graphic Design Century | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0038 | CIViC Archive | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0040 | Tasveer Ghar | failed | URLError: <urlopen error [Errno 54] Connection reset by peer>
- CSS0041 | Design Dashtahjaat | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0044 | Syrian Design Archive | failed | URLError: <urlopen error timed out>
- CSS0045 | Palestinian Museum Digital Archive | http_error | HTTP Error 429: Too Many Requests
- CSS0051 | Chimurenga Library | failed | URLError: <urlopen error timed out>
- CSS0052 | Africa Commons | http_error | HTTP Error 403: Forbidden
- CSS0057 | Archivo de Ilustración Argentina | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
- CSS0060 | Archivo Mexicano de Diseño | failed | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>

## Next Rule

Promote reachable protocol-family rows into source-family adapters first. Discovery-only rows should become source-registry or edge-source leads, not public image records, until a stable original source and rights basis are available.

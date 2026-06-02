# Contemporary Noise Filter Audit v1

Date: 2026-06-01

This audit applies a reusable contemporary-capture filter to existing 1970-2026 and adjacent late-period capture rows. It is not a deletion list. It marks which rows can proceed toward public surfaces, which should be downgraded to subsheet/card/text candidates, and which should remain discovery-only or review leads.

## Summary

- Rows audited: 281
- Include candidates: 243
- Downgrade candidates: 16
- Review leads: 22
- Discovery-only leads: 0
- Excluded noise candidates: 0

## Decisions

| Decision | Rows |
|---|---:|
| include_candidate | 243 |
| review_lead | 22 |
| downgrade_candidate | 16 |

## Source Families

| Source family | Rows |
|---|---:|
| institutional_api | 122 |
| wordpress | 65 |
| other | 56 |
| contentdm | 30 |
| dspace | 6 |
| omeka | 2 |

## Input Files

| Input file | Rows |
|---|---:|
| `capture_batch_late_period_coverage_1970_2026_records.csv` | 104 |
| `capture_batch_gap_noncanonical_image_text_1930_2000_records.csv` | 58 |
| `capture_batch_edge_wordpress_1970_2026_records.csv` | 40 |
| `capture_batch_source_breadth_1970_2026_records.csv` | 39 |
| `capture_batch_independent_asia_1990_2026_records.csv` | 22 |
| `capture_batch_noncanonical_exact_sources_1970_2000_records.csv` | 10 |
| `capture_batch_protocol_item_1970_2026_records.csv` | 8 |

## Largest Source Contributors

| Source | Rows |
|---|---:|
| Te Papa Collections Online | 56 |
| NAIDOC Poster Gallery | 49 |
| Internet Archive / text and periodical collections | 46 |
| Another Graphic | 14 |
| Malaysia Design Archive | 14 |
| Wikimedia Commons | 11 |
| Auckland Libraries Heritage Collections / CONTENTdm | 10 |
| Desain Grafis Indonesia | 10 |
| Asian Film Archive | 8 |
| Bophana Audiovisual Resource Center | 8 |
| Design Reviewed | 8 |
| NDL Search / National Diet Library | 6 |
| University of Washington Digital Collections / CONTENTdm | 6 |
| Los Angeles Public Library Tessa / CONTENTdm | 5 |
| University of Miami Libraries Digital Collections / CONTENTdm | 5 |
| University of Ghana Digital Collections | 4 |
| SMU Libraries Digital Collections / CONTENTdm | 3 |
| Biblioteca Nacional Digital de Chile / Memoria Chilena | 3 |
| South African History Archive | 3 |
| CeDInCI Archivo | 2 |

## Decision Notes

- `include_candidate` means the row has enough object/provenance language to remain in publication generation, subject to surface-gate thresholds.
- `downgrade_candidate` means the row should usually become a subsheet, text sheet, card, slip, or grouped child rather than a main sheet.
- `review_lead` means the row should stay in capture/research space until corroborated by a stronger object record or local source.
- `discovery_only` is for social/repost platforms and should not become standalone evidence.
- `exclude_noise` identifies likely jobs/events/commerce/policy/admin pages.

## Review Sample

| Decision | Source | Title | Reason |
|---|---|---|---|
| review_lead | AHIRA Archivo Historico de Revistas Argentinas | El siglo XX documentado a través de revistas, una iniciativa dirigida por la ensayista Sylvia Saítta | partial signal; keep as capture lead until corroborated |
| review_lead | Another Graphic | Anh-Đức Lê | partial signal; keep as capture lead until corroborated |
| review_lead | Another Graphic | Minha Kim | partial signal; keep as capture lead until corroborated |
| review_lead | Biblioteca Nacional Digital de Chile / Memoria Chilena | Memoria Chilena Mural de la Brigada Ramona Parra | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Bophana Audiovisual Resource Center | A Presentation of Bophana Center at FIAF 2024 Symposium: Film Archives in the Global South | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | App-learing on Khmer Rouge History | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | Bophana Center to Celebrate World Day for Audiovisual Heritage on October 27th, 2024 | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | Building Capacity for Indigenous Youth and Establishing Indigenous Audiovisual Archives | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | Mekong Discovery Days at the 13th Cambodia International Film Festival | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | Online Exhibition: “Through the Eyes of Jean-Michel GALLET: Exploring Cambodia in Photographs” | partial signal; keep as capture lead until corroborated |
| review_lead | Bophana Audiovisual Resource Center | Partage, 2023 | partial signal; keep as capture lead until corroborated |
| review_lead | CeDInCI Archivo | Políticas de la Memoria en el Núcleo Básico de Revistas Argentinas | partial signal; keep as capture lead until corroborated |
| review_lead | CeDInCI Archivo | ¡Relanzamos AméricaLee con nuevas funcionalidades y más revistas! | partial signal; keep as capture lead until corroborated |
| review_lead | Desain Grafis Indonesia | ASPaC AWARDS 2018: Asia Student Package Design Competition | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Desain Grafis Indonesia | Desain Sebagai Cermin Jiwa: Kontroversi Desain Jersey Timnas dan Identitas Pribadi Sang Desainer | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Desain Grafis Indonesia | Memaknai Desain Grafis sebagai Gagasan Politis | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Desain Grafis Indonesia | Meruangkan Kosong | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Desain Grafis Indonesia | Perjalanan Tujuh Tahun Situs Desain Grafis Indonesia (DGI): 2007–2014 (1) | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Desain Grafis Indonesia | Sugesti Bentuk & Keimanan: Desain Grafis, Grafika yang Berkelanjutan, Vernakular | not enough graphic-design or archive-specific evidence in metadata |
| review_lead | Malaysia Design Archive | 1970 World Exposition – Untitled 055 | partial signal; keep as capture lead until corroborated |
| review_lead | Malaysia Design Archive | 1970 World Exposition – Untitled 056 | partial signal; keep as capture lead until corroborated |
| review_lead | Malaysia Design Archive | BÍCH – silkscreen edition | partial signal; keep as capture lead until corroborated |

## Constraint

Future 1990-2026 captures should call the shared filter before writing publication-ready rows. Rejected rows may still be preserved as source leads, but they must not mint main sheets. This prevents contemporary independent-source expansion from turning into a general design-blog or event-listing scrape.

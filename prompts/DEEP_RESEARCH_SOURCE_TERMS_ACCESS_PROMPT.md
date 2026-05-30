# Deep Research Prompt: Source Terms and Access Review for First Experimental Ingest

Use this prompt to review source terms, access methods, automation feasibility, and image-display constraints before the first controlled ingest of a rights-aware modern graphic design history archive index.

This research is independent. Do not assume the reader has access to previous reports.

## Project Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

It does not replace archives, copy collections, build a course, produce a textbook, or impose a single historical narrative. It indexes and links distributed works, texts, people, institutions, movements, media technologies, places, sources, citations, rights states, and historical nodes back to original sources.

The project prioritizes indexing over possession:

- metadata before images;
- citation before interpretation;
- source links before local copies;
- rights state before display;
- classification with evidence, not visual intuition alone;
- unresolved or uncertain relations must remain visible rather than hidden.

The first controlled ingest scope has been defined as:

- 48 target records;
- 15 movement / formation cells;
- 15 event-node anchors;
- about 15 source families;
- at least 12 launch regions or transregional frames;
- majority non-Euro-American or transregional decolonial/digital material;
- at least one periodical issue/page chain;
- at least one web-archive capture chain;
- source-language metadata must be preserved where available.

## Image Presence Codes

The project uses `IMG00` through `IMG04`.

These are image-presence states, not image sizes.

Image size, crop, paper tier, and frame dimensions are controlled separately by sheet tier, layout ID, and template rules.

| Code | Meaning |
|------|---------|
| `IMG00` | Image frame exists, but no source image is shown. Empty archive frame only: linework/shadow, short rights/source text, source link. Used when image rights are missing, high-risk, unclear, or protocol-sensitive. |
| `IMG01` | Image frame exists and displays a permitted thumbnail only. |
| `IMG02` | Image frame exists and displays permitted embed / IIIF / source-served image. |
| `IMG03` | Image frame exists and displays open image with item-level OA / CC0 / public-domain / open-license evidence. |
| `IMG04` | No image frame. Pure text page, appendix, continuation page, citation page, registry page, or other page with `has_image_frame = false`. This is a script/template signal, not a copyright level. |

`IMG00` through `IMG03` assume an image frame exists and are resolved by copyright/display permission. `IMG04` means no image frame.

Unknown or ambiguous image rights default to `IMG00`.

## First-Ingest Cells

Review terms and access for sources needed by these cells:

| Cell | Movement / event | Target count | Main sources |
|------|------------------|--------------|--------------|
| C01 | Bauhaus / 1919 founding | 4 | The Met Open Access, Smithsonian / Cooper Hewitt, Internet Archive, authority sources |
| C02 | Polish Poster School | 2 | Poster Museum at Wilanow, Culture.pl, V&A, PGDA, authority sources |
| C03 | IBM corporate design | 4 | IBM History, Cooper Hewitt, PGDA, Letterform Archive, authority sources |
| C04 | Taller de Grafica Popular | 4 | The Met, MoMA, Internet Archive, authority sources |
| C05 | Brigadas Ramona Parra | 3 | Memoria Chilena, Chilean archive/authority sources |
| C06 | World Design Conference 1960 / NDC | 4 | M+, Nippon Design Center, NDL Search, Internet Archive |
| C07 | Shanghai Sketch / yuefenpai | 4 | Internet Archive, British Museum, authority sources |
| C08 | Minjung / Kwangju posters | 3 | Library of Congress, authority sources, Korean collection sources |
| C09 | Singapore multilingual posters/logotypes | 3 | NLB Singapore OneSearch, BiblioAsia |
| C10 | NID development communication | 3 | NID, Internet Archive, authority sources |
| C11 | Iranian modern poster design | 2 | Encyclopaedia Iranica, Internet Archive, authority sources |
| C12 | Medu / Culture and Resistance | 4 | South African History Archive, South African History Online |
| C13 | NAIDOC / land-rights posters | 3 | AIATSIS, Trove/NLA, NAIDOC |
| C14 | Gran Fury / ACT UP | 3 | ACT UP Oral History Project, MoMA, National Library of Medicine |
| C15 | Early web / CSS / GeoCities | 2 | CERN, W3C, Wayback Machine, Internet Archive |

## Research Goal

Determine whether each source can be used for first experimental ingest, and under what restrictions.

Focus on:

- source terms of use;
- API terms;
- robots.txt or crawl restrictions where relevant;
- rate limits;
- API-key requirements;
- whether automated metadata ingest is permitted;
- whether manual metadata seeding is safer;
- whether thumbnails/previews may be displayed;
- whether IIIF/embed use is allowed;
- whether open images can be locally displayed;
- whether cultural protocol, privacy, or community restrictions apply;
- whether source links/citations are stable enough.

Do not select final records in this report. This report is about source feasibility and access policy only.

## Required Output

Produce a structured report with these sections.

### 1. Executive Decision

State:

- `SOURCE_TERMS_READY_FOR_FIRST_INGEST: yes/no/yes_with_conditions`
- whether automated metadata ingest is possible for any sources;
- which sources must be manual-only;
- which sources must remain `IMG00`;
- which sources may support `IMG01`, `IMG02`, or `IMG03`;
- which sources should be blocked for now.

### 2. Source Terms Matrix

Use this table:

| Source | URL | Cell(s) | Access method | Terms URL | API/robots URL | API key? | Automation status | Rate limits | Metadata ingest allowed? | Image display allowed? | Recommended IMG state | Manual review required? | Notes |

Use `automation_status` values:

- `api_allowed`
- `api_allowed_with_key`
- `manual_only`
- `link_only`
- `blocked`
- `unknown_requires_review`

Use recommended image states:

- `IMG00`
- `IMG01`
- `IMG02`
- `IMG03`
- `IMG04` only if the source is text-only or the page is a pure text source page.

### 3. Source-Specific Notes

For each source, provide:

- what can be indexed safely;
- what must not be copied;
- whether thumbnails are permitted;
- whether IIIF/embed exists and is usable;
- whether open-image display is possible;
- what evidence must be captured in `source_terms_reviews`;
- takedown/contact/permission path if available.

### 4. Risk Categories

Use this table:

| Risk type | Affected sources | Recommended policy | Reason |

Include:

- object-level rights variation;
- metadata-open but image-restricted sources;
- community archive restrictions;
- Indigenous Cultural and Intellectual Property / protocol-sensitive materials;
- political sensitivity;
- web archive copyright ambiguity;
- corporate/commercial archive rights;
- crowd-sourced provenance uncertainty.

### 5. Terms Review Rows

Return machine-usable draft rows for `source_terms_reviews`.

Use this table:

| source_name | decision | key_clauses | image_reuse_summary | thumbnail_reuse_summary | iiif_summary | prohibited_uses | rate_limit_summary | commercial_use_summary | takedown_contact | recheck_needed |

Decision values:

- `approved_metadata_only`
- `approved_thumbnail_only`
- `approved_iiif_embed_only`
- `approved_open_image`
- `link_only`
- `manual_review_required`
- `blocked`

### 6. Source Registry Patch Recommendations

Return machine-usable recommendations for `data/source_registry.csv`:

```text
source_id or source_name
- automation_status:
- rights_basis:
- record_level_rights_required:
- default_image_zone:
- preview_allowed:
- thumbnail_allowed:
- iiif_capable:
- api_key_required:
- protocol_sensitive:
- notes:
```

### 7. Blockers Before Ingest

List exact blockers:

| Source | Blocker | Required action before ingest |

### 8. Final Flags

End with:

- `FIRST_INGEST_SOURCE_ACCESS_READY: yes/no/yes_with_conditions`
- `CAN_AUTOMATE_METADATA_FOR: ...`
- `MANUAL_ONLY_SOURCES: ...`
- `BLOCKED_SOURCES: ...`
- `IMG00_REQUIRED_SOURCES: ...`
- `IMG01_POSSIBLE_SOURCES: ...`
- `IMG02_POSSIBLE_SOURCES: ...`
- `IMG03_POSSIBLE_SOURCES: ...`
- `SOURCE_TERMS_ROWS_REQUIRED_BEFORE_FETCH: ...`

## Output Style

Be precise and operational. Cite source terms pages or policy pages. Do not write a general essay. Do not recommend frontend visuals. Do not select final target records.

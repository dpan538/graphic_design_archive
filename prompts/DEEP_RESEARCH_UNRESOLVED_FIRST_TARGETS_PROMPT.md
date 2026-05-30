# Deep Research Prompt: Resolve Unconfirmed First-Ingest Targets for a Rights-Aware Graphic Design History Archive

## Project Context

This project is a rights-aware archive index and automated archive workflow for modern graphic design history.

It does not replace archives or copy collections. It builds a research gateway by verifying source records, preserving citations, separating source metadata from normalized metadata, recording rights/protocol evidence, and generating public archive sheets from database records.

The system uses these image states:

- `IMG00`: image frame exists, but no image is displayed because rights are absent, unclear, high-risk, or unreviewed.
- `IMG01`: permitted thumbnail.
- `IMG02`: permitted source-hosted viewer/embed/IIIF.
- `IMG03`: open/reusable image with license and credit evidence.
- `IMG04`: no image frame; text/authority/event/appendix page.

The first 48 target records have already been selected. A mechanical verification pass found that most are ready for manual metadata ingest, but a subset still needs exact URLs, browser checks, source replacement, page-level locators, or item-level rights evidence.

## Research Goal

Resolve only the unresolved first-ingest targets listed below.

Do not rewrite the whole first-ingest scope. Do not write a design history essay. The output must be operational: exact stable URLs, source metadata, rights evidence, and an ingest decision.

## Unresolved Targets

| Target | Current issue |
|---|---|
| FIT002 | Harvard preliminary Bauhaus object target needs exact record confirmation. |
| FIT004 | Harvard Bauhaus chronology/tour slide is blocked or unstable in automated fetch. |
| FIT015 | Biblioteca Nacional Digital de Chile BRP target is search-path only. |
| FIT016 | Biblioteca Nacional Digital de Chile BRP target is search-path only and creator/subject relation is unclear. |
| FIT017 | MMDH / Brigada Ramona Parra 1971 poster context needs stable object or collection page. |
| FIT018 | NDL exact URL for World Design Conference proceedings needs confirmation. |
| FIT019 | NDL companion report needs exact persistent URL. |
| FIT023 | Internet Archive Shanghai Sketch issue 5 page 7 needs exact page locator and content-role confirmation. |
| FIT024 | Internet Archive Shanghai Sketch issue 5 page 8 needs exact page locator and ad-page confirmation. |
| FIT026 | Original OpenArchive Korean target was not confirmed; possible replacement is Seoul Museum of Art Archive record `MA-06-00004326`. |
| FIT027 | Kdemo record `00976552` needs exact item page URL or stable citation path. |
| FIT028 | Kdemo Hong Sung-dam oral archive page needs browser/source confirmation because automated fetch returned 404. |
| FIT030 | NAS multilingual sign target hit anti-bot page; confirm exact record and access/reproduction terms. |
| FIT031 | NAS Stamp Design Committee government record needs browser/source confirmation. |
| FIT034 | NID Young Designers 07 project page needs confirmation and rights status. |
| FIT036 | PGDA Iranian Poster Design collection needs one exact item target or should remain collection-level only. |
| FIT038 | SAHA `AL2446/4930` exact Medu item needs confirmation or replacement. |
| FIT048 | OoCities Dream Archive / Wayback target needs exact preserved page and capture chain. |

## Required Output

### 1. Executive Decision

Give:

- `UNRESOLVED_TARGETS_RESOLVED: yes/no/partially`
- `READY_AFTER_THIS_REVIEW: number`
- `STILL_SEARCH_PATH_ONLY: number`
- `RECOMMENDED_REPLACEMENTS: number`
- `BLOCKED_OR_DEFER: number`

### 2. Target Resolution Table

Use this table:

| Target | Decision | Exact stable URL | Canonical citation URL | Source identifier | Source title | Creator / institution | Date | Record family | Confirmed IMG | Rights evidence | Required action |

Decision values:

- `ready_manual_ingest`
- `ready_link_only`
- `replace_target`
- `keep_search_path_only`
- `browser_only_review_needed`
- `defer`
- `block`

### 3. Rights and Terms Evidence

For each target that becomes ready, provide:

| Target | Rights text summary | Rights URL or page section | Image display decision | Local-copy decision | Credit / attribution requirement | Notes |

Important:

- If image rights are unclear, use `IMG00`.
- If the source only allows viewing but not reproduction, use `IMG02`.
- If the page is text-only or authority/event/institutional, use `IMG04`.
- Do not upgrade to `IMG03` unless a clear license or public-domain/open-reuse statement is present.

### 4. Replacement Recommendations

Where a better source exists, use:

| Original target | Replacement source | Replacement URL | Why better | Record family | IMG | Rights risk |

Specifically evaluate the Seoul Museum of Art Archive record:

- title: `1988년 《한국민중판화모음전》 포스터`
- URL: `https://sema.seoul.go.kr/semaaa/front/archive/view.do?iId=21227`
- identifier: `MA-06-00004326`

### 5. Page-Level Locator Confirmation

For FIT023 and FIT024, provide:

| Target | Parent issue URL | Exact page/canvas/file locator | Page role | Evidence | Recommended child record label |

Do not invent page roles. If the page cannot be confirmed as text/ad material, say so.

### 6. Web Capture Chain

For FIT048, provide:

| Target | Preserved page URL | Original URL if recoverable | Wayback capture URL | Capture date | Rights risk | Recommended IMG |

### 7. Final Machine-Actionable Patch

Return a JSON array with this shape:

```json
[
  {
    "first_target_id": "FIT000",
    "verification_decision": "",
    "canonical_url": "",
    "replacement_url": "",
    "confirmed_image_zone": "IMG00",
    "evidence_summary": "",
    "required_action": "",
    "blocking_reason": ""
  }
]
```

## Constraints

- Do not treat search snippets as final evidence unless no better source is available and the record is explicitly marked search-path-only.
- Do not use image visibility as rights evidence.
- Do not recommend automated scraping unless source terms explicitly support it.
- Prefer exact source records over collection-level pages.
- Preserve original-language titles and identifiers.

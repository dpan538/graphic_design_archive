# Search field matrix

The matrix was measured against the frozen candidate payload whose canonical SHA-256 is `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`. Public eligibility is the existing non-inferential policy `trace.tier === "source_verified"`: 7,995 public objects are eligible and 7,928 records remain held.

| Canonical field | Database source | Public API/read-model source | Policy | Search text | Filter | Result card | Coverage | Null/missing semantics | Normalisation | Alias policy | Rights/privacy restriction | Implementation status |
|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| `stable_id` | `release.research_surface_presentation_projection_v3.public_surface_id`; legacy v1 `api_v1.sealed_surface.surface_id` | `surfaces[].surfaceId`; `/api/v1/releases/{release}/surfaces/{surfaceId}` | public only | yes | no | yes | 7,995 / 7,995 (100%) | Required; missing rejects the document | NFKC + case fold for exact lookup; display preserved | No inferred aliases; exact public ID only | Never exposes internal UUID/object URN | implemented v2 |
| `title` | `release.research_surface_presentation_projection_v3.title` | `surfaces[].title`; `SurfaceSummary.title` | public only | yes | no | yes | 7,995 / 7,995 (100%) | Required; missing rejects the document | NFC/NFKC, punctuation/separator folding, safe Latin diacritic fold | No generated title aliases | Public presentation title only | implemented v2 |
| `credited_label` | `release.research_surface_credit_projection_v3.credited_label` | `surfaces[].creator`; `SurfaceSummary.creditedLabels` | public where available | yes | no | yes | 5,653 / 7,995 (70.71%) usable | Explicit unknown, anonymous, unattributed, unidentified, `Ukjent`, `Inconnu`, `N/A`, and empty values become `null`/`[]` | Same lexical channels as title; display preserved | No authority expansion, nationality inference, or generated studio alias | Source-reported public credit only; held agent notes excluded | implemented v2 |
| `display_date` | `release.research_surface_presentation_projection_v3.display_date` | `surfaces[].dateText`; `SurfaceSummary.displayDate` | public only | no | no | yes | 7,995 / 7,995 (100%) | Display string preserved; no fabricated replacement | Trim only | None | Public presentation value only | implemented v2 |
| `year_range` | `release.research_surface_presentation_projection_v3.normalized_year` plus sealed range projection where present | `surfaces[].dateStart`, `surfaces[].dateEnd`; `SurfaceSummary.year` | public only | no | yes | yes | start 7,995 / 7,995 (100%); end 7,923 / 7,995 (99.10%) | Missing end uses start for interval comparison; no year is inferred from prose | Integer bounds; inclusive overlap filter; 1800–2026 current dictionary | No decade aliases in core data; UI ranges compile to numeric bounds | Public normalised dates only; raw/review dates excluded | implemented v2 |
| `place` | `release.research_surface_presentation_projection_v3.place_label` | `surfaces[].placeText`; `SurfaceSummary.placeLabel` | public only | yes | no | yes | 7,995 / 7,995 (100%) | Empty stays `null`; no repository/creator geography substitution | Same lexical channels as title; display preserved | No geocoding, geopolitical rewrite, or inferred place alias | Existing object-geography authority boundary applies | implemented v2 |
| `object_type` | `release.research_surface_presentation_projection_v3.type_label` | `surfaces[].objectType`; `SurfaceSummary.typeLabel` | public only | no | yes | yes | 7,995 / 7,995 (100%); 90 current values | Empty stays `null`; no generic placeholder | Trim + canonical dictionary ID; display preserved | Case variants remain distinct source values unless an existing canonical value binds them | Accepted public classification only | implemented v2 |
| `theme` | `release.research_folder_projection_v3` + accepted `release.research_folder_membership_projection_v3` where `folder_type_code='theme'` | `surfaces[].folders[type=theme]` | public accepted memberships only | no | yes | yes | 7,995 / 7,995 (100%); 8 current values | Empty array means no public theme | Canonical folder ID/title; deterministic code-point order | Existing folder identity only | No model inference; held/review assignments excluded | implemented v2 |
| `movement` | `release.research_folder_projection_v3` + accepted `release.research_folder_membership_projection_v3` where `folder_type_code='movement'` | `surfaces[].folders[type=movement]` | public accepted memberships only | no | yes | yes | 110 / 7,995 (1.38%); 7 current values | Empty array is expected and displayed as absent | Canonical folder ID/title; deterministic code-point order | Existing folder identity only | No model inference; sparse coverage must remain visible | implemented v2 |
| `source_collection` | `release.research_surface_presentation_projection_v3.source_label` and allowlisted public citation projection | `surfaces[].sourceName`; `SurfaceSummary.sourceLabel` | public result metadata only | no | no | optional | 7,995 / 7,995 (100%) | Empty stays `null`; no placeholder | Trim; display preserved | None | No raw locator, private note, or held collection text | implemented v2 result metadata |
| `public_description` | `release.research_surface_presentation_projection_v3.description` | `surfaces[].descriptionSummary`; `SurfaceDetail.description` | public detail only | no | no | no | 7,995 / 7,995 (100%) | Empty stays `null`; never filled from notes | Trim only | None | Not indexed or sent to guidance; private source notes excluded | audited, intentionally not indexed |

## Exact Search policy

```text
SEARCHABLE_FIELDS=stable_id,title,credited_label,place
FILTERABLE_FIELDS=year_range,object_type,theme,movement
RESULT_CARD_FIELDS=stable_id,title,credited_label,display_date,year_range,place,object_type,theme,movement,source_collection,delivery_state,object_route,match_explanation
PUBLIC_SEARCH_DOCUMENT_COUNT=7995
SOURCE_HELD_RECORD_COUNT=7928
HELD_SEARCH_DOCUMENT_COUNT=0
TRACE_RECORD_IN_SEARCH_INDEX_COUNT=0
OPEN_INQUIRY_RECORD_IN_SEARCH_INDEX_COUNT=0
```

The machine-readable equivalent is `docs/search/search-field-matrix.v1.json`.

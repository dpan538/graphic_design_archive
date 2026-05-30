# Design System / Database Audit v0

**Date:** 2026-05-29  
**Status:** First normalization pass started.  
**Scope:** Archive-cabinet public interface system mapped against the current database skeleton.

## Position

The current design system is a rights-aware archive-cabinet interface for a modern graphic design history index. It is not a product brand, course site, museum education layer, or visual storytelling site.

The system uses:

- cabinet / drawer / folder / loose-leaf / appendix / card / registration card / bookmark metaphors;
- 1-bit, high-contrast, grid-first visual language;
- fixed paper tiers and reusable layout templates;
- source-first, citation-first, rights-first rendering;
- one global publication sequence (`SEQ`);
- historical nodes and movements as folder/filter views, not duplicated containers.

## Database Support Already Present

| Design-system need | Current support | Notes |
|---|---|---|
| Historical drawers | `historical_nodes` | Stable `HN*` nodes exist. |
| Movement folders | `movements`, `regional_movements`, `classifications` | Canonical and regional formations now both exist. |
| Source metadata | `sources`, `source_records`, `source_record_snapshots` | Source fields are separable from normalized fields. |
| Normalized entities | `entities` | Needs reviewed conversion from source records after first experimental ingest. |
| Citations | `citations` | Strong enough for first manual and experimental records. |
| Rights stickers | `rights_reviews`, `rights_strategies`, `image_assets` | Rights state and display policy exist. |
| Relations | `assertions`, `assertion_reviews`, `relation_predicates` | Can support warning styles for low confidence and `visually_resembles`. |
| Classification | `classifications`, `classification_schemes`, `classification_axes` | Classification exists, but display registry needed a dedicated layer. |
| Geography/date filters | `geographies`, `entity_geographies`, `source_record_geographies`, `normalized_dates` | Global coverage baseline is now represented. |
| Search excerpt strips | `searchable_documents`, `api_search_documents` | Deterministic seed search exists. |

## Gaps Found

| Gap | Why it matters | Normalization response |
|---|---|---|
| Global `SEQ` was missing | Files/folders cannot share one public order without it. | Added `publication_surfaces.seq_int` and `seq_label`. |
| Display number was missing | Public citation/reading needs `GD / ERA / HN / MV|NONE / SEQ / TIER-pPAGE`. | Added `publication_surfaces.display_number` and per-page display number. |
| Sheet/card distinction was not explicit | Sparse stubs and publishable sheets need different workflows. | Added `publication_surface_type` and `sparse_cards`. |
| `TIER + layout_id` had no database home | Template rendering cannot be deterministic without stored assignment. | Added `tier`, `layout_id`, `display_templates`, and `display_profile`. |
| Multi-page sheets were not modeled | Appendices and overflow pages need `p02`, `p03`. | Added `publication_surface_pages`. |
| Six fixed table systems had no row mapping | UI tables need source/normalized/rights/classification/relation/citation rows. | Added `surface_table_rows` with `surface_table_kind`. |
| Folder-as-filter was only conceptual | Historical and movement folders must query same records, not copy them. | Added `folder_views` and `folder_memberships`. |
| Registration card was missing | Classification events need a visible ledger and member list. | Added `filing_registry_cards` and `filing_registry_members`. |
| Bookmark had no stable object | Pre-authored method notes need stable IDs and targets. | Added `archive_bookmarks`. |
| Image zone was not normalized | Rights-driven image behavior cannot be arbitrary in frontend. | Added `image_zone_code` and `publication_surfaces.image_zone`. |

## First Normalization Pass

Implemented in `db/006_publication_surface_skeleton.sql`.

New table families:

- `display_templates`
- `publication_surfaces`
- `publication_surface_pages`
- `surface_table_rows`
- `folder_views`
- `folder_memberships`
- `filing_registry_cards`
- `filing_registry_members`
- `sparse_cards`
- `archive_bookmarks`

New read models:

- `api_publication_surfaces`
- `api_publication_surface_pages`
- `api_surface_table_rows`
- `api_folder_views`
- `api_folder_memberships`
- `api_filing_registry_cards`
- `api_filing_registry_members`
- `api_sparse_cards`
- `api_archive_bookmarks`

## Working Display Number Grammar

```text
GD / {ERA} / {HN} / {MV|NONE} / {SEQ} / {TIER}-p{PAGE}
```

This grammar is now represented as:

- `ERA`: `publication_surfaces.era_text`
- `HN`: `publication_surfaces.primary_historical_node_id`
- `MV|NONE`: `publication_surfaces.movement_display`
- `SEQ`: `publication_surfaces.seq_int` / `seq_label`
- `TIER`: `publication_surfaces.tier`
- `PAGE`: `publication_surface_pages.page_label`
- full display string: `display_number`

The display number is a public reading/citation number. It does not replace internal IDs such as `ENT*`, `SR*`, or table primary keys.

## Current Boundary

This pass does not decide final visual dimensions, grid unit, exact layouts, or template assignment algorithms. Those require first experimental records.

The next practical test is:

1. create 20-30 manual or experimental source records;
2. normalize them into entities/source records/citations/rights/classifications;
3. assign provisional `SEQ`, `TIER`, `layout_id`, `image_zone`;
4. render the six table kinds from real rows;
5. evaluate which fields are too long, missing, ambiguous, multilingual, image-blocked, or relation-heavy.

Only after that should the visual archive Deep Research prompt be rewritten.

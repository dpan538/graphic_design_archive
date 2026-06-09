# Asset Freeze: 2026-05-31

## Description

This checkpoint freezes the archive project's first digital-asset direction:
minimal, information-bearing print-adjacent assets for bookmarks, cards, and
badges. The goal is to preserve the design rules and implementation entry
points before the next round of interface or asset work changes the surface.

The assets are intentionally treated as archive specimens. They should show
design capability while remaining restrained, useful, and tied to real archive
data.

## What Changed

### Bookmark Assets

- Established vertical and horizontal bookmark studies.
- Added small pure-color folder-dot treatment for folder identity.
- Kept bookmark palettes within a controlled same-family tone system.
- Used real archive payload fields for title, source, date, folder, and record
  detail tests.

### Card Assets

- Developed the card system beyond small decorative cards into higher-capacity
  archive cards.
- Added explicit layout constraints for every card family.
- Separated regular card families from rare special physical-format cards.
- Documented special-card placement weight, target share, and maximum share.
- Added rights-aware image-state behavior for missing or restricted images.
- Preserved the approved neutral card group and added color and special-card
  routes for review.

### Badge Assets

- Reduced the badge system to the strongest two groups.
- Removed repeated or similar badge silhouettes.
- Removed Chinese and Korean badge groups from the selected release.
- Kept English, Japanese, Devanagari, Spanish, and symbol marks.
- Added rules that prevent clipped inner frames and require content-safe
  layering.
- Froze badge usage until a clearer placement model exists.

### Design System

- Replaced the earlier asset colors with the open-library / printed-ephemera
  palette now used by the frontend.
- Brown Black is the only black. Region, Theme, Medium, and Movement use index
  colors; card, ticket, stamp, slip, proof, and stock treatments use ephemera
  colors.
- Preserved small, textless color dots as folder membership markers.

## Implementation Pointers

| Asset | Entry points | Rule file |
|---|---|---|
| Bookmarks | `frontend/src/components/archive/bookmarks/BookmarkLab.tsx` | Documented in this freeze |
| Cards | `frontend/src/components/archive/cards/CardLab.tsx` | `frontend/src/components/archive/cards/CARD_LAYOUT_CONSTRAINTS.md` |
| Badges | `frontend/src/components/archive/badges/BadgeLab.tsx` | `frontend/src/components/archive/badges/BADGE_SYSTEM_RULES.md` |

## Freeze Rules

- Do not expand badge groups until the project knows where badges will be used.
- Do not use special physical-card formats as regular card defaults.
- Do not replace real archive content with abstract decoration.
- Do not use image placeholders as fake photographs; use explicit image-state
  graphics for restricted or unavailable images.
- Keep future changes compatible with the current layout constraint documents.

## Validation

- Frontend production build passed after the latest asset work.
- The freeze excludes unrelated capture data and unrelated page edits that were
  present in the working tree.

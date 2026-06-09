# Digital Asset Archive

Freeze date: 2026-05-31

This folder freezes the current digital-asset studies for the graphic design
archive project. The assets are working design systems for archive-facing
ephemera: bookmarks, cards, and badges. They are part of the project identity
and specimen layer, not general-purpose UI decoration.

## Asset Families

### 1. Bookmarks

- Source component: `frontend/src/components/archive/bookmarks/BookmarkLab.tsx`
- Routes: `/bookmarks`, `/bookmarks/vertical`, `/bookmarks/horizontal`
- Status: usable study, frozen for reference

The bookmark system contains three vertical and three horizontal layouts with
different proportions. Bookmarks use real archive fields, three same-family
paper tones, and small pure-color folder dots. The folder color marker is a
badge-like dot only; it carries no text and should stay visually secondary.

Use bookmarks as reading markers, archive slips, collection inserts, and
print-adjacent navigation assets.

### 2. Cards

- Source component: `frontend/src/components/archive/cards/CardLab.tsx`
- Routes: `/cards`, `/cards/square`, `/cards/rectangle`, `/cards/color`,
  `/cards/special`
- Rules: `frontend/src/components/archive/cards/CARD_LAYOUT_CONSTRAINTS.md`
- Status: active design system, with special proportions frozen as rare assets

Cards are the primary high-information digital assets. They must carry enough
record information to stand alone in an archive view. The approved card system
contains regular neutral cards, color cards, and a small set of special
physical-format cards.

Special physical-format cards are intentionally low-priority and low-frequency.
They are used only when the content benefits from a physical reference such as
stamp, ticket, pass, or dossier. Shape alone is not a valid reason to use them.

When a record has `IMG00` or another restricted image state, the layout should
use a rights-aware graphic surrogate or image-state frame rather than pretending
that a photograph exists.

### 3. Badges

- Source component: `frontend/src/components/archive/badges/BadgeLab.tsx`
- Route: `/badges`
- Rules: `frontend/src/components/archive/badges/BADGE_SYSTEM_RULES.md`
- Status: frozen experimental asset

Badges are symbolic archive marks. The current release keeps only two groups of
eight: core English archive-control labels and a mixed global/symbol file-mark
set. They are not folder-color dots and should not replace folder membership
markers.

Badge usage is intentionally frozen for now. They may later appear as special
file marks, appendix covers, export stickers, collection packets, or project
ephemera, but they should not be promoted into regular record UI until the usage
model is clearer.

## Design-System Notes

- The current frontend palette is an open-library / printed-ephemera system:
  bright paper base, Brown Black ink, four index colors, and a separate
  ephemera stock layer.
- Folder membership markers remain small pure-color dots and must use index
  colors only: Region, Theme, Medium, and Movement.
- Card, ticket, stamp, proof, and slip treatments may use ephemera colors, but
  those colors must not replace folder-axis semantics.
- Layouts should stay clean, minimal, and information-bearing.
- Decorative shape, color, or texture is never enough by itself; each asset must
  clarify archive content or project identity.

## Current Freeze Summary

This freeze captures:

- Bookmark layouts for vertical and horizontal archive slips.
- Card families with content constraints and placement priority rules.
- Special-card probability limits for rare physical-format assets.
- Badge release rules with two selected groups and shape/content constraints.
- The project color additions needed by the digital-asset system.

The source code remains in the frontend so the assets can be viewed and revised.
This folder is the independent project-asset index for the current state.

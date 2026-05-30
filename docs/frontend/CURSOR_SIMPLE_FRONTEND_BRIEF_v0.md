# Cursor Simple Frontend Brief v0

**Project:** Rights-aware archive index and research gateway for modern graphic design history.  
**Frontend goal:** Build a minimal public reading prototype that renders the archive box system from static mock data.  
**Do not build:** ingestion, crawling, WebLLM, authentication, admin tooling, graph visualization, or a teaching/course site.

## Context

This project is not a design-history textbook, museum education site, inspiration gallery, or linear timeline.

It is a rights-aware archive index. The interface should feel like opening an archive box, choosing a folder, and reading fixed-format sheets, cards, stubs, appendices, and source links.

The frontend must preserve:

- source return;
- rights state;
- citation/access date;
- uncertainty;
- image display restrictions;
- folder membership;
- stable record identity.

The frontend must not imply that the project owns museum/archive material.

## Build Target

Create a simple frontend app in a new `/frontend` directory.

Recommended stack:

- Next.js App Router
- TypeScript
- plain CSS modules or global CSS
- no external UI framework required
- optional icon package only if already convenient

Static data source for v0:

- use `/data/public_surface_mock_v0.json` as the source mock;
- copy it into `frontend/public/data/public_surface_mock_v0.json` during setup, or import it directly if the build allows.

Also read `FRONTEND_FIELD_DECISIONS_v1.md`. It supersedes older HN-folder and HN-display-number language in previous documents.

Also read `SURFACE_FIELD_CONTRACT_v1.md`. It is the frozen field contract for surface payloads and six-table content.

## Required Routes

```txt
/
/folders
/folders/[type]
/folders/[type]/[slug]
/surfaces/[id]
/search
```

### `/`

Archive box overview.

Show:

- project title;
- short subtitle: `Rights-aware archive index for modern graphic design history`;
- global counts: folders, surfaces, sources, IMG states;
- folder type rail: Region, Theme, Medium, Movement;
- search placeholder input.

The page should feel like a box/cabinet entry, not a landing-page hero.

### `/folders`

List the four folder types.

Each type should show:

- type name;
- count;
- short scope note;
- type color used only on tab/edge/label.

### `/folders/[type]`

List folders within one type.

Each folder row/card should show:

- folder title;
- date span;
- member count;
- IMG state counts;
- surface type counts;
- last verified or staged status.

### `/folders/[type]/[slug]`

Folder cover + folder index.

Important:

- folders are filters/aggregations, not containers;
- the same surface can appear in multiple folders;
- default sort is chronological;
- folder color can appear on the tab/edge only;
- folder choice must not change sheet layout.

Show:

- folder tab;
- title;
- folder type;
- date span;
- scope note;
- chronological index of surfaces;
- status chips for sheet/card/stub/appendix;
- IMG00-IMG04 counts;
- source count;
- related folders if present.

### `/surfaces/[id]`

Render one public surface payload.

Support at least:

- `sheet.main.v0`
- `sheet.img00.v0`
- `sheet.text.v0`
- `card.sparse.v0`
- `stub.fallback.v0`

Every surface must show:

- display number or provisional display label;
- surface type;
- title;
- date;
- creator/agent if available;
- folder memberships;
- rights stamp;
- source return action;
- citation/access date;
- image zone behavior;
- table modules.

### `/search`

Static local search only.

Show:

- search input;
- note that local WebLLM/query expansion is reserved for a later version;
- deterministic results from static mock data if a query is typed.

Do not call an LLM API.

## Core Rendering Rules

### Time

Time is a sorting axis, not a container.

Region, Theme, Medium, and Movement folders all sort their contents chronologically by default.

### Folder Types

Only these four public folder types exist in v0:

| Type | Route key | Color use |
|------|-----------|-----------|
| Region | `region` | tab / edge / small label |
| Theme | `theme` | tab / edge / small label |
| Medium | `medium` | tab / edge / small label |
| Movement | `movement` | tab / edge / small label |

Folders may have distinct colors. Records do not change color by folder.

Historical nodes (`HN*`) are not public folder types. Do not create `/folders/historical-node`, a historical-node rail, or HN tabs.

Public display numbers use:

```txt
GD / {ERA} / {SEQ} / {TIER}-p{PAGE}
```

Do not add `HN` or movement IDs back into display-number chrome.

### Main Sheet Threshold

A main sheet is only shown when the payload says it is eligible.

Do not calculate eligibility in the frontend in v0. Read:

- `surfaceType`;
- `templateId`;
- `completenessScore`;
- `reviewGates`.

General meaning:

- `>= 60` plus essential gates: sheet.
- `45-59`: sparse card.
- `25-44`: fallback stub.
- below that: unassigned/proposed internal item, not a full sheet.

### IMG00-IMG04

Image state controls image display, not sheet size.

| Code | Frontend behavior |
|------|-------------------|
| `IMG00` | Render image bay, but do not render source image. Show empty frame, linework/hatch/shadow, rights note, and source link. |
| `IMG01` | Render constrained thumbnail only when provided by mock payload. Do not upscale. |
| `IMG02` | Render source-hosted/IIIF/embed placeholder if provided; otherwise show source viewer action. |
| `IMG03` | Render open image only if payload includes image URL and license evidence. Show credit/license. |
| `IMG04` | No image bay at all. Use text/table-only layout. |

Unknown image state defaults visually to `IMG00`.

## Visual Direction

Use the archive box / folder / sheet metaphor.

Design tone:

- high contrast;
- 1-bit leaning;
- functional;
- document-like;
- tabbed folders;
- fixed sheets;
- visible linework;
- restrained texture if desired, but no heavy decoration.

Avoid:

- marketing hero layout;
- gallery masonry;
- decorative card grid as the main experience;
- large gradient backgrounds;
- AI-chat-first interface;
- timeline-as-main-product;
- in-app educational narration.

Text labels should be English in the interface.

Source titles may preserve original language.

## Component Checklist

Create these components:

- `ArchiveBoxFrame`
- `FolderTypeRail`
- `FolderTypeIndex`
- `FolderCover`
- `FolderIndex`
- `ChronologyDivider`
- `SurfaceStrip`
- `SurfacePage`
- `ImageZone`
- `RightsStamp`
- `SourceReturn`
- `SurfaceTables`
- `SparseCard`
- `FallbackStub`
- `SearchPlaceholder`

Static search should inspect surface title, creator, date, place, source name, folder title, and table row values from the mock JSON.

## Data Contract

Use the mock JSON as the frontend contract.

Top-level shape:

```ts
type PublicSurfaceMock = {
  meta: {
    generatedAt: string
    status: "mock"
    note: string
  }
  folderTypes: FolderType[]
  folders: Folder[]
  surfaces: Surface[]
}
```

Cursor should keep types in `frontend/src/types/archive.ts`.

## Done Criteria

The first frontend version is done when:

- all required routes render;
- folder pages aggregate the mock surfaces;
- surface pages correctly distinguish sheet/card/stub;
- IMG00 renders an empty image frame;
- IMG04 renders no image frame;
- source return and rights stamp are visible on every surface;
- search route is a placeholder and does not call any LLM;
- layout works on desktop and mobile without overlapping text.

## Files To Read Before Coding

Read these project files before implementing:

- `FRONTEND_FIELD_DECISIONS_v1.md`
- `SURFACE_FIELD_CONTRACT_v1.md`
- `ARCHIVE_BOX_SYSTEM_SPEC_v0.md`
- `PUBLIC_INTERFACE_LAYOUT_SPEC_v0.md`
- `SURFACE_GENERATION_PIPELINE_v0.md`
- `IMAGE_ZONE_RENDERING_RULES_v0.md`
- `FRONTEND_HANDOFF_CONTRACT.md`
- `data/public_surface_mock_v0.json`

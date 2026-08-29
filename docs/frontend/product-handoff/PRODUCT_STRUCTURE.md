# Product structure and workflows

```text
Graphic Design Archive
├── Global Search
│   ├── homepage form and four deterministic starters
│   ├── desktop /search workspace
│   ├── mobile /search workspace
│   └── result → /surfaces/{surfaceId}
└── TRACE
    ├── Context Canvas
    ├── Spacetime
    └── Exploration
        ├── Validated Exploration
        └── Open Inquiry
```

## Search workflow

The homepage GET form submits `q` to `/search`. Starter links use real `objectType`, `theme`, `movement`, or year values. The workspace stores `q`, `yearFrom`, `yearTo`, `objectType`, `theme`, `movement`, and `after` in the URL; browser back/forward and return from an object page therefore restore the same state. The client requests bounded result DTOs from `/api/search/v1`; the 7,995-document index remains server-only. Every filter is hard and conjunctive, default order is relevance, and page size is 25 in the UI.

Search UI states: initial starters, loading, populated, zero, partial optional metadata (`Not recorded`), transport/validation error with retry, later cursor page, and optional System Suggestions. Guidance suggestions do not alter the URL until selected.

## System Suggestions workflow

The client sends a strict public state summary to `POST /api/system-suggestions/v1`. The server validates state/dictionaries, recomputes Search aggregates where applicable, generates an allowlist, and then selects `STATIC_FALLBACK_PROVIDER` or `DEEPSEEK_GUIDANCE_PROVIDER`. Model output is valid only when the note and every suggestion ID pass strict bounds. Any failure returns fallback. Public UI renders `System suggests` only and hides source class/provider status.

## TRACE workflow

TRACE is desktop-only. Mobile requests return a lightweight desktop-required message before governed runtime-data imports. Context suggestions can expose an available public medium/theme/movement representation. Spacetime suggestions can select a governed geography, focus the public count table, or reset the current view. Validated Exploration currently exposes no active v3 product composition. Open Inquiry always renders, in order: `Open inquiry`, `Evidence remains incomplete.`, and `This is not a validated historical association.`; optional guidance follows and cannot promote inquiry state.

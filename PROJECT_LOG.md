# Project log

This active log is a compact index of release-level decisions. The complete pre-hygiene implementation log remains immutable at tag `v49-data-api-closure-20260821` and can be read with:

```bash
git show v49-data-api-closure-20260821:PROJECT_LOG.md
```

## v49 release state — 2026-08-21

- Source closure commit: `d78f496bcdf2cd6941791986007cd7a885c4c532`.
- Source tree: `f0549c319d1e0b0cf5e0aab5a2b297361675b701`.
- Immutable annotated tag: `v49-data-api-closure-20260821`.
- Schema SHA-256: `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`.
- Release projection digest: `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`.
- Canonical objects / proposed curated folder-membership assignments: 15,923 / 47,982.
- Eligible / held: 7,995 / 7,928.
- Accepted TRACE / positive visual rights: 0 / 0.
- Public Read API templates: 18; all tested with no 5xx/search 503.

## Current decisions

- `database/` is the only active database root; legacy `db/` is source-tag history only.
- v49 database implementation and canonical inputs are frozen byte-for-byte.
- `generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input.
- SQLite/search/TRACE/manifests remain reconciliation-only and cannot repair canonical state.
- The browser never connects directly to PostgreSQL; `api_v1`/release-derived reads form the public boundary.
- Historical raw captures, backups, pre-v49 generated output, prompts, reports, and unrelated archive material are recoverable by immutable ref rather than duplicated in the active tip.
- Future database changes require v50+, a new forward-only migration, and an ADR.

## Current indexes

- Release: `docs/releases/v49/RELEASE_INDEX.md`
- Data retention: `docs/releases/v49/DATA_RETENTION.md`
- Audits: `docs/releases/v49/AUDIT_INDEX.md`
- Repository layout: `docs/maintenance/REPOSITORY_LAYOUT.md`
- Retention policy: `docs/maintenance/RETENTION_POLICY.md`
- Database freeze: `database/FROZEN_V49.md`
- Read API: `docs/api/v49-read-api-catalog.md`

## TRACE interface direction — 2026-08-23

### Context Canvas

- Confirmed as the first TRACE implementation: an ERD-style interactive research canvas with typed entities and typed connections.
- Initialize from deterministic templates; provide a sidebar entity palette, drag/add, automatic connections from validated context data, pan/zoom/reposition, auto-layout, inspector, and PNG export.
- Do not permit manual historical-relation creation. Canvas and layout edits are local composition only; canonical data remain read-only.
- Final typography, color, spacing, visual language, and component styling are deferred to the later frontend redesign.

### Spacetime

- Confirmed as the second TRACE direction: map-first, with exactly one selected time layer/bucket at a time for v1 and a discrete selector rather than autoplay.
- Use governed aggregate geographic marks; selecting geography reveals matching recorded objects.
- Parameter inventory and geography/time governance are next. No map implementation belongs in this round.

### Exploration Field

- Confirmed as the third TRACE research direction: an exploratory pixel-grid/generative field driven by similarity, probability-like signals, and ambient factors.
- Use seeded deterministic randomness; approximately 8–10 template families are currently envisioned, with theme, medium, and similar single-factor selections able to drive exploration.
- Derived associations are not historical relations. Data mining remains active; do not freeze factors, scoring, or the template catalog yet.

### Context Canvas real-data validation — 2026-08-23

- Real-data validation uses the audited 7,995-object public cohort while retaining proposed candidate states; it is validation-only, not a governed public TRACE release, and introduces no accepted semantic edges.

### Context V1 governance closure — 2026-08-23

- Context V1 is frozen as a release-derived `project_curated_context` read model: it describes how the archive project classifies a selected public record and does not publish historical relations, influence, causation, creator intent, chronology, or definitive movement membership.
- The governed projection `trace-context-v1` contains 25 controlled terms and 16,106 published representations for all 7,995 eligible public records. Frozen source rows remain `proposed`; publication is a separate Context governance decision.
- Governed Canvas defaults to the selected record plus controlled medium, theme, and movement-context representations. Curated memberships are provenance only; default membership nodes/connections and real semantic edges are zero.
- Context has an additive release-pinned public Read API and compact server-only projection. The route remains unlinked and `noindex`; final visual design and public navigation are deferred.
- Region is excluded from Context and handed to Spacetime parameter governance. No map/time implementation is included.

### Context runtime + Spacetime functional foundation — 2026-08-23

- Context V1 runtime behavior is rehearsed and frozen: the Context API dispatches through its compact governed projection without loading the Search index, SQLite, or the generic archive repository in the normal Context path.
- Spacetime V1 governs all 7,996 public typed-region assignments across the 7,995-record public cohort, with explicit mapped, aggregate-only, and display-unmapped outcomes. It publishes recorded project context only; it does not assert object coordinates, historical presence, movement, influence, or semantic relations.
- The functional foundation uses a checksum-bound Natural Earth Admin 0 Countries 50m artifact, an Equal Earth default projection, deterministic aggregate marks, 23 decade buckets, and release-pinned server API reads. Final visual design, public navigation, and visual acceptance remain deferred.
- Exploration Field remains an open-ended data-mining direction; no implementation or factor/template freeze is included here.

### Spacetime engineering closure + Exploration discovery — 2026-08-24

- Spacetime V1 engineering logic is frozen after production-runtime rehearsal, exhaustive period/geography validation, deterministic renderer parity, cache and stale-request hardening, and functional browser acceptance. Final visual design and public navigation remain deferred.
- Exploration Field Data Discovery Round 1 maps a 64-signal research space across governed Context, governed Spacetime, source/corpus composition, descriptive metadata, curatorial structure, missingness/uncertainty, and bounded frequency/intersection diagnostics.
- Curatorial co-membership, rarity, concentration, conditional rates, lift, and uncertainty remain analysis diagnostics only. They are not historical or semantic relations, rankings, probabilities, or evidence of influence.
- No similarity model, weights, clustering model, probability model, renderer, or final Exploration template registry is selected in this round. Context governance and Spacetime governance remain unchanged.

`CONTEXT_CANVAS_FUNCTIONAL_CORE=COMPLETE`

`CONTEXT_CANVAS_REAL_DATA_VALIDATION=ACTIVE`

`CONTEXT_V1=GOVERNED_DATA_AND_READ_MODEL_READY`

`CONTEXT_CANVAS_FINAL_VISUAL_DESIGN=DEFERRED`

`CONTEXT_V1_RUNTIME_REHEARSAL=PASS`

`CONTEXT_V1_ENGINEERING_LOGIC=FROZEN`

`SPACETIME=GOVERNED_FUNCTIONAL_FOUNDATION_READY`

`SPACETIME_GIS_GOVERNANCE=PASS`

`SPACETIME_TIME_GOVERNANCE=PASS`

`SPACETIME_FUNCTIONAL_FOUNDATION=PASS`

`SPACETIME_VISUAL_DESIGN=DEFERRED`

`SPACETIME_ENGINEERING_LOGIC=FROZEN`

`SPACETIME_RUNTIME_REHEARSAL=PASS`

`SPACETIME_FINAL_VISUAL_DESIGN=DEFERRED`

`EXPLORATION_FIELD=OPEN_ENDED_DATA_MINING`

`EXPLORATION_FIELD_DATA_DISCOVERY_ROUND1=COMPLETE`

`EXPLORATION_SIGNAL_REGISTRY=64`

`EXPLORATION_SIMILARITY_MODEL=NOT_SELECTED`

`EXPLORATION_RENDERER=NOT_IMPLEMENTED`

`FINAL_TRACE_VISUAL_DESIGN=DEFERRED`

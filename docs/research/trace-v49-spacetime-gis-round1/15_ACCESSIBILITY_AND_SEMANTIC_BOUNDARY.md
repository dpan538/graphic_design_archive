# Accessibility and semantic boundary

## Non-graphic equivalent

Every selected-period map state has a table/list equivalent containing:

- selected period and its overlap interpretation;
- geography label and mapping state;
- record count and period denominator;
- precision breakdown;
- mapped, aggregate-only, unmapped, and held-excluded status;
- deterministic selection control;
- paged public record links.

The map SVG is described as an aggregate representation. Its paths and dots are `aria-hidden`; the surrounding title/description and the numerical table carry the accessible meaning. Geography selection is keyboard-operable through native buttons in the table. Texture, area fill, circle size, or dot density is never the only carrier of a count.

## Interaction boundary

The primary period control is a native select with previous/next buttons. No autoplay is required. Period changes reset stale selection/records and request one governed atlas. Geometry is fetched once and retained.

Mapped, aggregate-only, and unmapped rows can all be selected through the table. A selected row drives the same deterministic record-page resource; lack of a map point does not make a record inaccessible.

## Statement boundary

UI copy consistently uses “recorded geographic context,” “recorded temporal extent,” and “overlaps this period.” It must not say or imply:

- exact object location;
- created in a decade when only recorded context is known;
- travel, diffusion, influence, route, or causality;
- archive endorsement of a cartographic boundary;
- one record per synthetic dot location.

Aggregate anchors and density dots carry `positionClaim=aggregate_only`. Selecting a dot/mark selects a geography aggregate; it does not select an individual co-located object.

## TRACE isolation

Spacetime map marks never become TRACE semantic edges. Context retains zero region nodes and does not import Spacetime geography. Spacetime does not use Context medium/theme to determine geography or map styling. Cross-filtering is deferred.

## Route boundary

`/trace/spacetime` is unlinked and emits `noindex, nofollow`. It does not replace `/trace` or add global navigation. Visual design remains intentionally functional and replaceable.

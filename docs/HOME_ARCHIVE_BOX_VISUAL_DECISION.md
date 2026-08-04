# Home archive-box visual decision

## Decision

Keep the existing four-coordinate archive index and strengthen its physical
filing semantics. Desktop presents the four links as labelled dividers held by
a flat archive-box frame. Mobile presents the same four links as a native,
scroll-snapping card set. No route, count, frozen object, TRACE edge, or search
record is changed by this work.

## Reference translation

| Reference quality | Project translation | Deliberate limit |
| --- | --- | --- |
| Punched and register cards | A quiet repeating registration-hole row and mono index numbers | No distressed overlay that reduces text contrast |
| Varidex box and tabbed folders | Four offset category tabs, side enclosure, front panel, index handle | No literal 3D render, colour band, or heavy cast shadow |
| Mobile stacked cards | Horizontal native scrolling, snap alignment, persistent scope/count text, next-card preview | No hover-only disclosure and no unrelated wallet/payment metaphor |
| Editorial paper references | Warm-neutral paper white, fine rules, large negative space, restrained mono metadata | No dominant grey or dark teal wash |
| Blue/editorial accent references | Category colour appears only in tab chips, thin rules, focus, and registration marks | No full-card category fills |

## Desktop behaviour

- All four folder tabs are visible without interaction.
- Hover and keyboard focus lift one divider and reveal its title, scope, and
  folder/surface count.
- A planar side enclosure, shallow interior lip, and labelled front panel make
  the object read as a box while preserving the project's light composition.
- The existing archive-counts card remains a separate research ledger.

## Mobile behaviour

- Cards use native horizontal overflow and `scroll-snap-type: x mandatory`.
- Every card exposes its title, scope, counts, and open action without hover.
- The following card remains partially visible as the affordance for swiping.
- A linear view-timeline reveal is progressive enhancement only. Native
  scrolling remains complete without it, and reduced-motion disables it.
- The large desktop counts ledger collapses to a two-cell image/source strip so
  it cannot obscure card content.

## Palette

- Canvas: `#f2eee3`
- Primary paper: `#f8f4e8`
- Ink: `#2e322f`
- Category colours: highlight only, never the paper field

This is a warm-neutral paper system: lighter than the previous grey/teal cast,
but with sufficient line and ink contrast to keep the archive skeleton legible.

## Browser acceptance

Desktop was checked at 1440 × 1000 and again at the shorter 1280 × 720 default
viewport. The latter exposed and then verified the compact tab-spacing rule:
the box frame measured 620 × 553 px and the Movement tab had zero right-edge
overflow. Mobile was checked at 390 × 844. The first card measured 298 × 484
px, the card rail exposed 896 px of horizontal overflow, all four detail blocks
were visible, and all four touch actions were present. Scrolling 292 px centred
the Theme card while leaving adjacent cards visible.

Screenshots and their hashes are stored in
`docs/capture/home-archive-box-v48/`.

The project-level `asset:a11y-check` could not complete because its bundled
Puppeteer launcher did not expose a browser WebSocket endpoint within 30
seconds, including when allowed outside the filesystem sandbox. Browser-based
manual acceptance therefore checked the accessible region name, four direct
folder links, persistent mobile descriptions/actions, reduced-motion fallback,
and an empty warning/error console. The launcher failure remains an environment
gate and is not recorded as a passing automated gate.

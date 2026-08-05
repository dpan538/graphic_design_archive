# Home archive-cabinet visual decision

## Decision

The homepage no longer asks one archive-box metaphor to serve desktop and
mobile. The two presentations share the same four routes and counts, but they
are separate interaction systems:

- Desktop is a compact filing-cabinet index: four calm rows inside a shallow
  metal/paper drawer frame. A row behaves like a small drop-down menu and
  reveals its catalogue scope on hover or keyboard focus.
- Mobile is a vertical card wheel: cards move above and below a centre point
  with native vertical scrolling and scroll snap. It has no cabinet shell and
  needs no hover.

No route, frozen object, TRACE edge, source record, or search index is changed
by this work.

## Why the earlier model was rejected

The previous stacked-folder construction carried too many physical cues and
too much engineering for four choices. Its large lifted cards also made the
homepage look like an interaction prototype instead of a finished archive.
On mobile, the horizontal card rail preserved the box/folder logic when the
more appropriate behaviour was a lightweight vertical selector.

## Desktop translation

| Archive reference | Interface translation | Limit |
| --- | --- | --- |
| Open filing-cabinet drawer | Fine side rails, an interior paper stack and one restrained front handle | No literal 3D render or cast shadow |
| Hanging-folder index | Four always-visible catalogue rows | No overlapping folder pile |
| Pulling one file | Scope text opens within the selected row | No auto-scroll or pointer tracking |
| Metal label holder | Small centred `OPEN` handle | Decorative only; links remain the rows |

The default state presents only the four titles and their compact counts. This
is intentionally closer to a traditional navigation menu than to a simulated
object. Category colour is limited to a dot, a thin focus rule and the active
row wash.

## Mobile translation

- `Region`, `Theme`, `Medium` and `Movement` are direct links in a vertical
  `scroll-snap-type: y mandatory` viewport.
- The centred card faces the reader. Cards entering and leaving the viewport
  rotate around the horizontal axis, scale down and recede, producing a light
  circular-wheel reading without a bespoke gesture engine.
- The wheel motion uses a CSS view timeline as progressive enhancement. Native
  vertical scrolling and snap remain complete when view timelines are absent.
- Reduced-motion removes rotation, scale, opacity and transition changes.
- Every card permanently exposes title, scope, count and open action; no
  information depends on hover.
- The homepage counts card is hidden on mobile so it cannot obscure the wheel.

## Counts and palette

The former engineering-style counts ledger is removed from the homepage. A
single desktop summary retains only folder count, surface count and image
coverage. Detailed counts remain available in their existing research pages.

- Canvas: `#f2eee3`
- Primary paper: `#f8f4e8`
- Ink: `#2e322f`
- Category colours: highlight only

This keeps the project on warm-neutral paper rather than dark teal or grey.

## Acceptance contract

- Desktop: all four routes and counts are visible before interaction; scope is
  keyboard-revealable; no overlap or auto-scroll exists.
- Mobile: the viewport scrolls vertically, centres each card, preserves direct
  link navigation, exposes adjacent-card context and remains readable with
  reduced motion.
- Automated source checks cover the presentation split, native scroll/snap,
  progressive animation, direct routes, restrained palette and simplified
  homepage summary.
- Browser screenshots and hashes are stored in
  `docs/capture/home-archive-box-v48/` after visual acceptance.

## Browser acceptance results

Desktop was inspected at 1280 × 720. The cabinet measured 675 × 451 px,
contained four direct routes, had no horizontal overflow, and kept all four
default rows at 70 px. Keyboard focus on Region expanded that row to 99 px;
the scope text reached opacity `1` while focus remained on the link.

Mobile was inspected at 390 × 844. The wheel viewport measured 353 × 604 px,
contained four direct-link cards, hid the homepage counts stack, and had no
horizontal overflow. Region occupied the readable centre at 329 px high while
Theme remained visible below as a tilted, receding card.

That mobile capture also exposed a collision between the duplicate intro
heading and the fixed Search control. The heading is now hidden at the mobile
breakpoint and a source gate verifies that correction. A final browser refresh
and re-capture was denied by the local browser security policy, so the stored
mobile image records the interaction geometry immediately before that final
one-line visibility correction. This re-capture remains an explicit open
visual gate rather than being reported as passed.

The production build compiled successfully in 27.5 minutes and completed type
checking. It then attempted to generate 8,783 static pages; several pages
exceeded the 60-second page limit, and `/_not-found` failed after three
attempts. The full production build gate is therefore **not passed**. This is
an existing full-archive static-generation performance constraint, but it must
be addressed before release.

The project-level Puppeteer accessibility launcher previously failed to expose
a browser WebSocket endpoint within 30 seconds. Until that environment gate is
resolved, browser acceptance must explicitly inspect accessible region names,
direct folder links, keyboard focus, mobile descriptions/actions, reduced
motion and the warning/error console. The launcher failure is never recorded
as a passing automated gate.

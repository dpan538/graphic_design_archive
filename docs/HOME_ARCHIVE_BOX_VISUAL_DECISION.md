# Home research-index visual decision

## Decision

The homepage is a research entrance, not a simulation of opening an archive
box. This removes the archive-box stereotype, not material interaction.
Archival qualities remain in paper, rules, indexing numbers, button depth and
press response, while literal cabinet copy, handles, folder lifts and top-left
brand cards are removed.

Desktop and mobile continue to share the same four routes and counts, but use
separate interaction systems:

- Desktop presents a flat research-coordinate index.
- Mobile presents the four coordinates as one tightly stacked vertical card
  wheel.

No route, frozen object, TRACE edge, source record, or search index is changed.

## Academic framing

The desktop lead is `Research index · 04 coordinates`, followed by a concise
method statement explaining that the four catalogue structures preserve object
and source evidence. There is no promotional headline and no instruction to
“open the archive cabinet”.

Each row exposes:

- coordinate number and type;
- folder/surface count;
- catalogue scope on hover or keyboard focus;
- a direct route to the corresponding research index.

The former cabinet front, handle, side rails and drawer language are removed.
Colour remains a small category marker and focus rule.

## Global navigation

The persistent top-left `Archive Box / Modern Graphic Design History` card is
removed. The page field and negative space now carry the composition without a
second branded object competing with the research content.

Only one global `Menu` button appears at rest. It has `aria-expanded` and opens
exactly five controls:

1. About
2. Index
3. Folders
4. TRACE
5. Search

The expanded controls share the same visual size family as the counts module.
Search continues to use its existing panel and data flow.

## Archive counts

Homepage counts use native `<details>` / `<summary>` interaction:

- collapsed: a narrow module with the surface total as the dominant number;
- expanded: folders, surfaces and image coverage in a compact definition list;
- keyboard and screen-reader interaction remain native;
- the module is narrower than the former three-column strip.

Detailed engineering counts stay in the dedicated research pages.

## Mobile card wheel

- Cards use vertical native scrolling and `scroll-snap-type: y mandatory`.
- Adjacent cards use negative block spacing so they read as one card set rather
  than separate pages.
- The centred card moves to the foreground; entering and leaving cards rotate,
  scale and recede around the horizontal axis.
- Multiple card headers remain visible together, matching the mental model of
  cards carried on one ring.
- Scope, count and direct link remain present on every card.
- The redundant bottom instruction is removed.
- Reduced motion removes rotation, scale, opacity and transition changes.

## Palette, contrast and interaction state

- Canvas: `#f5f0e3`
- Primary paper: `#fbf7eb`
- Ink: `#242925`
- Secondary ink: `#505650`
- State blue: `#2567df`
- State orange: `#f04b23`
- Category colours: highlight only

The result stays light and warm-neutral while text, rules and visualisation
marks gain enough contrast to establish a reading order. Buttons retain a
small physical edge, shallow shadow and pressed translation; large skeuomorphic
containers do not return.

On precise pointing devices, the cursor is a small state dot:

- grey on non-interactive material;
- blue on links, buttons, summaries and data controls;
- orange on selected, active or evidence-focus states.

Touch layouts do not receive a simulated cursor. TRACE routes, stations,
geographic points and evolution cells use the stronger blue/orange signal pair
against the paper field; colour still never changes evidence semantics.

## Acceptance contract

- Resting desktop and mobile states show exactly one global Menu button.
- Expanding Menu exposes exactly five labelled controls without displacing the
  page layout.
- Counts are clickable, narrower than the previous strip and visibly expand.
- Desktop pointer states are grey / blue / orange and controls retain tactile
  press feedback.
- Desktop has no top-left wordmark card, cabinet headline or simulated drawer
  front.
- Mobile shows at least the active card and adjacent card headers together,
  supports vertical movement and has no bottom instruction.
- All four coordinate cards/rows remain direct links.
- TRACE map points and analytical highlights remain distinguishable on paper
  and dark plotting fields.
- TRACE and frozen v48 hashes remain unchanged.

Browser screenshots and their hashes are stored under
`docs/capture/home-archive-box-v48/` after the acceptance pass.

## Acceptance evidence · 2026-08-05

Desktop viewport (`1280 × 720`):

- resting state contains one `80 × 80 px` Menu control;
- collapsed counts are `259 × 108 px`, with a `195 × 36 px` dominant total;
- the research coordinate index is `840 × 358 px`;
- expanding Menu exposes exactly five `69 × 69 px` controls;
- opening counts exposes the three compact rows without horizontal overflow;
- measured text contrast is `13.01:1` for primary ink and `6.62:1` for
  secondary ink.

Mobile viewport (`390 × 844`):

- all four card layers remain simultaneously legible in the stack;
- the card wheel scrolls independently and was verified at `scrollTop 0`, `81`
  and `201`;
- Menu remains a `70 × 70 px` primary control;
- the five expanded controls are each `44 × 44 px`, occupying
  `x = 51.4–296.1 px` with no clipping or horizontal overflow;
- counts are intentionally hidden from the mobile card-reading field.

Screenshot manifest:

| File | SHA-256 |
| --- | --- |
| `01-home-research-index-desktop.png` | `fbd96abe33a137294698ba50683d38d0e3ab4431a9960b0a00589afd293fdb72` |
| `02-home-menu-and-counts-desktop.png` | `33dede4b452856c8ab3759d9a548bab7c38be130b39ee1fc64a19797eb1f0235` |
| `03-home-mobile-card-stack.png` | `cb892f28879fbb6454f1a6fc71c741ab58fd761f8a54d8448bd2896ea1f8e6b5` |
| `04-home-mobile-card-stack-scrolled.png` | `bfb958720b4064ebd72ccc18eee20c92324569870aeb1fa62ff1890bcaf06813` |

Automated gates passed: TypeScript (`tsc --noEmit`), homepage contract
(`13/13`), TRACE visualisation contract (`13/13`) and `git diff --check`.
The TRACE gate reads the frozen v48 aggregates: `15,923` active objects,
`21` normalised TRACE types, `20` observed relation types, `15,569` mapped
objects and zero inferred influence edges.

Frozen files were read-only throughout this change. Their SHA-256 values remain:

- SQLite: `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`
- candidate JSON: `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`

## Known build constraint

The previous production run compiled successfully and completed type checking,
then attempted to statically generate 8,783 pages. Multiple pages exceeded the
60-second page limit and `/_not-found` failed after three attempts. This remains
a project-level release gate; it is not caused by the homepage interaction
components and is not reported as passing.

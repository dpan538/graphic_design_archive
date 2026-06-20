# Prefreeze Main/Sub/Text Method Discussion v1

Scope: methodology discussion for main/sub/text archival structure before any
further rebuild or role application.

This document is a discussion draft. It does not mutate records, does not apply
role overrides, does not rebuild payloads, does not download images, and does
not change rights or image states.

## Current Evidence

The latest candidate audit gives the following structural baseline:

- Candidate surfaces: 16,175.
- Candidate active public sources: 14,997.
- Candidate main sheets: 13,537.
- Candidate cards: 1,943.
- Candidate support packet appendix text rows: 689.
- Main-sheet review rows: 13,528.
- Main sheets with explicit `compoundChildren`: 9.
- Main dossiers with more than two subsheet pages: 0.
- Main dossiers with more than five text pages: 0.
- Soft main-anchor audit lanes:
  - support or card review: 9,251.
  - main anchor manual review: 3,809.
  - keep main anchor candidate: 397.
  - needs packet/subsheet assignment: 42.
  - needs editorial text: 38.

Release-facing image/source indicators are already relatively strong:

- Object source-visible: 98.92%.
- Object verified-open: 95.29%.
- Weighted publication-grade image coverage: 97.26%.
- IMG04: 0.82%.
- Strict distribution adjusted source coverage: 74.98%.

Interpretation: the immediate bottleneck is no longer raw item volume or image
availability. The bottleneck is whether main sheets can be reorganized into
credible research packets with meaningful relation structure and editorial
depth.

## Working Definitions

### Main Sheet

A main sheet is a provisional research-packet anchor, not a final proof that the
archive has completed research around that object.

It may represent:

- A single highly important work or object.
- A project or campaign that anchors several related records.
- A source-rich series or institutional cluster.
- A regional or historical packet anchor where scarcity justifies provisional
  main status.
- A methodological anchor that will later require editorial text and sub sheets.

Main status should remain soft until the archive validates:

- impact or representativeness,
- source depth,
- relation density,
- period span,
- rights/source state,
- region scarcity,
- editorial need.

### Sub Sheet

A sub sheet is a source-linked packet member. It can be a variant, issue,
parallel poster, page, episode, source record, or related object that supports a
main anchor.

A sub sheet is not necessarily less important historically. Its role is
structural: it helps a research packet avoid overproducing separate main sheets
for related evidence.

### Text Sheet

A text sheet is an editorial or interpretive support page. It should explain why
a packet exists, how its members relate, and what the archive can safely claim
from source evidence.

Text sheets should not be treated as filler. They are required when the main
sheet's value depends on context rather than a single self-evident object.

### Card

A card is a lightweight context/support surface. Cards are appropriate for
events, photos, weak object evidence, repeated views, source-page traces, and
records that support research but should not carry the weight of a main anchor.

### Appendix

An appendix holds source evidence, rights evidence, provenance, index material,
or dense metadata that should remain available without interrupting the reading
path.

## Proposed Soft Anchor Model

The archive should not apply a hard "main must already be research-grade" rule.
Instead, every main can carry an anchor marker:

- `strong_soft_anchor`: likely main, sample before keeping.
- `soft_anchor_review`: plausible main, needs human review.
- `anchor_if_editorial_text_added`: can remain main if editorial text is added.
- `packet_anchor_or_member_review`: may be anchor or sub sheet depending on
  packet design.
- `support_or_card_review`: should usually move into support/card unless review
  finds strong source or scarcity reasons.

This lets the archive preserve exploratory research structure without pretending
that every main already has complete text, subsheets, and editorial framing.

## Validation Protocol Before Any Rebuild

### Step 1: Sample The Anchor Lanes

Review a stratified sample before applying role changes:

- 40 from `strong_soft_anchor`.
- 80 from `soft_anchor_review`.
- 40 from `anchor_if_editorial_text_added`.
- All 42 from `packet_anchor_or_member_review`.
- 120 from `support_or_card_review`.

Sampling should be balanced by:

- period,
- region,
- source family,
- image state,
- source-reading length,
- cluster size.

### Step 2: Decide What Counts As A Good Main Anchor

For each sampled main, reviewers should answer:

- Does this surface anchor a research question, project, series, movement, or
  regional scarcity case?
- Is the source evidence strong enough to support main status?
- Does it need at least one sub sheet, card, appendix, or text page?
- Would demoting it hide an important research path?
- Would keeping it as main create shallow noise?

### Step 3: Establish Minimal Text Expectations

Text requirement should depend on packet complexity, not a universal word count.

Suggested starting model:

- Single-object strong anchor: one text page may be enough.
- Series/project anchor: at least one packet overview text page plus sub sheets.
- Long period span: add period-context text.
- High relation density: add relation-map or source-cluster text.
- Region-scarcity anchor: add scarcity/context text even if source text is thin.
- Weak source but important image: add cautionary source-note text or demote to
  card/support.

### Step 4: Validate Against Failure Cases

The method must catch and explain:

- stamp/philatelic overrepresentation,
- event/photo/context records,
- Commons file-page overclaiming,
- unresolved or transnational geography,
- natural-history/geology false positives,
- repeated page/view variants,
- source families with large homogeneous runs,
- contemporary platform/studio clusters that are source-rich but historically
  shallow.

### Step 5: Only Then Apply A Small Override

After sampling and agreement, create a small applied override layer. Rebuild
only a candidate payload and compare:

- main/sub/card counts,
- text-page distribution,
- dossiers with more than two subsheets,
- dossiers with more than five text pages,
- object source-visible,
- verified-open,
- weighted publication-grade image coverage,
- IMG04,
- region and period balance.

## Advantages

- Preserves research flexibility: main sheets can remain provisional anchors
  while the packet structure matures.
- Avoids premature demotion: historically important but thinly described
  records are not automatically downgraded.
- Makes weak records visible: support/card review exposes shallow Commons,
  event/photo, stamp, and geography-risk clusters.
- Creates a scalable workflow: review lanes let the project move in batches
  instead of relying on one giant rebuild.
- Keeps rights discipline intact: structural review does not upgrade IMG01/IMG03
  or rights states.
- Supports future frontend design: a soft anchor model maps naturally to tree
  views, context panels, and research assistant explanations.

## Disadvantages

- It slows down final publication: the archive must review structure before
  applying large role changes.
- It adds methodological complexity: users and maintainers must understand that
  "main" is a provisional anchor, not always a finished essay-level page.
- It requires editorial labor: text sheets cannot be produced honestly from
  image/source metadata alone.
- It can preserve too many mains if review standards are too generous.
- It can demote too much if weak-source signals are treated as absolute rather
  than contextual.
- It depends on source-family knowledge: Gallica, Commons, DigitalNZ, Te Papa,
  IA, university collections, and contemporary platforms need different review
  expectations.

## Open Questions For Discussion

- Should a main sheet be allowed to remain main with only one text page if it is
  a strong visual/object anchor?
- How much region scarcity should compensate for thin text?
- Should repeated poster-series records become one main plus many subsheets by
  default?
- Should Commons file-source records ever become main without external source
  corroboration?
- What is the minimum editorial text expectation for a main that spans more
  than one decade?
- Should "main anchor manual review" be sampled before any further source
  capture, or can it proceed in parallel with source cleanup?

## Recommended Next Action

Do not rebuild yet.

First, validate the method on a review packet:

- 40 strong soft anchors.
- 80 soft anchor review rows.
- 40 editorial-text-needed rows.
- all packet anchor/member review rows.
- 120 support/card review rows.

The output of that review should be a methodology decision log, not an applied
override file.

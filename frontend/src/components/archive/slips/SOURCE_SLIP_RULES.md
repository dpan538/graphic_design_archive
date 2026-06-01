# Source Slip / Citation Slip Rules

Source slips are compact citation receipts for MGD Archive records. They sit
between cards and appendix pages: denser than cards, lighter than appendix.

## Placement

- Primary home: source slips should live as their own asset family.
- Secondary home: they may appear near card sets as a dense text-only companion
  when a card needs citation/source support.
- Do not place them inside appendix flows. Appendix pages carry broader
  evidence and review context.

## Shared Constraints

- Use real `Surface` payload fields only.
- Default orientation is vertical.
- No horizontal layouts in this set.
- No photos, simulated photos, or decorative image placeholders.
- `IMG00` can appear as a textual state or stamp only.
- Folder color is shown by small pure-color dots, without text.
- Typography should feel like a receipt, catalog slip, or source return mark:
  dense, legible, and plain.

## Ratios

- Square: 1:1. Use for source receipt summaries.
- Portrait: 3:4. Use for citation + rights ledgers.
- Narrow: 1.5:3. Use for source-return tickets or IMG-state receipts.

## Content Minimums

Each slip must include:

- `MGD Archive` label;
- surface id or display number;
- source name;
- source record id;
- date or access date;
- title;
- image state;
- source URL, citation basis, or source table rows.

Source slips may be grouped with cards in browsing surfaces, but selection
priority should remain lower than regular cards because their role is support
and verification, not general display.

# Appendix Layout Constraints

Appendix assets are rare evidence pages. They are not cards, bookmarks, or
generic decorative inserts. Appendix pages explain why a record is retained,
restricted, classified, cited, grouped, or routed back to a source.

## Shared Rules

- Use real archive payload fields only.
- Production appendix leaves must resolve to one of AX01-AX06. If an appendix
  leaf is missing an explicit AX id, it falls back inside the new system:
  `IMG00` rights evidence uses AX01, and all other missing-id cases use AX05.
  The previous table-only continuation layout is retired and must not be used
  as a fallback.
- Appendix pages are higher-density than cards but lower-status than final
  sheets.
- `IMG00` means the image area is intentionally empty. Do not draw a decorative
  surrogate, simulated photograph, or abstract replacement image.
- `IMG04` means no image area at all.
- Tables may be compressed, but labels must remain readable.
- Every appendix must identify the parent surface, source, and reason for the
  appendix.
- Appendix usage should remain rare. Do not use appendix pages as automatic
  overflow for every unused table.
- `AX06` has a low selection priority: its production selection weight is one
  third of the other appendix layouts.

## AX01 `appendix-sheet--rights`

Purpose: rights/image evidence continuation.

Use when:
- a sheet has `IMG00`;
- the image identifier exists but display/reuse evidence is insufficient;
- rights explanation is too important to sit only in a small stamp.

Required content:
- surface id;
- display number;
- title;
- source name;
- source identifier;
- source URL;
- access date;
- image state;
- display policy;
- rights basis;
- local copy permitted;
- rights review required;
- raw payload locator when present.

Do not:
- render a source image;
- render a placeholder illustration;
- make the empty image area look like a failed load.

## AX02 `appendix-sheet--citation`

Purpose: source and citation register.

Use when:
- citation/source rows exceed a compact sheet footer;
- grouped records carry multiple source links;
- raw payload paths or access dates need to remain visible.

Required content:
- parent surface id;
- title or group label;
- source name;
- at least 4 source/citation rows when available;
- source URL or source locator;
- access date or raw payload status.

Do not:
- include an image bay;
- use this as a visual bookmark;
- hide long source lists behind a single summary line.

## AX03 `appendix-sheet--relations`

Purpose: relations, classification, and authority-evidence appendix.

Use when:
- relation rows exceed the main sheet;
- classification needs evidence context;
- authority/folder memberships need careful labeling.

Required content:
- parent surface id;
- classification rows;
- relation rows;
- folder memberships;
- relation caution or evidence level.

Do not:
- imply causal design influence from `associated_with`;
- turn visual resemblance or movement membership into an authority claim;
- omit the source basis for the relation.

## AX04 `appendix-sheet--context`

Purpose: protocol, context, or source-review packet.

Use when:
- records require manual review, protocol notes, sensitivity notes, or source
  return policies;
- the appendix is a contextual note rather than a table-only continuation;
- a source family needs review handling before visual display.

Required content:
- review or advisory reason;
- affected source/folder;
- image/display policy;
- source return;
- context note;
- suppression or review rule when present.

Do not:
- make tabs decorative only;
- promote this page to a general folder cover;
- replace the actual source-return policy with visual shorthand.

## AX05 `appendix-sheet--statement`

Purpose: vertical source dossier / verification ledger.

Use when:
- source verification needs a formal administrative page;
- source, normalized, rights, citation, and classification rows all need to
  remain visible;
- the appendix should read as a narrow evidence packet, not a postcard.

Required content:
- source date or normalized date;
- addressee / review destination;
- source name;
- source record id;
- title;
- description or citation basis;
- source metadata rows;
- normalized metadata rows;
- rights and citation rows;
- folder/classification index;
- image state and source return.

Do not:
- add a decorative image;
- use a wide landscape ratio;
- leave large blank areas unless the blank is evidence-bearing;
- let the statement become a marketing poster.

## AX06 `appendix-sheet--typed-index`

Purpose: typed source index and table-heavy appendix.

Selection priority: low. Because this layout uses a heavier typographic weight
and reads more like typed back matter than a standard appendix, its target
selection weight is one third of AX01-AX05.

Use when:
- source, normalized, and classification rows are better read as a numbered
  index;
- a long title needs to be paired with compact table rows;
- the page should feel like a typed insert, track list, or catalog back matter.

Required content:
- parent source record id;
- title;
- source name;
- 18-24 numbered rows from source/normalized/classification/relation evidence
  when available;
- rights/citation side rail;
- explicit image state area;
- folder and date footer.

Do not:
- use a new image when the record is `IMG00`;
- make the numbered rows decorative text;
- repeat another appendix silhouette exactly;
- stretch into a full-width landscape sheet unless the source payload is itself
  a horizontal sequence.

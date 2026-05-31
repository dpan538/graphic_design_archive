# Card Layout Constraints

These card layouts are digital archive assets, not decorative thumbnails. Each
card must carry enough record information to stand alone in a design archive
view while preserving a controlled physical-print reference.

## Shared Rules

- Badge: 1 to 3 pure-color folder dots only; no visible text inside badges.
- Source: use real `Surface` or `Folder` fields from the archive payload.
- Overflow: no scrolling inside a card; truncate long fields deliberately.
- Typography: no viewport-scaled type; preserve the mono/sans hierarchy.
- Images: render a real source image only when `image.url` exists; otherwise
  show the rights-aware image state frame.
- Color: orange means Portland Orange only (`#ff5e39`).

## Family Priority And Placement Probability

Card families are not sampled evenly. Families A, B, and C are regular card
systems; Family D is an exceptional physical-format system.

| Family | Priority | Target placement weight | Use |
|---|---:|---:|---|
| A Minimal Archive Display | P1 | 0.32 | Default record/folder cards. |
| B Approved Neutral Cards | P1 | 0.38 | Default high-information archive cards. |
| C Color Archive Cards | P2 | 0.24 | Secondary regular cards when color helps grouping or contrast. |
| D Special Physical Proportions | P4 | 0.06 | Rare emphasis cards only. |

Family D must remain visibly rarer than every regular card family:

- Treat D as a low-priority accent after A, B, and C eligibility has been
  checked.
- Cap D at 6% target share and 8% maximum share in any generated card set.
- Do not place more than one D card in the same viewport cluster or immediate
  folder sequence unless the user explicitly requests a special-card study.
- Use D only when the content benefits from a physical reference such as stamp,
  ticket, punch card, pass, or chamfered dossier. Shape alone is not sufficient.
- If no D layout is semantically eligible, do not force one into the set.

## Family A: Minimal Archive Display

### A1 `archive-card--a-specimen`
- Ratio: 1:1 square, 21rem x 21rem.
- Purpose: object/specimen summary with image evidence and key metadata.
- Required content: source record id, title, image bay, description summary,
  date, place, medium, source.
- Limits: title <= 70 chars; summary <= 136 chars; metadata <= 4 rows.
- Do not: use this for folders or long chronological lists.

### A2 `archive-card--a-exhibition`
- Ratio: wide landscape, 31rem x 17.5rem.
- Purpose: exhibition/poster/event-style record with date sidebar.
- Required content: source record id, date, title, creator/byline, short body,
  image bay, medium, source, rights.
- Limits: title <= 80 chars; body <= 164 chars; metadata <= 3 rows.
- Do not: show folder line when metadata is present; it causes crowding.

### A3 `archive-card--a-reading`
- Ratio: tall reading card, 16.4rem x 23rem.
- Purpose: citation/classification-heavy record without image emphasis.
- Required content: source record id, title, classification rationale, date,
  creator, source, access date, reading length, up to 2 classification rows.
- Limits: body <= 150 chars; classification rows <= 2; no URL text.
- Do not: render raw source URLs inside the body.

### A4 `archive-card--a-folder`
- Ratio: compact landscape index, 31rem x 16.5rem.
- Purpose: folder overview with count and sample chronological records.
- Required content: folder type, folder title, date span, surface count,
  scope note, 5 sample records.
- Limits: sample title <= 56 chars; samples <= 5.
- Do not: use for single-surface records.

## Family B: Approved Neutral Cards

### B1 `archive-card--rights-review`
- Ratio: tall review card, 18rem x 24rem.
- Purpose: rights/status review for an image-restricted record.
- Required content: source record id, title, image state frame, rights label,
  4 rights rows.
- Limits: rights body <= 152 chars; rights rows <= 4.
- Do not: replace the empty image frame with decorative art.

### B2 `archive-card--source-wide`
- Ratio: wide source dossier, 30rem x 18rem.
- Purpose: source-centered record with image/status and metadata table.
- Required content: source record id, title, creator, body, image bay, 6 rows
  covering date/source/identifier/medium/rights/accessed.
- Limits: body <= 142 chars; metadata <= 6 rows in 2 columns.
- Do not: use a narrow right-side table.

### B3 `archive-card--publication`
- Ratio: mid landscape, 25rem x 22rem.
- Purpose: publication/text record with simple rule graphic.
- Required content: source record id, title, date, body, creator, medium,
  source, rights/status.
- Limits: title <= 90 chars; body <= 156 chars; metadata <= 4 rows.
- Do not: add image unless the publication has reliable image rights.

### B4 `archive-card--folder-timeline`
- Ratio: large landscape folder card, 30rem x 19rem.
- Purpose: chronological folder preview with count and 6 samples.
- Required content: folder type, title, date span, count, 6 dated sample rows.
- Limits: samples <= 6; sample title <= 68 chars.
- Do not: use for single-surface object records.

## Family C: Color Archive Cards

### C1 `archive-card--color-record`
- Ratio: color landscape, 21rem x 15.5rem.
- Purpose: color-forward single-record summary.
- Required content: source record id, title, date, place, source, image state.
- Limits: title <= 70 chars; metadata <= 4 rows.
- Do not: introduce additional accent colors beyond the system palette.

### C2 `archive-card--color-image`
- Ratio: split-color landscape, 30rem x 16rem.
- Purpose: image/status record with strong color block.
- Required content: source record id, title, short body, image bay, folder line.
- Limits: title <= 80 chars; body <= 126 chars.
- Do not: let text cross the color split into the image column.

### C3 `archive-card--color-type`
- Ratio: color portrait, 16.5rem x 23rem.
- Purpose: type/publication record where graphic rules carry the visual weight.
- Required content: source record id, title, rule graphic, creator, medium,
  source.
- Limits: title <= 82 chars; metadata <= 3 rows.
- Do not: add decorative illustration.

### C4 `archive-card--color-folder`
- Ratio: banded folder card, 30rem x 14.5rem.
- Purpose: color-coded folder summary with sample records.
- Required content: folder type, title, count, 4 sample records.
- Limits: samples <= 4; sample title <= 50 chars.
- Do not: use as a detailed source card.

## Family D: Special Physical Proportions

### D1 `archive-card--special-stamp`
- Ratio: tall perforated stamp, 13.2rem x 29rem.
- Purpose: collectible/specimen card with a scalloped physical edge.
- Required content: source record id, title, image bay, body, date, source,
  medium, rights/status.
- Limits: title <= 58 chars; body <= 128 chars; metadata <= 4 rows.
- Do not: make the edge treatment the only visual idea; the card must still
  read as a record.

### D2 `archive-card--special-admit`
- Ratio: long admission ticket, 37rem x 12.6rem.
- Purpose: event/poster record with detachable stub logic.
- Required content: source record id, title, body, date, stub label/image
  state, creator, source, rights/status.
- Limits: body <= 132 chars; metadata <= 3 rows.
- Do not: use for dense folder lists; it is a single-record ticket.

### D3 `archive-card--special-punch`
- Ratio: rounded vertical punch ticket, 13.6rem x 24rem.
- Purpose: narrow ticket-like record for image-restricted material; the top
  visual must be a rights-aware graphic, not a simulated missing photo.
- Required content: rights graphic, date or date start, image state, title,
  folder line, barcode mark, source, medium.
- Limits: title <= 42 chars; metadata <= 2 rows.
- Do not: render a photograph-style empty frame for `IMG00`; add more than two
  punch holes.

### D4 `archive-card--special-chamfer`
- Ratio: chamfered pass/dossier, 33rem x 15.5rem.
- Purpose: hybrid folder + representative record card.
- Required content: folder type, folder title, count, representative surface
  id/title, date/source/status, 4 sample records.
- Limits: samples <= 4; representative title <= 72 chars.
- Do not: use for pure decoration; both folder and surface contexts are
  required.

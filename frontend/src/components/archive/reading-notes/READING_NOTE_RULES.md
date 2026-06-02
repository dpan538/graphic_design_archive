# Reading Note Asset Rules

Reading notes replace the old `L10.bookmark` folder note. They are folder-level
reading aids, not decorative cards. Each layout must expose filter status,
scope, image policy, and a short sample of records from the current folder.

## Layout Set

### RN01 `stack`
- Shape: two stacked 3:4 note cards.
- Use: region folders or other broad folders that need clear separation between
  scope and reading protocol.
- Content constraints: top card carries folder identity, date span, surface
  count, source count, image distribution, and scope note. Bottom card carries
  IMG00/IMG04 reading policy plus 3 chronological sample records.
- Record constraint: title <= 54 characters, source <= 54 characters, no
  filename-style titles, no bracket-only descriptive titles, no ellipsis.

### RN02 `pair-strip`
- Shape: two joined vertical 1:3 strips.
- Use: theme folders with enough records to read like a route or schedule.
- Content constraints: left strip carries folder stats and early samples; right
  strip carries later samples, source-note pairing, and a short scope reminder.
- Hard ratio: the joined card is 2:3; each child strip is 1:3.
- Record constraint: left strip shows 3 records, right strip shows 4 records.
  Titles must be <= 38 characters and sources <= 42 characters. Filename-style
  titles (`.jpg`, `.png`, etc.) and bracket-only descriptive titles are skipped
  for this layout. Do not truncate with ellipsis.

### RN03 `sparse-strip`
- Shape: one vertical 1:3 strip.
- Use: sparse folders with 1-2 records or uncertain membership.
- Content constraints: no padding with fake data. Show folder, span, one record
  title, image state, source, and the reading-note footer.

### RN04 `ledger`
- Shape: upright regular note.
- Use: medium or movement folders where the user needs a stable, readable record
  list rather than a special object shape.
- Content constraints: title, date span, scope, stats, and 3 sample rows.
- Record constraint: title <= 48 characters, source <= 56 characters, no
  filename-style titles, no bracket-only descriptive titles, no ellipsis.

## Stability

- Missing sample records must not throw. Render `unrecorded` for empty text.
- Reading note record rows must be selected before render according to the
  layout constraint. Do not rely on CSS clipping or post-render cropping.
- IMG00 remains empty by policy; reading notes may mention IMG00, but must not
  create a decorative image replacement.
- All badge marks are pure color dots with no text.
- Folder color dots are 1-4 pure color dots based on the real associated folder
  types. Region, theme, medium, and movement must each have a distinct color.

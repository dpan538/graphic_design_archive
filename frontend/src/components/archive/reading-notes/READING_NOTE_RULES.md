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
  IMG00/IMG04 reading policy plus 3-4 chronological sample records.

### RN02 `pair-strip`
- Shape: two joined vertical 1:3 strips.
- Use: theme folders with enough records to read like a route or schedule.
- Content constraints: left strip carries folder stats and early samples; right
  strip carries later samples, source-note pairing, and a short scope reminder.

### RN03 `sparse-strip`
- Shape: one vertical 1:3 strip.
- Use: sparse folders with 1-2 records or uncertain membership.
- Content constraints: no padding with fake data. Show folder, span, one record
  title, image state, source, and the reading-note footer.

### RN04 `ledger`
- Shape: upright regular note.
- Use: medium or movement folders where the user needs a stable, readable record
  list rather than a special object shape.
- Content constraints: title, date span, scope, stats, and 4-5 sample rows.

## Stability

- Missing sample records must not throw. Render `unrecorded` for empty text.
- IMG00 remains empty by policy; reading notes may mention IMG00, but must not
  create a decorative image replacement.
- All badge marks are pure color dots with no text.

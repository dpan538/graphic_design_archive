# Main Sheet Asset Rules

Main sheets are the highest-weight object record surface in the archive reader.
They are not bookmarks, reading notes, cards, slips, text pages, or appendix
leaves. A main sheet must carry object identity, source-return logic,
rights/image policy, classification evidence, and a compact visual reference.

## Frozen Layout Set

The first main-sheet group is frozen as four distinct directions. Do not merge
them into one template with different content.

### MS01 `protocol-ledger`
- Weight: `2`
- Role: dense control sheet.
- Use: records that need a strong object-control register, table rows, source
  rows, and folder rows.
- Constraint: image evidence stays secondary; the register and source logic are
  the page's main structure.

### MS02 `evidence-dossier`
- Weight: `3.5`
- Role: primary dramatic evidence dossier.
- Use: records with strong source context, high conceptual value, and enough
  description to support a large identity/score treatment.
- Constraint: keep the large score, small image plate, and source-return block.
  This layout should appear more often than MS01 and MS04.

### MS03 `split-bulletin`
- Weight: `3.5`
- Role: primary high-contrast bulletin.
- Use: records that benefit from a black identity field and a clear object
  evidence panel.
- Constraint: keep the black field restrained and functional. It must not become
  a decorative poster card.

### MS04 `grid-register`
- Weight: `1`
- Role: support register.
- Use: records that need classification clarity, rights/source fields, and a
  quieter grid treatment.
- Constraint: appears least often. The red grid is structural only and should
  not dominate the page.

## Distribution

Default layout ratio:

`MS01 : MS02 : MS03 : MS04 = 2 : 3.5 : 3.5 : 1`

Normalized target distribution:

- MS01: 20%
- MS02: 35%
- MS03: 35%
- MS04: 10%

The selector should favor MS02 and MS03 as the archive's primary main-sheet
voice. MS01 and MS04 remain available for variety and information-fit, but they
must not dominate a folder sequence.

## Hard Constraints

- Main sheets must use real project data.
- Main sheets must include a table/register component.
- Visual evidence must be present but modest; the photo/image must not become
  the full page subject.
- Use strong contrast and archival weight. Avoid lightweight web-card styling.
- Color is allowed only as restrained evidence or construction color.
- No fallback to an old main-sheet layout once this frozen set is active.
- No layout may rely on CSS clipping to hide overflow. Content must be selected
  to fit before render.

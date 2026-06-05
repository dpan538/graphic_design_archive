# Sub Sheet Asset Rules

Sub sheets sit one half-step below main sheets. They are stronger than
appendix leaves and text sheets, but they should not compete with the accepted
main-sheet group for top-level object authority.

## Position

- Hierarchy: `main sheet -> sub sheet -> appendix/text sheet -> card/slip -> bookmark`.
- Relative weight: `0.9` of main sheet.
- Role: strong secondary object surface for records that have enough evidence
  to deserve a sheet, but do not need the full main-sheet treatment.
- Sub sheets may carry a photo or source image, but it must remain a compact
  evidence component rather than the page subject.

## Group 01 Directions

Status: frozen. Placement ratio is `SS01:SS02:SS03:SS04 = 1.2:0.5:0.55:1.1`.

### SS01 `schedule-index`

- Direction: source scroll index, using a vertical axis, compact evidence image,
  and restrained badge/seal logic inspired by Japanese/Chinese graphic sheets.
- Use: source-context records, periodical records, and text-heavy objects where
  metadata can read as an ordered register.
- Constraint: the title, metadata, evidence image, and description must each
  occupy a distinct area. Do not allow numbered fields or the footer to overlap
  body text.

### SS02 `redline-cv`

- Direction: ink seal dossier with dark blue rules and a square source/image
  seal.
- Use: records with strong source image evidence and clear classification rows.
- Constraint: do not use a red grid system. This layout must remain visibly
  separate from the main-sheet grid-register language.

### SS03 `day-column`

- Direction: vertical chronology with modest image evidence.
- Use: records where date/year is a strong identifier and the image can act as
  a small proof stamp.
- Constraint: oversized chronology may lead the page, but the evidence text
  must remain readable and must not collide with the title.

### SS04 `resume-dossier`

- Direction: resume-like archival dossier.
- Use: single-object summaries with useful image, source, and classification
  fields.
- Constraint: keep the image small and the field rows compact. This is not a
  card, slip, or reading note.

## Group 02 Directions

Status: frozen. Placement ratio is `SS05:SS06:SS07:SS08 = 1:3:4:3`.
Group-level placement should favor Group 02 over Group 01: use
`Group 02:Group 01 = 1:0.85` when selecting between the two frozen groups.
This means Group 02 is the primary sub-sheet set, while Group 01 remains an
active but slightly less frequent companion set.

Group 02 must deliberately avoid Group 01's register/seal/day-column/dossier
language. It borrows from menus, invoices, stationery, and CV systems rather
than from the first main-sheet group.

### SS05 `layered-menu`

- Direction: layered paper/menu stack with side slips, central source menu, and
  compact circular evidence.
- Use: source-heavy records where many short fields can be scanned as a
  service/menu list.
- Constraint: side layers are structural information rails, not decoration. Do
  not let them become a fallback for clipped or unreadable data.

### SS06 `punched-letter`

- Direction: punched stationery letter with left binding marks, address logic,
  and restrained quotation/table information.
- Use: single-object records where archive metadata can read as a formal
  correspondence or quotation.
- Constraint: keep large quiet areas but preserve enough source rows to justify
  the sheet's hierarchy.

### SS07 `invoice-ledger`

- Direction: sparse invoice ledger with payment/source blocks and a precise
  line-item register.
- Use: grouped records, compound records, and source batches that need a
  transactional reading structure.
- Constraint: use real project metadata as line items; never fake prices or
  financial totals.

### SS08 `cv-sections`

- Direction: CV section sheet with thick section rules, a small evidence image,
  and grouped source/folder/record fields.
- Use: records with compact but varied metadata fields.
- Constraint: this layout can be typographically assertive, but it must remain
  a sub sheet rather than a card or visual poster.

## Hard Constraints

- Sub sheets must use real project data.
- Sub sheets must not reuse the first main-sheet group's layout language.
- Sub sheets must not be generated as old main-sheet fallbacks.
- No pure decorative background images.
- No CSS clipping as a substitute for content selection.
- Headless capture must verify no broken images and no meaningful overflow
  before a sub-sheet group is shown for review.

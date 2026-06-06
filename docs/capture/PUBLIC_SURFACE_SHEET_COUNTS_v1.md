# Public Surface Sheet Counts v1

Scope: generated public-surface payload and existing surface-group membership hints.

## Summary

- Public surfaces: 7716
- Main sheets: 7462
- Sub sheets: 240
- Text sheets: 242
- Inferred parent main sheets: 185
- Main sheets with more than 2 sub sheets: 121
- Main sheets with more than 5 text sheets: 1

## Template Distribution

- card.sparse.v0: 14
- sheet.compound.v0: 21
- sheet.img00.v0: 36
- sheet.main.v0: 7403
- sheet.text.v0: 242

## Publication Role Distribution

- (blank): 2
- main_sheet: 7462
- merge_candidate_support_packet: 14
- support_packet_appendix_text: 235
- thin_visual_support_packet: 3

## Interpretation

- `main_sheets` uses `publicationRole=main_sheet` because that is the project-facing role surfaced to the frontend.
- `sub_sheets` counts non-main sheet surfaces, including appendix/support/merge/thin visual sheets.
- Parent-child depth is inferred from `surface_group_memberships_v1`; it is a reporting aid, not a rights or authorship claim.

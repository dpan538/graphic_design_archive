# Public Surface Gate Recalculation

Date: 2026-06-01

## Reason

The archive had too many thin records appearing as full main sheets. The first
visual-verification pass used a permissive completeness threshold and an older
score that started every record at 20 points. That made true card/bookmark
states nearly impossible and weakened the distinction between a main sheet and
a sparse evidence record.

## New Gate

The recalculation uses a stricter 0-100 score.

| Score | Public disposition |
|---:|---|
| 75-100 + at least 80 source-reading characters | `main_sheet` |
| 75-100 but thin source text with displayable image | `thin_visual_support_packet` |
| 55-74 | `support_packet_appendix_text` |
| 40-54 | `merge_candidate_support_packet` |
| 20-39 | `card` |
| <20 | `bookmark_candidate` |

Main sheets can still keep a compact text block. Longer reading content should
move to attached text leaves. Evidence tables and rights/source trails should
move to AX appendices where appropriate.

## Recalculated Payload

Command:

```bash
python3 scripts/rebuild_public_surfaces_from_records.py
```

Result:

| Metric | Count |
|---|---:|
| Input rows after dedupe | 1092 |
| Public surfaces | 991 |
| Folder views | 44 |
| Image-ready surfaces (`IMG01`/`IMG02`/`IMG03`) | 899 / 991 |
| Image-ready percentage | 91% |
| Top-level appendix candidates | 237 |

Disposition counts:

| Disposition | Count |
|---|---:|
| `main_sheet` | 849 |
| `support_packet_appendix_text` | 125 |
| `merge_candidate_support_packet` | 14 |
| `thin_visual_support_packet` | 1 |
| compound / missing explicit disposition | 2 |

Template counts after recalculation:

| Template | Count |
|---|---:|
| `sheet.main.v0` | 889 |
| `sheet.text.v0` | 37 |
| `sheet.img00.v0` | 35 |
| `sheet.compound.v0` | 16 |
| `card.sparse.v0` | 14 |

Note: `sheet.main.v0` still includes some `support_packet` surfaces because the
current frontend template set does not yet have a separate support-packet
component. The data layer now marks these with `surfaceDisposition` /
`publicationRole`, so the frontend can render them differently without changing
capture data.

## Interpretation

The stricter gate reduced thin full-sheet promotion, but the current archive
still has many records with strong metadata and rights/image evidence. The next
quality step is not only score reduction. It is clustering:

- merge duplicate or near-duplicate records into canonical sheets;
- use weaker rows as source/citation/text appendices for stronger rows;
- move low-context but visually useful records into support packets;
- use cards only for compact citable records;
- reserve bookmarks for very sparse fragments, single-image markers, and
  orientation notes.

## Next Implementation Target

Build a duplicate/enrichment clustering pass that groups by:

- stable source identifier;
- canonical URL;
- normalized title + date + creator;
- shared collection or series;
- near-duplicate title within the same source;
- image perceptual hash when local image checks are allowed.

Each cluster should choose one canonical surface and attach other rows as:

- AX02 source/citation register;
- AX03 relation/classification appendix;
- text leaf material;
- child card/slip;
- bookmark fragment.

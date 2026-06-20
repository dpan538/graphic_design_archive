# Prefreeze Main/Sub/Text Method Validation Packet v1

Scope: non-mutating review packet for validating the main/sub/text method before any rebuild or role application.

This pass does not rebuild surfaces, does not apply overrides, does not download images, and does not change rights or image states.

## Why This Exists

The current archive has many surfaces that are technically main sheets but have not yet proven that they can act as durable research-packet anchors. This packet creates a reviewable sample so the method can be accepted, revised, or rejected before any structural mutation.

## Sample Size

- Total validation rows: 320.
- support_or_card_review: 120.
- soft_anchor_review: 80.
- packet_anchor_or_member_review: 42.
- strong_soft_anchor: 40.
- anchor_if_editorial_text_added: 38.

## Period Spread

- 1914_1945: 72.
- 1946_1969: 57.
- 1970_1989: 46.
- 2020_2026: 32.
- 1850_1899: 29.
- 2010_2019: 26.
- 1990_1999: 19.
- 2000_2009: 17.
- 1900_1913: 14.
- pre_1850: 8.

## Source-Family Spread

- Wikimedia Commons: 131.
- Wellcome Collection: 26.
- Internet Archive: 24.
- Georgia State CONTENTdm: 18.
- DigitalNZ: 17.
- Gallica / BnF APIs: 17.
- Library of Congress: 15.
- Princeton Figgy: 12.
- V&A Collections API: 11.
- Another Graphic: 8.
- Auckland Libraries Heritage Collections / CONTENTdm: 7.
- Malaysia Design Archive: 7.
- Smithsonian Open Access: 6.
- University of Miami Libraries Digital Collections / CONTENTdm: 5.
- Te Papa: 4.
- NAIDOC Poster Gallery: 4.
- Art Institute of Chicago API: 3.
- Cleveland Museum Open Access API: 1.
- Chinese Posters: 1.
- Los Angeles Public Library Tessa / CONTENTdm: 1.

## Validation Rule

- A main sheet may remain a provisional research-packet anchor when it has impact, source depth, relation density, period/region scarcity, or clear editorial need.
- A sub sheet is not a demotion of historical importance; it is a structural assignment under a stronger packet anchor.
- A text sheet is valid only when it adds interpretive, contextual, or methodological value beyond metadata repetition.
- Cards and appendix pages should preserve evidence, provenance, index, and lightweight context without overclaiming research anchor status.

## Advantages

- Keeps the archive from making premature structural changes on weak evidence.
- Lets main sheets carry provisional anchor intent without pretending every main already has a full dossier.
- Makes edge cases reviewable by period, region, source family, image state, source depth, and cluster size.
- Creates an audit trail that can be revisited after the next large data-cleaning cycle.

## Disadvantages

- It adds a review layer before visible structure improves.
- Some genuinely important isolated works may stay in review longer than ideal.
- Source-family imbalance can still affect the sample because the underlying archive is uneven.
- The method cannot prove final packet quality until reviewed rows are later tested in a small rebuild.

## Pass / Fail Meaning

- Pass: reviewers agree that the marker classes predict plausible main/sub/text/card/appendix roles often enough to justify a small applied override test.
- Revise: reviewers find a recurring failure pattern, such as Commons event photos, stamps, transnational region drift, or thin source text receiving too much anchor weight.
- Fail: reviewers conclude that object-level rows cannot be packetized until more source text or relation data is available.

## Next Permitted Action

Review this packet and fill the decision log template. Do not apply a new override layer until the decision log states which marker classes are accepted and which require new rules.

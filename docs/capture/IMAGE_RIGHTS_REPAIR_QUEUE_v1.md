# Image Rights Repair Queue v1

Scope: object-level advisory queue for source-visible, verified-open, and weighted-publication repair. This report does not upgrade image states.

## Safety Contract

- IMG01 and IMG03 are not automatically upgraded by this audit.
- Heuristics, LLM output, TOS/platform reputation, or source-family assumptions are not treated as rights evidence.
- Each candidate requires item-level source evidence before any future state change.
- Object-level grouping collapses repeated photos/views so one object contributes one repair unit.

## Summary

- object_total: 13659 (Object-level groups; repeated views/photos count once.)
- object_source_visible_rate: 97.91 (Objects with IMG01/IMG02/IMG03 evidence.)
- object_verified_open_rate: 87.96 (Objects with reviewed IMG03 evidence.)
- object_weighted_publication_rate: 93.36 (Object-level max image weight per object.)
- object_weighted_gap_to_95_points: 223.40 (Weighted points needed for the 95% publication-grade gate.)
- repair_candidate_objects: 1644 (Objects with source-visible, verified-open, or weighted-publication gaps.)
- source_priority_count: 802 (Source families represented in the repair queue.)
- candidate_img02_objects: 1321 (Source-hosted visible objects needing open-rights review.)
- candidate_img01_objects: 37 (Thumbnail-only objects needing item-level image/rights review.)
- candidate_img00_objects: 43 (Expected-image blockers needing source-visible repair.)
- candidate_img04_objects: 243 (Text/no-image objects needing text-state confirmation or visual record search.)

## Top Source Priorities

- Cooper Hewitt Collection GraphQL API: gap=61.65, candidates=137, IMG02=137, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- Wellcome Collection Catalogue API: gap=39.45, candidates=84, IMG02=81, IMG01=0, IMG00=3, IMG04=0, action=img02_open_rights_review
- Library of Congress loc.gov API: gap=38.90, candidates=50, IMG02=0, IMG01=37, IMG00=0, IMG04=13, action=img01_item_image_and_rights_review
- Georgia State University Library Digital Collections / CONTENTdm: gap=38.25, candidates=85, IMG02=85, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- Art Institute of Chicago API: gap=36.00, candidates=36, IMG02=0, IMG01=0, IMG00=35, IMG04=1, action=img00_source_visible_repair
- Internet Archive / text and periodical collections: gap=33.75, candidates=75, IMG02=75, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- V&A Collections API: gap=30.25, candidates=44, IMG02=25, IMG01=0, IMG00=0, IMG04=19, action=img02_open_rights_review
- Te Papa Collections Online: gap=25.75, candidates=56, IMG02=55, IMG01=0, IMG00=1, IMG04=0, action=img02_open_rights_review
- DigitalNZ: gap=22.95, candidates=51, IMG02=51, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- NAIDOC Poster Gallery: gap=22.05, candidates=49, IMG02=49, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- Princeton University Library Digital Collections / Figgy: gap=18.45, candidates=41, IMG02=41, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- The Met Open Access: gap=15.00, candidates=15, IMG02=0, IMG01=0, IMG00=0, IMG04=15, action=img04_text_state_review
- Another Graphic: gap=6.75, candidates=15, IMG02=15, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- Gallica / BnF APIs: gap=6.75, candidates=15, IMG02=15, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- Malaysia Design Archive: gap=5.95, candidates=12, IMG02=11, IMG01=0, IMG00=0, IMG04=1, action=img02_open_rights_review
- Malaysian Design Archive: gap=5.00, candidates=5, IMG02=0, IMG01=0, IMG00=0, IMG04=5, action=img04_text_state_review
- National Repository of Nigeria: gap=5.00, candidates=5, IMG02=0, IMG01=0, IMG00=0, IMG04=5, action=img04_text_state_review
- Asian Film Archive: gap=4.05, candidates=9, IMG02=9, IMG01=0, IMG00=0, IMG04=0, action=img02_open_rights_review
- American University of Beirut ScholarWorks: gap=4.00, candidates=4, IMG02=0, IMG01=0, IMG00=0, IMG04=4, action=img04_text_state_review
- Stellenbosch University Scholar: gap=4.00, candidates=4, IMG02=0, IMG01=0, IMG00=0, IMG04=4, action=img04_text_state_review

## Top Object Candidates

- SURF-ER1830R052 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Modern Poster
- SURF-ER1830R064 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Tell that to the Marines!
- SURF-ER1830R065 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · To the Amputees—Join the Workforce
- SURF-ER1830R066 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Buy a Little Present for the Kaiser
- SURF-ER1830R068 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Invest in the Victory Liberty Loan
- SURF-ER1830R069 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Keep These Off the U.S.A.
- SURF-ER1830R071 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Art Institute by the Elevated Lines
- SURF-ER1830R073 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Ascot By Motor Bus
- SURF-ER1830R075 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Rich repose of Autumn
- SURF-ER1830R076 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Centenary of the Omnibus
- SURF-MC1930R001 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Come Out at Easter
- SURF-MC1930R003 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · No. 2 Spring
- SURF-MC1930R004 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Whitsuntide in the Countryside
- SURF-MC1930R006 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · By the Rushy - Fringed Bank
- SURF-MC1930R042 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Time for Vengeance is Approaching
- SURF-MC1930R043 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Wedding Present
- SURF-MC1930R044 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · This Is the Enemy
- SURF-MC1930R045 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Thrill to the Heroic Struggle on "Our Russian Front"
- SURF-MC1930R046 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Thunderous Blow
- SURF-MC1930R047 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · A Belorussian Landscape
- SURF-MC1930R048 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · An Attempt Using Unfit Means
- SURF-MC1930R049 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Our One-Thousandth Blow
- SURF-MC1930R050 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Hour Approaches
- SURF-MC1930R051 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · The Search for Human Resources in Germany
- SURF-MC1930R052 · IMG00 · gap=1.00 · Art Institute of Chicago API · img00_source_visible_repair · Untitled

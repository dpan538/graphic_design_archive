# Layered Image and Source Metrics v1

Date: 2026-06-06

Scope: capture records, not final public surfaces. These metrics measure the raw/candidate corpus before grouping and surface assignment.

## Overall

- Capture records: 3815
- Source-visible coverage: 92.24%
- Publication-grade candidate coverage: 89.49%
- Weighted publication image rate: 68.27% (2604.40 weighted points)
- Open-image candidate coverage: 42.80%
- Rights-labeled coverage: 100.00%
- Unclear image-state rate: 0.10%
- Duplicate image URL record rate: 1.86%

## Period Bands

- 2000_2026: records=1403, source-visible=88.17%, publication-grade=88.10%, weighted=59.45%, open=30.86%, duplicate-url=0.86%
- pre_1930: records=1028, source-visible=96.69%, publication-grade=93.39%, weighted=82.35%, open=60.21%, duplicate-url=3.79%
- 1930_1970: records=919, source-visible=95.43%, publication-grade=88.25%, weighted=70.04%, open=50.38%, duplicate-url=1.85%
- 1970_2000: records=391, source-visible=97.44%, publication-grade=97.44%, weighted=67.56%, open=30.18%, duplicate-url=0.00%
- undated_or_unparsed: records=74, source-visible=40.54%, publication-grade=35.14%, weighted=21.42%, open=0.00%, duplicate-url=4.05%

## Lowest Weighted Publication Periods

- undated_or_unparsed: weighted=21.42% (15.85 weighted points / 74 records)
- 2000_2026: weighted=59.45% (834.15 weighted points / 1403 records)
- 1970_2000: weighted=67.56% (264.15 weighted points / 391 records)
- 1930_1970: weighted=70.04% (643.65 weighted points / 919 records)

## Source Families

- unmapped_source_family: records=2816, source-visible=93.71%, publication-grade=92.05%, weighted=72.22%, open=52.20%
- independent_design_archive_or_publication: records=304, source-visible=76.64%, publication-grade=76.64%, weighted=60.12%, open=51.32%
- government_or_public_cultural_database: records=207, source-visible=97.58%, publication-grade=97.58%, weighted=76.16%, open=0.00%
- general_archive_or_collection: records=172, source-visible=95.35%, publication-grade=68.02%, weighted=45.96%, open=0.00%
- university_repository_or_special_collection: records=158, source-visible=92.41%, publication-grade=92.41%, weighted=51.04%, open=0.00%
- library_or_national_library: records=110, source-visible=89.09%, publication-grade=89.09%, weighted=51.23%, open=6.36%
- community_activist_diaspora_archive: records=32, source-visible=78.12%, publication-grade=78.12%, weighted=42.97%, open=0.00%
- poster_film_festival_design_archive: records=13, source-visible=92.31%, publication-grade=7.69%, weighted=4.23%, open=0.00%
- aggregator_or_discovery_router: records=1, source-visible=0.00%, publication-grade=0.00%, weighted=0.00%, open=0.00%
- municipal_or_state_archive: records=1, source-visible=0.00%, publication-grade=0.00%, weighted=0.00%, open=0.00%
- newspaper_magazine_ocr_portal: records=1, source-visible=0.00%, publication-grade=0.00%, weighted=0.00%, open=0.00%

## Duplicate Image URL Warnings

- 3 records share `https://wellcomecollection.org/placeholder.jpg`; sources=Wellcome Collection Catalogue API; periods=1930_1970; ids=IR1970R044 | IR1970R047 | IR1970R060
- 2 records share `https://www.artic.edu/iiif/2/59320f53-e6a1-4fb7-0246-ff70542460bf/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP001 | ER1830R066
- 2 records share `https://www.artic.edu/iiif/2/119dba14-acf2-cdcd-e9e6-b9cd38bc3aad/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP003 | ER1830R055
- 2 records share `https://www.artic.edu/iiif/2/01e6ed5b-5b03-3929-f424-96e4bcbbec31/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP004 | ER1830R065
- 2 records share `https://www.artic.edu/iiif/2/7aeac16d-ac42-79f1-d49e-fb7b49193ae3/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP005 | ER1830R069
- 2 records share `https://www.artic.edu/iiif/2/40d361de-3296-7ed1-a6a9-f592457864b0/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=1930_1970; ids=ECAP006 | MC1930R062
- 2 records share `https://www.artic.edu/iiif/2/51548c3f-089f-4258-00ee-67087fb2d305/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=1930_1970; ids=ECAP007 | MC1930R044
- 2 records share `https://www.artic.edu/iiif/2/965eac7d-008c-2812-7807-a91071de7bfd/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP009 | ER1830R068
- 2 records share `https://www.artic.edu/iiif/2/48c8b6f9-fc55-5717-88fa-d4f468b048cf/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=1930_1970; ids=ECAP010 | MC1930R048
- 2 records share `https://www.artic.edu/iiif/2/0d5db4d9-0725-7ecd-e44b-95d0750949a3/full/843,/0/default.jpg`; sources=Art Institute of Chicago API; periods=pre_1930; ids=ECAP011 | ER1830R052

## Interpretation

- Source-visible coverage means an image or source viewer appears to exist.
- Publication-grade candidate coverage requires IMG02/IMG03 plus source return and rights labeling.
- Weighted publication rate uses conservative visual-evidence weights: {'IMG03': 0.9, 'IMG02': 0.55, 'IMG01': 0.3, 'IMG00': 0.0, 'IMG04': 0.0}.
- Open-image coverage is deliberately stricter and should not be confused with IMG02 source-hosted visibility.
- Duplicate image URL warnings identify repeated visual evidence that may be legitimate series reuse, source thumbnails, or a data bug; these rows require review before public rebuild.

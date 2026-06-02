# Layered Image and Source Metrics v1

Date: 2026-06-02

Scope: capture records, not final public surfaces. These metrics measure the raw/candidate corpus before grouping and surface assignment.

## Overall

- Capture records: 1524
- Source-visible coverage: 92.98%
- Publication-grade candidate coverage: 86.09%
- Weighted publication image rate: 61.27% (933.80 weighted points)
- Open-image candidate coverage: 10.70%
- Rights-labeled coverage: 100.00%
- Unclear image-state rate: 0.26%
- Duplicate image URL record rate: 4.53%

## Period Bands

- 1930_1970: records=523, source-visible=92.16%, publication-grade=79.54%, weighted=55.36%, open=13.77%, duplicate-url=3.25%
- pre_1930: records=467, source-visible=92.72%, publication-grade=85.44%, weighted=73.17%, open=12.42%, duplicate-url=8.35%
- 1970_2000: records=279, source-visible=98.92%, publication-grade=98.92%, weighted=61.43%, open=6.45%, duplicate-url=0.00%
- 2000_2026: records=227, source-visible=93.83%, publication-grade=93.39%, weighted=54.91%, open=6.61%, duplicate-url=4.41%
- undated_or_unparsed: records=28, source-visible=46.43%, publication-grade=32.14%, weighted=23.21%, open=0.00%, duplicate-url=10.71%

## Lowest Weighted Publication Periods

- undated_or_unparsed: weighted=23.21% (6.50 weighted points / 28 records)
- 2000_2026: weighted=54.91% (124.65 weighted points / 227 records)
- 1930_1970: weighted=55.36% (289.55 weighted points / 523 records)
- 1970_2000: weighted=61.43% (171.40 weighted points / 279 records)

## Source Families

- unmapped_source_family: records=587, source-visible=96.42%, publication-grade=88.42%, weighted=64.57%, open=0.00%
- independent_design_archive_or_publication: records=298, source-visible=77.18%, publication-grade=77.18%, weighted=60.77%, open=52.35%
- government_or_public_cultural_database: records=197, source-visible=100.00%, publication-grade=100.00%, weighted=78.63%, open=0.00%
- general_archive_or_collection: records=162, source-visible=97.53%, publication-grade=68.52%, weighted=46.76%, open=0.00%
- university_repository_or_special_collection: records=146, source-visible=95.89%, publication-grade=95.89%, weighted=52.98%, open=0.00%
- library_or_national_library: records=100, source-visible=94.00%, publication-grade=94.00%, weighted=54.15%, open=7.00%
- community_activist_diaspora_archive: records=23, source-visible=91.30%, publication-grade=91.30%, weighted=50.22%, open=0.00%
- poster_film_festival_design_archive: records=11, source-visible=100.00%, publication-grade=0.00%, weighted=0.00%, open=0.00%

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

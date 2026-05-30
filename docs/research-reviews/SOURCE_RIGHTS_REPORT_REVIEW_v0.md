# Source & Rights Feasibility Report Review v0

**Date:** 2026-05-29  
**Reviewed file:** `Source and Rights Feasibility Audit for a Modern Graphic Design History Research Gateway.docx`

## Executive Read

The report says experimental ingest can begin, but only with conservative guardrails.

Decision:

- `SOURCE_RIGHTS_READY_FOR_EXPERIMENTAL_INGEST: yes`

Important condition:

- the project must not start image-rich ingest until source-level policy, item-level rights overrides, versioned source terms reviews, and renderer-level `IMG00` default behavior are enforced.

The main risk is not lack of sources. The main risk is accidental escalation from metadata indexing to image reuse.

## Source Policy Summary

Safest for open image display / `IMG03`:

- Smithsonian Open Access;
- The Met Open Access API;
- carefully filtered Rijksmuseum open-rights subsets;
- explicit CC/PD Internet Archive items, with item-level review.

Safest for metadata/API ingest:

- Wikidata;
- Getty Vocabularies;
- VIAF;
- DPLA metadata;
- Europeana metadata;
- HathiTrust metadata;
- Tate metadata;
- MoMA research datasets;
- Trove metadata;
- DigitalNZ metadata;
- Te Papa metadata;
- Library of Congress metadata;
- official museum APIs where image policy remains separate.

Best controlled thumbnail test / `IMG01`:

- DigitalNZ small-thumbnail metadata records.

Best IIIF/embed tests / `IMG02`:

- carefully reviewed Rijksmuseum records;
- Library of Congress records with rights-advisory capture;
- Europeana records with explicit permissive rights URI and IIIF manifest.

Default link-only / `IMG00` sources:

- People’s Graphic Design Archive;
- Fonts In Use;
- Letterform Archive;
- SAHA Poster Collection;
- Memoria Chilena;
- many non-reviewed Internet Archive items;
- mixed-rights Trove items;
- mixed-rights NDL items;
- aggregator records whose provider asset terms are unclear.

Rendering clarification:

- `IMG00` means the fixed image area remains, but it renders an intentionally empty archive frame only: linework/shadow if needed, short rights/source text, and a source link.
- `IMG00` must not render the source image, thumbnail, screenshot, preview, or local copy.

Manual review before ingest/display:

- V&A image-bearing records;
- Rijksmuseum records without clearly open rights labels;
- Te Papa records without explicit image license;
- Library of Congress records with uncertain advisory status;
- BNDigital image-bearing records;
- SAOA page-image reuse;
- culturally sensitive Trove or Te Papa records.

## Database Work Completed From Report

Created:

- `db/008_source_rights_policy_skeleton.sql`
- `data/experimental_ingest_shortlist.csv`

Added source/right policy enums:

- `source_record_policy`
- `public_display_policy`
- `asset_origin`
- `terms_review_decision`

Expanded:

- `sources`: source-level default record policy, display policy, image zone, licenses, terms URLs, API/robots/rate-limit fields, item-level rights support, protocol/privacy flags.
- `source_terms_reviews`: versioned policy snapshot fields, key clauses, reuse summaries, prohibited uses, rate limits, takedown contact, decision.
- `rights_reviews`: item-level rights basis, evidence URL/date, attribution, display booleans, manual review requirement, normalized image zone and display policy.
- `image_assets`: remote/local asset origin, rights status, source item URL, IIIF info, manifest URL, attribution, checksum, suppression, no-local-copy reason.
- `ingestion_runs`: harvest scope, API version, query/set, rights/terms block counts, review counts, thumbnail/IIIF metrics, policy snapshot.

Added:

- `experimental_ingest_candidates`

Added read models:

- `api_source_policy_summary`
- `api_source_terms_review_policy`
- `api_experimental_ingest_candidates`

## First Experimental Ingest Shortlist

The shortlist contains 24 candidates, designed to test:

- `IMG03` open image records;
- `IMG02` IIIF/embed records;
- `IMG01` thumbnail-only records;
- `IMG00` link-only / metadata-only records;
- non-Latin scripts;
- community/protocol risk;
- born-digital and web archive records;
- authority-only records with no image risk;
- negative rights tests.

Stored in:

- `data/experimental_ingest_shortlist.csv`

## Implementation Boundary

This review does not authorize actual crawling yet.

Before any source is fetched:

1. create or approve a `source_terms_reviews` row;
2. assign default source policy in `sources`;
3. define ingest scope in `ingestion_runs`;
4. ensure item-level records default to `IMG00`;
5. require rights evidence before any `IMG01`, `IMG02`, or `IMG03` escalation.

## Next Step

The next practical task is to convert the 24 shortlist rows into a staged experimental ingest plan:

- pick 8-12 records first, not all 24;
- include at least one `IMG03`, one `IMG02`, one `IMG01`, and several `IMG00`;
- run manual terms review before any automated fetch;
- populate the paper-surface model with real six-table rows;
- evaluate field length, multilingual labels, rights capsule behavior, and source-link ergonomics before visual system research resumes.

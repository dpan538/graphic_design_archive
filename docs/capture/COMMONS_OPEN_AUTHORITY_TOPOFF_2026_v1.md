# Commons Open Authority Topoff 2026 v1

Access date: 2026-06-13

Scope: narrow source-only topoff for
`capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv`.
The script uses Wikimedia Commons file metadata, source links, source-hosted
image URLs, and open-license extmetadata only.

## Result

- Final authority-weighted records: 5,055.
- Final distinct active source names: 5,021.
- Final distinct source identifiers: 5,055.
- Image state: IMG03 only, 5,055 records.
- 2026 records: 53, or about 1.05% of the authority-weighted batch.
- Topoff script added 377 records after the general authority runner slowed
  near the 5,000-row target.
- The controlled-expansion topoff attempt added 10 records but was stopped
  because it was too low-yield for this round.

## Final Authority Batch Distribution

Period distribution:

- pre_1940: 1,927
- 2000_2026: 1,617
- 1940_1970: 898
- 1970_2000: 613

Macro-region distribution:

- Eastern Europe: 1,069
- Africa: 1,034
- Latin America: 842
- Middle East and North Africa: 686
- Southeast Asia: 441
- South Asia: 416
- Oceania: 204
- East Asia: 187
- Central Asia: 176

Object-family distribution:

- postage_stamp: 1,445
- poster: 1,403
- label_packaging: 889
- advertising_trade: 807
- book_cover: 173
- brochure_pamphlet: 108
- film_poster: 97
- typography_identity: 64
- political_poster: 37
- magazine_cover: 27
- travel_poster: 5

## Cleaning And Metrics

- Commons open-source cleaning audit: 11,051 records audited across recent
  Commons open batches; 11,039 release-ready; 6 weak-graphic review; 6 duplicate
  review.
- Layered image/source metrics across all capture records: 19,886 records;
  source-visible 98.51%; publication-grade 98.08%; weighted publication 95.01%;
  open image 89.03%; IMG04 295.
- Source coverage v1 after this capture: active source count 18,312; source
  pool 100.00%; time-weighted source coverage 82.62%; strict distribution
  adjusted source coverage 26.23%.
- Source coverage v2 is pre-rebuild: source-visible surface rate 97.80%;
  research-quality adjusted source coverage 2.31%.

## Boundary

- No image binaries, thumbnails, screenshots, browser sessions, cookies, raw API
  payload dumps, or local image files were saved.
- IMG03 is assigned only from Commons open-license extmetadata.
- The capture is not included in public surfaces yet; frontend/public-surface
  rebuild is deferred to a smaller isolated pass.
- Source links and source-hosted image URLs are evidence routes, not ownership
  claims.
- The topoff plan uses whitelisted country/object queries because the broad
  authority queue became sparse near the target.

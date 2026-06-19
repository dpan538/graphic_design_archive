# Pre-freeze Data Cleaning Audit v1

Scope: consolidated, non-mutating audit across capture records, generated public surfaces, release snapshot, temporal anomaly review, recent-object quality review, and source coverage diagnostics.

## Headline

- Capture records scanned: 19898
- Public surfaces: 13680
- Active public sources: 12342
- Object source-visible: 97.91%
- Object verified-open: 87.96%
- Object IMG04: 1.78%
- Strict distribution adjusted coverage: 26.23%
- Research-quality adjusted source coverage: 2.31%

## Cleaning Queue

- P0: 5287
- P1: 2566
- P2: 2670

P0 means the row can materially distort release metrics if kept as a primary object: access-year/span records, post-2010 stamp drift, event/memory material, context images, or source-page/profile rows.

## Action Counts

- card_or_appendix_reclass_review: 2930
- metadata_cleanup_review: 2670
- recent_stamp_event_reclassification: 1643
- deduplicate_or_merge_review: 1141
- manual_rights_or_date_review: 1089
- date_or_span_reclass_review: 1050

## P0 Examples

- CAW2026R00122 · 1837 · Middle East and North Africa / Egypt · STAMPS (4263067047).jpg · event_photo_memory_or_commemoration
- CAW2026R00207 · 1853 · Oceania / Pacific / Aotearoa New Zealand · Wellington Provincial Council elections, 1853.jpg · context_image_or_environmental_poster
- CAW2026R00222 · 1857 · Latin America / Caribbean / Panama · Panama 1949 Mi 387 stamp (75th anniversary of the UPU. Alejandro Melendez G. (' 1857), teacher).jpg · event_photo_memory_or_commemoration
- CAW2026R00315 · 1870 · Eastern Europe / Caucasus / Ukraine · Hubert Lanzinger Der Bannerträger (The Standard bearer) Oil on plywood ca 1934-36 Adolf Hitler as knight Denazified hole in Hitler's face scrathes US Army Center of Military History USHMM No known copyright restrictions 2450324-2396x2.jpg · event_photo_memory_or_commemoration
- CAW2026R00336 · 1874 · Eastern Europe / Caucasus / Ukraine · Ludwig HOHLWEIN Reichs Parteitag-Nürnberg 1936 Hitler Ansichtskarte Propaganda Drittes Reich Nazi Germany Veterans Picture postcard Public Domain No known copyright 627900-000016.jpg · event_photo_memory_or_commemoration
- CAW2026R00352 · 1877 · Eastern Europe / Caucasus / Bulgaria · Stamp of Russia 2013 No 1686 Russo-Turkish War 1877-78.jpg · event_photo_memory_or_commemoration
- CAW2026R00469 · 1885 · Central Asia / Uzbekistan · The Soviet Union 1965 CPA 3211 stamp (80th birth anniversary of Yuldash Akhunbabaev, Soviet Uzbek politician, revolutionary, and communist activist).jpg · event_photo_memory_or_commemoration
- CAW2026R00470 · 1885 · Central Asia / Uzbekistan · Почтовая марка СССР № 3211. 1965. Деятели КПСС и Советского государства.jpg · event_photo_memory_or_commemoration
- CAW2026R00612 · 1890 · Latin America / Caribbean / El Salvador · El Salvador 1892 10c Seebeck essay vermillion.jpg · event_photo_memory_or_commemoration
- CAW2026R00613 · 1890 · Latin America / Caribbean / El Salvador · El Salvador 1892 11c Seebeck essay blue.jpg · event_photo_memory_or_commemoration
- CAW2026R00614 · 1890 · Latin America / Caribbean / El Salvador · El Salvador 1892 11c Seebeck essay pair orange brown.jpg · event_photo_memory_or_commemoration
- CAW2026R00615 · 1890 · Latin America / Caribbean / El Salvador · El Salvador 1892 1p Seebeck essay pair green.jpg · event_photo_memory_or_commemoration

## Interpretation

- Source count is now a capacity indicator, not the defining release-quality metric.
- The largest blockers are distribution, research-quality main-sheet structure, rights verification, and recent-object contamination.
- Broad Commons search should stay paused except for manually verified collection gaps; institution APIs and known collections are better next capture targets.
- A larger cleaning pass is needed before any full surface rebuild, otherwise noisy rows will be promoted into main sheets and distort release gates.

## Output Files

- `data/prefreeze_data_cleaning_summary_v1.csv`
- `data/prefreeze_data_cleaning_priority_queue_v1.csv`
- `data/prefreeze_source_authority_concentration_v1.csv`
- `data/prefreeze_region_period_gap_matrix_v1.csv`

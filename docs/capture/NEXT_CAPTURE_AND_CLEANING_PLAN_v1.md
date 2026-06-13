# Next Capture And Cleaning Plan v1

This plan schedules the next work cycle after the region/geography confidence gate. It does not run capture or mutate archive data.

## Current Read

- Active public sources: 12342; full 20,000-source gap: 7658; 80% release floor gap: 3658.
- Source-visible: 97.91%; verified-open: 87.96%; weighted publication-grade: 93.36%; IMG04: 1.78%.
- Period source gaps: pre_1930: 550; 1930_1970: 3268; 1970_2000: 1852; 2000_2026: 787.
- Top rights-repair sources: Cooper Hewitt Collection GraphQL API (61.65 pts); Wellcome Collection Catalogue API (39.45 pts); Library of Congress loc.gov API (38.90 pts); Georgia State University Library Digital Collections / CONTENTdm (38.25 pts); Art Institute of Chicago API (36.00 pts); Internet Archive / text and periodical collections (33.75 pts); V&A Collections API (30.25 pts); Te Papa Collections Online (25.75 pts).
- The immediate bottleneck is not raw source discovery alone; it is controlled attribution, source authority, rights evidence, and text-supported surface value.
- The next capture cycle should start after the first cleaning pass so new sources inherit stricter labels.

## Region Surface Snapshot

- Unresolved region: 3945
- Indonesia: 1079
- Mexico: 561
- Brazil: 486
- Argentina: 435
- Iran: 406
- India: 356
- Aotearoa New Zealand: 338
- Colombia: 334
- Kazakhstan: 327
- Bolivia: 310
- Iraq: 301
- France: 298
- Algeria: 291
- United States: 279

## Plan Phases

- capture_tranche_a: 9
- cleaning_first: 3
- capture_tranche_b: 1
- method_lock: 1

## Priorities

- P1: 7
- P0: 4
- P2: 3

## Recommended Sequence

- P0 `region_geo_safe_apply`: 8 hardened direct-conflict candidates (8 reviewed patch candidates)
- P0 `historical_split_policy`: Mexico; United States military occupation context (220 reviewed decisions)
- P0 `rights_repair_before_volume`: Cooper Hewitt; Wellcome; Library of Congress; GSU CONTENTdm; AIC; Internet Archive; V&A; Te Papa (repair 800-1200 candidate objects or at least 223.40 weighted-publication points)
- P0 `source_pool_5000_after_cleaning`: first 5,000 new active public-payload-ready sources (5,000 successful active sources after item/image capture, surface build, and metrics)
- P1 `authority_institution_sources`: art schools, national libraries, design museums, university special collections, cultural institutes (1,400-1,700 successful active sources)
- P1 `contemporary_studio_platform_school_sources`: workshops, art/design schools, community design programs, studios, biennales, visual communication platforms (1,100-1,300 successful active sources)
- P1 `southeast_asia_modern_contemporary`: Indonesia (381 review hints); Vietnam; Philippines; Thailand; Malaysia; Singapore (500-650 successful active sources)
- P1 `caucasus_central_asia_repair`: Caucasus (64); Azerbaijan (39); Georgia (38); Armenia; Kazakhstan; Uzbekistan; Kyrgyzstan (350-450 successful active sources)
- P1 `south_asia_bangladesh_nepal_pakistan`: Bangladesh (22); Pakistan; Nepal; Sri Lanka; India non-canonical regional sources (450-550 successful active sources)
- P1 `mena_africa_noncanonical`: Egypt; Morocco; Tunisia; Algeria; Lebanon; Palestine; Nigeria; Ghana; Kenya; Ethiopia; Senegal; South Africa (650-800 successful active sources)
- P1 `pre_1940_historical_continuity`: pre-1930 gap plus 1930-1940 advertising, printing, visual education, colonial/postcolonial print cultures (450-650 successful active sources)
- P2 `latin_america_cleanup_and_growth`: Mexico; Brazil; Argentina; Chile; Colombia; Peru; Cuba; Caribbean design/print cultures (350-450 successful active sources after conflict cleanup)
- P2 `second_5000_after_audit`: second 5,000 successful active sources only after tranche A release snapshot (5,000 additional successful active sources, then full rebuild and gate audit)
- P2 `classification_deep_research_inputs`: movement/theme/method terms that remain unstable (one evidence packet per disputed method family)

## Operating Rules

- Do not download images during source discovery.
- Do not upgrade IMG01/IMG03 from heuristic, platform, TOS, or LLM signals.
- Count new successful sources only after item/image capture, surface build, archive incorporation, and release-gate metrics.
- Keep IMG04 low, but do not remove text capture pressure; text is required for research-packet value.
- Use sandbox/sample runs before full rebuilds whenever the task does not require rebuilding all surfaces.

## Output File

- `data/next_capture_plan_v1.csv`

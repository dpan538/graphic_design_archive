# Spacetime research-readiness census · v1

**Status: CANDIDATE — pending the owner's approval. Nothing here is wired into the UI.**

Release `v49-api-contract-fresh-c` · projection `trace-spacetime-v1` (`f751b0f432ff684f…`) · generator `scripts/spacetime/census_spacetime_research_readiness_v1.py` · outputs `data/spacetime_research_readiness_census_v1.csv`, `data/spacetime_research_region_registry_candidate_v1.json`.

## 1 · Why

The sealed v49 Spacetime projection governs 93 geographies over 23 decades (373 non-zero period × geography cells). Governance means every one of them is *safe to show*; it does not mean every one of them can carry research. Exposing all 93 as equal options on a world map overstates the archive's geographic and temporal coverage: most decades are carried by a handful of places, and most places are a handful of records. This census evaluates every governed geography for research readiness and proposes a separate, versioned **Spacetime Research Region Registry** that decides which geographies are promoted into the normal public Spacetime UI. The projection underneath is untouched; a geography that is not promoted is not deleted and not held — it is `NOT_RESEARCH_READY` for this Spacetime release.

A first-release Research Region maps directly to one existing governed geography identity. No macro-region (Western Europe, East Asia, Latin America, Global North) is composed in this round; that would be a separate governance decision.

## 2 · Inputs (all frozen, all one release)

- `frontend/generated/trace-spacetime-v1/` — geography registry (93), period-region aggregates (23 periods, per-cell record counts, denominators, precision breakdowns), record index (7,995 public records with geography ids, period ids, governed year extent and precision), time buckets; payload sha256 checked against the manifest.
- `frontend/generated/source-viewer-v49/source-viewer.json` — the public source record URL of every record; the URL host is the record's source institution (13 hosts). Cross-checked read-only against the frozen candidate payload's `objects.source_name`: each host maps to exactly one institution (the V&A's two API names share one host, as do the Library of Congress's two).
- `frontend/generated/reader-eligibility-v49/eligibility.json` — `INDEX_ELIGIBLE` (a human-readable title) vs `RECORD_ONLY` per record: the reader-facing usability of a matching-records list.
- `frontend/generated/visual-availability-v49/census.json` — whether a record has a visual route (`SOURCE_VIEWER_AVAILABLE` or `REMOTE_VISUAL_CANDIDATE_VERIFIED`); reported, not gated.
- Nothing is inferred. Where a value is not in the frozen public resources it is not computed.

## 3 · Metrics per geography

| Metric | Definition |
| --- | --- |
| Public records | distinct public records whose governed geography ids include the geography |
| Records by decade | the sealed period-region cell counts (INTERVAL_OVERLAP: a ranged record counts in every decade it overlaps, so the decade sum can exceed the record count); verified equal to a recount from the record index |
| Active decades | decades with at least one record |
| Substantive decades | decades with at least 5 records — the second sealed count tier (1–4 · 5–24 · 25–99 · 100+) |
| Longest substantive run | the longest sequence of consecutive substantive decades |
| Median records per active decade | the typical active decade |
| Peak-decade concentration | the largest decade's share of the geography's decade assignments; and the records outside that decade |
| Share of period | the geography's records over the period's public denominator, per decade; rank within the decade |
| Year-or-finer share | records whose governed precision is `year`, `month` or `day` (vs `approximate`, `range`) |
| Institutions | distinct source hosts; the top institution's share; the records outside it |
| Reader-facing | `INDEX_ELIGIBLE` records (a human-readable title) |
| Visual route | records with a source-viewer frame or a verified remote image |
| Mapping state | the registry's `mapped` / `aggregate_only` / `unmapped` |

## 4 · Observed distribution (93 geographies)

| Metric | min | p25 | p50 | p75 | p90 | max |
| --- | --- | --- | --- | --- | --- | --- |
| Public records | 1.0 | 2.0 | 8.0 | 40.0 | 128.6 | 3,214.0 |
| Active decades (non-zero) | 1.0 | 1.0 | 2.0 | 4.5 | 10.6 | 22.0 |
| Substantive decades (≥5) | 0.0 | 0.0 | 1.0 | 2.0 | 6.0 | 21.0 |
| Longest consecutive substantive run | 0.0 | 0.0 | 1.0 | 2.0 | 3.6 | 20.0 |
| Median records per active decade | 1.0 | 1.0 | 2.5 | 5.8 | 11.3 | 57.0 |
| Peak-decade concentration % | 17.4 | 50.0 | 66.7 | 100.0 | 100.0 | 100.0 |
| Records outside the peak decade | 0.0 | 0.0 | 2.0 | 15.0 | 73.2 | 1,621.0 |
| Largest share of a period denominator % | 0.1 | 0.3 | 1.7 | 5.0 | 17.6 | 100.0 |
| Institutions | 1.0 | 1.0 | 1.0 | 3.0 | 4.0 | 6.0 |
| Top-institution share % | 34.5 | 83.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Records outside the top institution | 0.0 | 0.0 | 0.0 | 3.5 | 41.2 | 710.0 |
| Year-or-finer share % | 66.7 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Reader-facing share % | 30.4 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Visual-route share % | 0.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

The archive is steep: 47 of the 93 governed geographies have 8 records or fewer, 47 are active in two decades or fewer, 24 have at most 2 records. Only 11 geographies reach the top sealed count tier (100+) and only 9 have a run of four or more substantive decades; 53 are single-institution.

### Per-decade coverage

| Decade | Public records | Geographies | Mapped | Substantive (≥5) | Top geography | Top records | Top share % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1800s | 12 | 4 | 1 | 1 | United Kingdom | 7 | 58.3 |
| 1810s | 6 | 3 | 1 | 0 | United Kingdom | 2 | 33.3 |
| 1820s | 10 | 3 | 1 | 1 | United Kingdom | 8 | 80.0 |
| 1830s | 16 | 1 | 1 | 1 | United Kingdom | 16 | 100.0 |
| 1840s | 26 | 2 | 2 | 1 | United Kingdom | 25 | 96.2 |
| 1850s | 49 | 2 | 2 | 1 | United Kingdom | 48 | 98.0 |
| 1860s | 79 | 3 | 3 | 1 | United Kingdom | 77 | 97.5 |
| 1870s | 61 | 4 | 4 | 1 | United Kingdom | 58 | 95.1 |
| 1880s | 48 | 6 | 6 | 2 | United Kingdom | 37 | 77.1 |
| 1890s | 211 | 12 | 12 | 7 | United Kingdom | 96 | 45.5 |
| 1900s | 164 | 9 | 9 | 5 | United Kingdom | 111 | 67.7 |
| 1910s | 188 | 15 | 13 | 4 | United Kingdom | 101 | 53.7 |
| 1920s | 257 | 16 | 16 | 9 | United Kingdom | 145 | 56.4 |
| 1930s | 265 | 21 | 20 | 10 | Norway | 58 | 21.9 |
| 1940s | 270 | 20 | 19 | 7 | United Kingdom | 56 | 20.7 |
| 1950s | 383 | 20 | 20 | 11 | United Kingdom | 233 | 60.8 |
| 1960s | 1,397 | 55 | 52 | 33 | United States | 157 | 11.2 |
| 1970s | 1,096 | 48 | 45 | 27 | United States | 226 | 20.6 |
| 1980s | 1,898 | 22 | 19 | 10 | United Kingdom | 1,630 | 85.9 |
| 1990s | 441 | 20 | 20 | 8 | United Kingdom | 157 | 35.6 |
| 2000s | 646 | 43 | 42 | 14 | United States | 274 | 42.4 |
| 2010s | 351 | 29 | 28 | 13 | United States | 119 | 33.9 |
| 2020s | 159 | 15 | 15 | 10 | Wallis and Futuna | 28 | 17.6 |

Before the 1890s no decade has more than 2 geographies with five or more records, and in 8 of those 9 decades one geography holds more than half of the decade. Only the 1960s and 1970s have more than 20 substantive geographies. A world map of the other decades draws a global coverage the archive does not have.

## 5 · The gates (thresholds derived from §4)

| Criterion | STRICT | RELAXED |
| --- | --- | --- |
| mapped | 1 | 1 |
| min_total_public_records | 100 | 25 |
| min_substantive_periods | 6 | 3 |
| min_longest_substantive_run | 4 | 2 |
| max_peak_period_concentration_pct | 50.0 | 75.0 |
| min_off_peak_records | 100 | 25 |
| min_source_count | 2 | 2 |
| min_outside_top_source_records | 25 | 5 |
| min_precise_share_pct | 90.0 | 80.0 |
| min_reader_facing_records | 100 | 25 |

Derivation:

- **Absolute floors reuse the sealed count tiers** (`TRACE_NATIVE_COUNT_TIERS`: 1–4 · 5–24 · 25–99 · 100+). STRICT requires the top tier (100+) for the geography's records, its reader-facing records and its material outside the peak decade, and the third tier (25+) for material outside the top institution; RELAXED steps each down one tier. A *substantive* decade is the second tier (5+).
- **Continuity** is the cohort's own distribution: STRICT = the 90th percentile (6 substantive decades, a run of 4 — p90 is 6.0 and 3.6); RELAXED = above the 75th percentile (3 and 2 — p75 is 2 and 2).
- **Single-period concentration** fails only when the peak decade holds more than the gate's share *and* the remainder is below the volume floor: a geography whose remainder is itself a top-tier body of material is not 'one decade', however large that decade is (the United Kingdom's 1980s is the case).
- **Source concentration** requires a second institution with tier-level material (25+ STRICT, 5+ RELAXED) rather than a share ceiling, because a share ceiling would fail the two largest continuous series (the United Kingdom at 92.8% V&A, Norway at 92.9% National Library) while passing two-record geographies split one-and-one. The share is disclosed as a flag (`SOURCE_DOMINANT_75`) for the Data quality fold instead.
- **Date quality**: 90% year-or-finer (STRICT) / 80% (RELAXED); the cohort's 10th percentile is 100%, so the gate only catches the tail (Switzerland 87.5, Poland 89.9, Spain 80.0, Egypt 66.7).
- **Mapped** is required by both gates: a Research Region needs a map locator.

Reason codes: `NOT_MAPPED` — no safe map position in the governed registry (aggregate-only or unmapped); `LOW_TOTAL_VOLUME` — fewer public records than the gate's volume floor; `INSUFFICIENT_TEMPORAL_CONTINUITY` — too few substantive decades, or no long enough consecutive run of them; `SINGLE_PERIOD_CONCENTRATION` — one decade holds more than the gate's share and the remainder is below the volume floor; `SOURCE_CONCENTRATION` — a single institution, or too little material from any other institution; `DATE_QUALITY_INSUFFICIENT` — too small a share of records dated to a year or finer; `INSUFFICIENT_READER_FACING_RECORDS` — too few records with a human-readable title (reader-eligibility census). Disclosure flags (never a decision): `SOURCE_DOMINANT_75` (one institution ≥ 75%), `PEAK_DECADE_HALF` (one decade ≥ 50%), `READER_FACING_MINORITY` (reader-facing < 50%), `COMPOSITE_GOVERNED_IDENTITY` (a governed transnational or broad-region identity).

## 6 · Decisions: 8 OPEN · 7 REVIEW · 78 NOT_READY

### 6.1 · STRICT candidates (OPEN) — proposed first release

| Place | Records | Active decades | Substantive decades (≥5) | Longest substantive run | Median / active decade | Peak decade (share) | Institutions (top share) | Year-or-finer | Reader-facing | Range | Decision | Reason codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| United Kingdom | 3,214 | 22 | 21 | 20 | 57.0 | 1980s (50.1%) | 6 (92.8% collections.vam.ac.uk) | 93.7% | 976 (30.4%) | 1800s–2010s | OPEN | OPEN |
| United States | 1,175 | 17 | 14 | 14 | 37 | 2000s (23.3%) | 6 (39.6% www.loc.gov) | 95.3% | 1,118 (95.1%) | 1860s–2020s | OPEN | OPEN |
| Norway | 562 | 15 | 13 | 13 | 35 | 1990s (17.4%) | 5 (92.9% api.nb.no) | 100.0% | 562 (100.0%) | 1850s–2010s | OPEN | OPEN |
| Germany | 427 | 16 | 11 | 10 | 7.0 | 1960s (33.5%) | 6 (55.5% www.loc.gov) | 96.3% | 313 (73.3%) | 1860s–2010s | OPEN | OPEN |
| Russia | 231 | 9 | 7 | 7 | 11 | 1960s (36.8%) | 5 (69.3% www.loc.gov) | 98.7% | 200 (86.6%) | 1910s–1990s | OPEN | OPEN |
| France | 224 | 15 | 9 | 4 | 5 | 1960s (32.1%) | 6 (55.8% www.loc.gov) | 95.1% | 193 (86.2%) | 1870s–2010s | OPEN | OPEN |
| Italy | 128 | 11 | 6 | 6 | 5 | 1960s (42.2%) | 4 (69.5% www.loc.gov) | 96.1% | 106 (82.8%) | 1890s–2010s | OPEN | OPEN |
| Japan | 116 | 9 | 7 | 6 | 14 | 1960s (23.3%) | 4 (34.5% collections.vam.ac.uk) | 95.7% | 105 (90.5%) | 1930s–2010s | OPEN | OPEN |

- **United Kingdom** — 1800s 7 · 1810s 2 · 1820s 8 · 1830s 16 · 1840s 25 · 1850s 48 · 1860s 77 · 1870s 58 · 1880s 37 · 1890s 96 · 1900s 111 · 1910s 101 · 1920s 145 · 1930s 47 · 1940s 56 · 1950s 233 · 1960s 154 · 1970s 19 · 1980s 1630 · 1990s 157 · 2000s 198 · 2010s 26. Flags: SOURCE_DOMINANT_75, PEAK_DECADE_HALF, READER_FACING_MINORITY.
- **United States** — 1860s 2 · 1870s 1 · 1880s 1 · 1890s 21 · 1900s 11 · 1910s 37 · 1920s 21 · 1930s 56 · 1940s 40 · 1950s 23 · 1960s 157 · 1970s 226 · 1980s 49 · 1990s 129 · 2000s 274 · 2010s 119 · 2020s 9.
- **Norway** — 1850s 1 · 1880s 3 · 1890s 9 · 1900s 16 · 1910s 23 · 1920s 41 · 1930s 58 · 1940s 46 · 1950s 35 · 1960s 54 · 1970s 52 · 1980s 83 · 1990s 98 · 2000s 28 · 2010s 15. Flags: SOURCE_DOMINANT_75.
- **Germany** — 1860s 1 · 1870s 1 · 1880s 2 · 1890s 5 · 1900s 6 · 1910s 6 · 1920s 8 · 1930s 22 · 1940s 52 · 1950s 25 · 1960s 144 · 1970s 118 · 1980s 21 · 1990s 3 · 2000s 3 · 2010s 13.
- **Russia** — 1910s 4 · 1920s 5 · 1930s 11 · 1940s 34 · 1950s 10 · 1960s 85 · 1970s 60 · 1980s 18 · 1990s 4.
- **France** — 1870s 2 · 1880s 5 · 1890s 51 · 1900s 15 · 1910s 4 · 1920s 5 · 1930s 14 · 1940s 2 · 1950s 5 · 1960s 72 · 1970s 33 · 1980s 9 · 1990s 2 · 2000s 3 · 2010s 2.
- **Italy** — 1890s 1 · 1900s 2 · 1920s 2 · 1930s 7 · 1940s 5 · 1950s 5 · 1960s 54 · 1970s 41 · 1980s 7 · 2000s 2 · 2010s 2.
- **Japan** — 1930s 6 · 1940s 2 · 1950s 3 · 1960s 27 · 1970s 14 · 1980s 19 · 1990s 6 · 2000s 24 · 2010s 15.

### 6.2 · Near misses (REVIEW) — pass RELAXED, fail STRICT

| Place | Records | Active decades | Substantive decades (≥5) | Longest substantive run | Median / active decade | Peak decade (share) | Institutions (top share) | Year-or-finer | Reader-facing | Range | Decision | Reason codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Netherlands | 164 | 12 | 6 | 3 | 5.5 | 2010s (40.9%) | 3 (62.2% www.artic.edu) | 98.2% | 157 (95.7%) | 1890s–2020s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY |
| China / Hong Kong | 163 | 7 | 3 | 2 | 3 | 1970s (75.5%) | 3 (93.3% www.loc.gov) | 96.9% | 158 (96.9%) | 1910s–2000s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION |
| Chile | 129 | 6 | 4 | 2 | 5.5 | 1970s (65.9%) | 2 (51.9% www.bibliotecanacionaldigital.gob.cl) | 100.0% | 129 (100.0%) | 1960s–2010s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION |
| Poland | 99 | 11 | 6 | 3 | 7 | 1960s (28.3%) | 5 (73.7% collections.vam.ac.uk) | 89.9% | 77 (77.8%) | 1910s–2020s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, DATE_QUALITY_INSUFFICIENT, INSUFFICIENT_READER_FACING_RECORDS |
| Switzerland | 96 | 10 | 7 | 6 | 8.0 | 1960s (25.0%) | 4 (56.2% www.loc.gov) | 87.5% | 91 (94.8%) | 1900s–2000s | REVIEW | LOW_TOTAL_VOLUME, DATE_QUALITY_INSUFFICIENT, INSUFFICIENT_READER_FACING_RECORDS |
| Malaysia | 52 | 8 | 3 | 2 | 4.0 | 2020s (51.9%) | 2 (90.4% search.malaysiadesignarchive.org) | 96.2% | 52 (100.0%) | 1930s–2020s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| South Africa | 36 | 3 | 3 | 2 | 11 | 1960s (55.6%) | 3 (69.4% www.loc.gov) | 100.0% | 35 (97.2%) | 1960s–2000s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |

- **Netherlands** — 1890s 3 · 1900s 1 · 1920s 8 · 1930s 4 · 1940s 1 · 1950s 1 · 1960s 44 · 1970s 11 · 1990s 1 · 2000s 7 · 2010s 67 · 2020s 16.
- **China / Hong Kong** — 1910s 1 · 1920s 3 · 1930s 3 · 1950s 3 · 1960s 25 · 1970s 123 · 2000s 5. Flags: SOURCE_DOMINANT_75, PEAK_DECADE_HALF, COMPOSITE_GOVERNED_IDENTITY.
- **Chile** — 1960s 28 · 1970s 85 · 1980s 4 · 1990s 6 · 2000s 5 · 2010s 1. Flags: PEAK_DECADE_HALF.
- **Poland** — 1910s 2 · 1920s 1 · 1930s 10 · 1950s 8 · 1960s 28 · 1970s 28 · 1980s 3 · 1990s 1 · 2000s 2 · 2010s 7 · 2020s 9.
- **Switzerland** — 1900s 1 · 1920s 6 · 1930s 13 · 1940s 11 · 1950s 10 · 1960s 24 · 1970s 21 · 1980s 3 · 1990s 5 · 2000s 2.
- **Malaysia** — 1930s 2 · 1950s 6 · 1960s 7 · 1970s 4 · 1980s 1 · 1990s 4 · 2010s 1 · 2020s 27. Flags: SOURCE_DOMINANT_75, PEAK_DECADE_HALF.
- **South Africa** — 1960s 20 · 1970s 5 · 2000s 11. Flags: PEAK_DECADE_HALF.

### 6.3 · NOT_READY — by reason code (a geography can carry several)

| Reason code | Geographies |
| --- | --- |
| INSUFFICIENT_TEMPORAL_CONTINUITY | 75 |
| SOURCE_CONCENTRATION | 71 |
| INSUFFICIENT_READER_FACING_RECORDS | 63 |
| LOW_TOTAL_VOLUME | 62 |
| SINGLE_PERIOD_CONCENTRATION | 38 |
| NOT_MAPPED | 12 |
| DATE_QUALITY_INSUFFICIENT | 1 |

### 6.4 · All 93 geographies

| Place | State | Records | Active | Subst. (≥5) | Run | Median | Peak % | Inst. | Top inst. % | Year+ % | Reader-facing | Range | Decision | Reason codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| United Kingdom | mapped | 3,214 | 22 | 21 | 20 | 57.0 | 50.1 | 6 | 92.8 | 93.7 | 976 | 1800s–2010s | OPEN | OPEN |
| United States | mapped | 1,175 | 17 | 14 | 14 | 37 | 23.3 | 6 | 39.6 | 95.3 | 1,118 | 1860s–2020s | OPEN | OPEN |
| Norway | mapped | 562 | 15 | 13 | 13 | 35 | 17.4 | 5 | 92.9 | 100.0 | 562 | 1850s–2010s | OPEN | OPEN |
| Germany | mapped | 427 | 16 | 11 | 10 | 7.0 | 33.5 | 6 | 55.5 | 96.3 | 313 | 1860s–2010s | OPEN | OPEN |
| Russia | mapped | 231 | 9 | 7 | 7 | 11 | 36.8 | 5 | 69.3 | 98.7 | 200 | 1910s–1990s | OPEN | OPEN |
| France | mapped | 224 | 15 | 9 | 4 | 5 | 32.1 | 6 | 55.8 | 95.1 | 193 | 1870s–2010s | OPEN | OPEN |
| Netherlands | mapped | 164 | 12 | 6 | 3 | 5.5 | 40.9 | 3 | 62.2 | 98.2 | 157 | 1890s–2020s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY |
| China / Hong Kong | mapped | 163 | 7 | 3 | 2 | 3 | 75.5 | 3 | 93.3 | 96.9 | 158 | 1910s–2000s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION |
| Chile | mapped | 129 | 6 | 4 | 2 | 5.5 | 65.9 | 2 | 51.9 | 100.0 | 129 | 1960s–2010s | REVIEW | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION |
| Italy | mapped | 128 | 11 | 6 | 6 | 5 | 42.2 | 4 | 69.5 | 96.1 | 106 | 1890s–2010s | OPEN | OPEN |
| Japan | mapped | 116 | 9 | 7 | 6 | 14 | 23.3 | 4 | 34.5 | 95.7 | 105 | 1930s–2010s | OPEN | OPEN |
| Poland | mapped | 99 | 11 | 6 | 3 | 7 | 28.3 | 5 | 73.7 | 89.9 | 77 | 1910s–2020s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, DATE_QUALITY_INSUFFICIENT, INSUFFICIENT_READER_FACING_RECORDS |
| Global / transnational | aggregate_only | 97 | 5 | 2 | 2 | 4 | 53.6 | 1 | 100.0 | 100.0 | 97 | 1910s–1980s | NOT_READY | NOT_MAPPED, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION |
| Switzerland | mapped | 96 | 10 | 7 | 6 | 8.0 | 25.0 | 4 | 56.2 | 87.5 | 91 | 1900s–2000s | REVIEW | LOW_TOTAL_VOLUME, DATE_QUALITY_INSUFFICIENT, INSUFFICIENT_READER_FACING_RECORDS |
| Indonesia | mapped | 79 | 7 | 4 | 3 | 10 | 36.7 | 3 | 96.2 | 100.0 | 78 | 1930s–2010s | NOT_READY | SOURCE_CONCENTRATION |
| Austria | mapped | 77 | 6 | 3 | 3 | 6.0 | 63.6 | 2 | 98.7 | 100.0 | 77 | 1920s–2000s | NOT_READY | SOURCE_CONCENTRATION |
| Cuba / transnational | aggregate_only | 76 | 3 | 2 | 2 | 27 | 63.2 | 3 | 86.8 | 100.0 | 74 | 1960s–1980s | NOT_READY | NOT_MAPPED, INSUFFICIENT_TEMPORAL_CONTINUITY |
| Belgium | mapped | 59 | 11 | 2 | 1 | 3 | 33.9 | 4 | 44.1 | 94.9 | 48 | 1840s–2010s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY |
| Finland | mapped | 59 | 4 | 2 | 2 | 8.5 | 69.5 | 1 | 100.0 | 100.0 | 59 | 1940s–1970s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION |
| Sweden | mapped | 58 | 6 | 2 | 2 | 1.5 | 75.9 | 3 | 87.9 | 100.0 | 58 | 1890s–1990s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION |
| Denmark | mapped | 55 | 6 | 2 | 2 | 1.0 | 74.5 | 3 | 94.5 | 100.0 | 55 | 1890s–2000s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION |
| Malaysia | mapped | 52 | 8 | 3 | 2 | 4.0 | 51.9 | 2 | 90.4 | 96.2 | 52 | 1930s–2020s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Ireland | mapped | 43 | 3 | 2 | 2 | 13 | 67.4 | 2 | 97.7 | 100.0 | 42 | 1960s–2010s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION |
| Wallis and Futuna | mapped | 37 | 3 | 2 | 2 | 6 | 75.7 | 1 | 100.0 | 100.0 | 37 | 2000s–2020s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION |
| Portugal | mapped | 36 | 2 | 2 | 2 | 18.0 | 80.6 | 1 | 100.0 | 100.0 | 36 | 1960s–1970s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION |
| South Africa | mapped | 36 | 3 | 3 | 2 | 11 | 55.6 | 3 | 69.4 | 100.0 | 35 | 1960s–2000s | REVIEW | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Canada | mapped | 32 | 7 | 3 | 1 | 2 | 34.4 | 3 | 50.0 | 100.0 | 32 | 1910s–2010s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY |
| Israel / Palestine | mapped | 31 | 3 | 2 | 2 | 10 | 58.1 | 1 | 100.0 | 100.0 | 31 | 1940s–1970s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION |
| Turkey | mapped | 30 | 3 | 1 | 1 | 1 | 93.3 | 3 | 93.3 | 100.0 | 30 | 1920s–2020s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION |
| Mexico | mapped | 29 | 10 | 2 | 2 | 1.0 | 34.5 | 4 | 82.8 | 96.6 | 29 | 1890s–2010s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY |
| Aotearoa New Zealand | mapped | 25 | 3 | 1 | 1 | 4 | 80.0 | 2 | 96.0 | 100.0 | 24 | 1960s–1980s | NOT_READY | INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Vietnam | mapped | 23 | 2 | 2 | 2 | 11.5 | 52.2 | 2 | 91.3 | 91.3 | 23 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Federated States of Micronesia | mapped | 22 | 3 | 3 | 3 | 8 | 36.4 | 1 | 100.0 | 100.0 | 22 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Romania | mapped | 18 | 2 | 2 | 2 | 9.0 | 61.1 | 2 | 55.6 | 100.0 | 8 | 1950s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, INSUFFICIENT_READER_FACING_RECORDS |
| Vanuatu | mapped | 18 | 3 | 2 | 2 | 6 | 61.1 | 1 | 100.0 | 100.0 | 18 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| India | mapped | 14 | 1 | 1 | 1 | 14 | 100.0 | 2 | 92.9 | 100.0 | 14 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Australia | mapped | 13 | 3 | 1 | 1 | 2 | 76.9 | 2 | 92.3 | 100.0 | 13 | 1960s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Korean Peninsula | mapped | 13 | 4 | 1 | 1 | 2.5 | 53.8 | 3 | 76.9 | 100.0 | 13 | 1940s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Solomon Islands | mapped | 13 | 3 | 1 | 1 | 4 | 61.5 | 1 | 100.0 | 100.0 | 13 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Cook Islands | mapped | 12 | 3 | 1 | 1 | 4 | 41.7 | 1 | 100.0 | 100.0 | 12 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Hungary | mapped | 12 | 3 | 1 | 1 | 2 | 75.0 | 2 | 91.7 | 100.0 | 12 | 1960s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Ghana | mapped | 11 | 1 | 1 | 1 | 11 | 100.0 | 1 | 100.0 | 100.0 | 11 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Spain | mapped | 10 | 3 | 1 | 1 | 3 | 50.0 | 3 | 50.0 | 80.0 | 10 | 1890s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, INSUFFICIENT_READER_FACING_RECORDS |
| Ukraine | mapped | 10 | 3 | 1 | 1 | 1 | 80.0 | 2 | 80.0 | 100.0 | 10 | 1920s–1990s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Brazil | mapped | 9 | 7 | 0 | 0 | 1 | 22.2 | 3 | 55.6 | 100.0 | 7 | 1880s–2010s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| New Caledonia | mapped | 9 | 2 | 1 | 1 | 4.5 | 77.8 | 1 | 100.0 | 100.0 | 9 | 2010s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Czech Republic | mapped | 8 | 4 | 0 | 0 | 1.5 | 50.0 | 3 | 62.5 | 100.0 | 8 | 1910s–1990s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Kiribati | mapped | 8 | 3 | 1 | 1 | 2 | 62.5 | 1 | 100.0 | 100.0 | 8 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Palestine / transnational | aggregate_only | 8 | 4 | 0 | 0 | 1.5 | 50.0 | 1 | 100.0 | 100.0 | 8 | 1930s–1980s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Samoa | mapped | 8 | 2 | 1 | 1 | 4.0 | 87.5 | 1 | 100.0 | 100.0 | 8 | 2000s–2010s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Tonga | mapped | 7 | 2 | 1 | 1 | 3.5 | 71.4 | 1 | 100.0 | 100.0 | 7 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Argentina | mapped | 6 | 4 | 0 | 0 | 1.0 | 50.0 | 2 | 50.0 | 100.0 | 6 | 1960s–1990s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Fiji | mapped | 6 | 2 | 0 | 0 | 3.0 | 66.7 | 1 | 100.0 | 100.0 | 6 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Iran | mapped | 6 | 2 | 0 | 0 | 3.0 | 66.7 | 1 | 100.0 | 100.0 | 6 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Nauru | mapped | 6 | 2 | 0 | 0 | 3.0 | 50.0 | 1 | 100.0 | 100.0 | 6 | 2000s–2020s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Thailand | mapped | 6 | 2 | 1 | 1 | 3.0 | 83.3 | 2 | 83.3 | 100.0 | 6 | 1960s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Zimbabwe | mapped | 6 | 2 | 0 | 0 | 3.0 | 66.7 | 1 | 100.0 | 100.0 | 6 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Greece | mapped | 5 | 3 | 0 | 0 | 1 | 60.0 | 2 | 80.0 | 100.0 | 5 | 1960s–1990s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Marshall Islands | mapped | 5 | 2 | 0 | 0 | 2.5 | 60.0 | 1 | 100.0 | 100.0 | 5 | 2000s–2010s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Paris, France | aggregate_only | 5 | 2 | 0 | 0 | 2.5 | 60.0 | 1 | 100.0 | 100.0 | 5 | 1800s–1810s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Niue | mapped | 4 | 2 | 0 | 0 | 2.0 | 75.0 | 1 | 100.0 | 100.0 | 4 | 2000s–2010s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Palau | mapped | 4 | 2 | 0 | 0 | 2.0 | 75.0 | 1 | 100.0 | 100.0 | 4 | 2000s–2010s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Paraguay | mapped | 4 | 1 | 0 | 0 | 4 | 100.0 | 1 | 100.0 | 100.0 | 4 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Egypt | mapped | 3 | 3 | 0 | 0 | 1 | 33.3 | 2 | 66.7 | 66.7 | 3 | 1940s–1980s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, DATE_QUALITY_INSUFFICIENT, INSUFFICIENT_READER_FACING_RECORDS |
| Guatemala | mapped | 3 | 2 | 0 | 0 | 1.5 | 66.7 | 1 | 100.0 | 100.0 | 3 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Iraq | mapped | 3 | 1 | 0 | 0 | 3 | 100.0 | 1 | 100.0 | 100.0 | 3 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Lebanon | mapped | 3 | 2 | 0 | 0 | 1.5 | 66.7 | 1 | 100.0 | 100.0 | 3 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Nicaragua | mapped | 3 | 2 | 0 | 0 | 1.5 | 66.7 | 1 | 100.0 | 100.0 | 3 | 1960s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Nigeria | mapped | 3 | 1 | 0 | 0 | 3 | 100.0 | 1 | 100.0 | 100.0 | 3 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Boston, United States | aggregate_only | 2 | 1 | 0 | 0 | 2 | 100.0 | 1 | 100.0 | 100.0 | 2 | 1810s–1810s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Dominican Republic | mapped | 2 | 1 | 0 | 0 | 2 | 100.0 | 1 | 100.0 | 100.0 | 2 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Georgia | mapped | 2 | 1 | 0 | 0 | 2 | 100.0 | 1 | 100.0 | 100.0 | 2 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Papua New Guinea | mapped | 2 | 1 | 0 | 0 | 2 | 100.0 | 1 | 100.0 | 100.0 | 2 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Tuvalu | mapped | 2 | 1 | 0 | 0 | 2 | 100.0 | 1 | 100.0 | 100.0 | 2 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Uruguay | mapped | 2 | 2 | 0 | 0 | 1.0 | 50.0 | 1 | 100.0 | 100.0 | 2 | 1940s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Angers, France | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1800s–1800s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Australia / Indigenous | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1910s–1910s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Bangladesh | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Bordeaux, France | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1820s–1820s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| El Salvador | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Estonia | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1990s–1990s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Hawaii | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 2010s–2010s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Jordan | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| New York, United States | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1800s–1800s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Pakistan | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Peru | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Port-au-Prince, Haiti | aggregate_only | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1820s–1820s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Puerto Rico | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 2000s–2000s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Serbia | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Singapore | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1950s–1950s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Syria | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1960s–1960s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Tokelau | unmapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 2000s–2000s | NOT_READY | NOT_MAPPED, LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |
| Venezuela | mapped | 1 | 1 | 0 | 0 | 1 | 100.0 | 1 | 100.0 | 100.0 | 1 | 1970s–1970s | NOT_READY | LOW_TOTAL_VOLUME, INSUFFICIENT_TEMPORAL_CONTINUITY, SINGLE_PERIOD_CONCENTRATION, SOURCE_CONCENTRATION, INSUFFICIENT_READER_FACING_RECORDS |

## 7 · Findings the product must state

- The United Kingdom's 1980s (1,630 of the decade's 1,898 public records) is 1,629 V&A records and one Nasjonalmuseet record; 92.8% of the United Kingdom's 3,214 records are V&A, and only 976 (30.4%) carry a human-readable title (the V&A titles are mostly source identifiers). It still passes STRICT — 21 substantive decades, 230 records from five other institutions — but the Data quality fold must say so.
- Norway is a single-institution series in effect (92.9% National Library of Norway) with 40 records from four others; China / Hong Kong is 93.3% Library of Congress with 75.5% of its material in one decade; Indonesia (96.2%), Austria (98.7%), Finland, Portugal and the Pacific territories (100%) are single-institution captures in effect.
- Under STRICT the open set is exactly the geographies that are continuous, multi-institution and large: six in Europe, the United States and Japan. Nothing in the Pacific, Africa, the Middle East, South Asia, Southeast Asia or Latin America clears it; under RELAXED only China / Hong Kong, Chile, Malaysia and South Africa do outside Europe and North America. That is the archive's present coverage, not a curatorial choice, and the public statement should say it.
- Aggregate-only identities with research-scale material — Global / transnational (97), Cuba / transnational (76) — are excluded only by `NOT_MAPPED`; a later governance round could give transnational identities a non-map research surface.

## 8 · What this round does not do

- It does not change `gis/*`, the governed readers, the read APIs, the projection, the period membership or the count tiers.
- It does not hard-code the shortlist into the UI: the registry is `CANDIDATE_PENDING_OWNER_APPROVAL`.
- It does not compose macro-regions and does not rename or hold any geography.

## 9 · Proposed public Spacetime scope (for review, not built)

Entry: **RESEARCH REGIONS** — the approved set as cards (name · substantive decades · public records · research range first–last substantive decade · a one-line source statement), plus the boundary sentence: *We do not expose a geography merely because a record can be plotted. Spacetime opens a place for research only when the current archive contains sufficient temporal and evidentiary coverage.* Selecting a region opens five blocks: 01 Research region (name, Change), 02 Time (the decade rail limited to the region's substantive range, previous → current → next with counts), 03 Map (one primary visualization: the region's locator with the three-bar temporal glyph; Density / Texture under View options; the world atlas as an optional Overview mode, not the entry), 04 Place profile (records · share of period · rank; the three-decade ledger; Data quality fold holding mapping state, precision mix, institution mix, reader-facing share, flags), 05 Records (matching records). System suggests reads the region's own change only.


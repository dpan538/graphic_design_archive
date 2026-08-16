# A4 — Corpus Scope, Missingness, and Growth Decision

**Status:** complete; read-only research assessment  
**Date:** 2026-08-16 (Australia/Brisbane)  
**Question:** whether the 20,000-object target adds research value, and what corpus-quality work should take priority.

## Decision in brief

**Do not run a volume-expansion programme in the two-week window.** Keep the 15,923-object operational frame, publish its boundaries and its held/unknown states, and spend the available effort on a source-family registry, faceted missingness baseline, and a small, auditable evidence-cleaning pilot. `TARGET_20000_IS_ACCEPTANCE_GATE=false` is the correct policy result, not a temporary shortfall.

Object count is a measure of ingest throughput and possible discovery breadth; it is neither a measure of representativeness nor of scholarly/TRACE readiness. Digitization selection can reproduce archival silences and remove awareness of context, so a larger digitized aggregate cannot by itself repair the bias of its acquisition and digitization paths [S1]. Comparative work on museum online databases likewise finds different geographic biases across interfaces/API outputs drawn from the same institutions [S2]. The project must consequently make its population frame and omissions visible before treating growth as improvement.

## 1. Baseline: what the counts do and do not establish

| Measure | Count | Rate of 15,923 | Defensible reading | It does **not** establish |
|---|---:|---:|---|---|
| Operational archive objects | 15,923 | 100.00% | Every frozen input surface is accounted once. | Unique intellectual works, a random sample, global coverage, or representative design history. |
| Research-eligible objects | 7,995 | 50.21% | Rows explicitly marked `source_verified` meet the current minimal descriptive-research gate. | A semantic claim, relation, image right, or a balanced corpus. |
| Held objects | 7,928 | 49.79% | 2,971 `metadata_supported` and 4,957 absent/blank evidence-tier rows are intentionally not promoted. | Rejection, low cultural value, or non-existence. |
| TRACE-eligible objects | 0 | 0.00% | No object has an accepted registered semantic relation/claim path. | That no historical relationships exist. |
| Positive visual-rights coverage | 0% | 0.00% | No claim of positively-cleared visual coverage is available. | Permission to reuse, cache, or imply endorsement from linked images. |

The local, release-pinned migration evidence is exact about the row counts and fail-closed rules: all 15,923 objects are held from TRACE; 9,393 rows have edge-ID/label arrays that cannot safely be zipped; the legacy graph is therefore not relationship evidence [S6]. The split also makes “15,923 objects” a **Browse-frame statistic**, not a strict research-corpus statistic. The 7,995/7,928 division is a useful quality baseline precisely because it prevents a historical derived fallback from silently converting the 4,957 unknown-tier rows into evidence-bearing material [S6].

## 2. Statistical and research interpretation

### Population frame, not sample

The project has a deterministic frame of source surfaces, not a probability sample of modern graphic design. Without a named reference universe, collection policy, inclusion/exclusion log, and coverage measurement, it cannot estimate population prevalence or call itself representative. `N=15,923` lowers neither selection bias nor source dependence. Digital-history scholarship stresses that archive appraisal and subsequent microfilming/digitization select what is kept and visible; those selections can reproduce dominant narratives and silences [S1].

The appropriate claim is: *“a release-pinned index of 15,923 operational source surfaces, with a 7,995-row source-verified descriptive-research subset.”* The inappropriate claim is: *“a comprehensive/representative archive of modern graphic design.”*

### Evidence coverage is the binding constraint

The strict research-evidence coverage is only **50.21%**, while **31.13%** of all rows have an absent/blank evidence tier and **18.66%** are metadata-supported but below the current threshold. The immediate opportunity is not another 4,077 objects to reach a round number: it is converting a documented, reviewed subset of the 7,928 held objects when row-level authority warrants it. A target of 20,000 can raise the browse count while reducing the verified proportion.

TRACE is a separate, stricter constraint: **0 / 15,923** eligible objects. It follows that no aggregate count can make TRACE research-ready until governed claim/evidence/relation records exist. Growth in objects and growth in relations must remain different workstreams.

### Missingness must be a research result, not a null hidden by UI

Archives and their digital surrogates are purposefully incomplete representations; finding aids and selection choices need contextual interpretation [S3]. The project should therefore display *unknown/not collected*, *held for insufficient evidence*, *not digitized/not visually reusable*, and *out of-scope* as different states. It must never render an empty region, year, medium, image field, or relation field as evidence of absence. Europeana's production guidance similarly treats metadata/content quality, rights, and contextual data as independently consequential for discovery and reuse [S4].

## 3. Growth decision framework

### Two-week disposition

| Workstream | Decision | Gate / output |
|---|---|---|
| Broad, untargeted acquisition toward 20,000 | **STOP** | No new collection-wide target; do not ingest merely to increase `N`. |
| Semantic relations / old v48 graph | **STOP** | Keep `TRACE_ELIGIBLE_OBJECTS=0`; no positional repair, split/zip, or historical assertion. |
| Evidence-tier cleaning | **GO, narrow** | Pilot a bounded, logged sample of held rows; each promotion requires row-level primary/authoritative source and reviewer decision. |
| Source-family normalization | **GO, P0** | Create a governed registry before measuring concentration; do not infer provider from URL host/prefix. |
| Coverage/missingness dashboard or release table | **GO, P0** | Publish faceted denominator, unknown rate, and provenance/release version for every advertised coverage figure. |
| Targeted acquisition after baseline | **CONDITIONAL** | Add only to correct a predeclared, measured gap and only if the candidate can satisfy evidence/rights/provenance intake gates. |

### Required metrics before any new volume target

No numeric target should be approved until the following table has a frozen denominator, explicit `UNKNOWN` state, source registry, and release comparison. These are monitoring and decision metrics, **not** claims of demographic or historical representativeness.

| Dimension | Measure | Continue targeted acquisition when | Stop / clean first when |
|---|---|---|---|
| Evidence tier | `source_verified / all`, `unknown-tier / all`, reason-coded held rate | A documented underserved stratum has an authoritative source path and each intake improves its verified coverage. | Any collection-wide intake adds unknown-tier or metadata-only rows faster than verified rows; immediately if promotion is based on derived/catalog presence. |
| Source family / provider | share of operational and research subset by governed source family; top-1/top-3 concentration; `UNKNOWN provider` | A new independently governed family reduces measured concentration or fills a declared scope gap. | Provider identity is unnormalized/unknown, or growth extends the already-dominant family without a gap rationale. |
| Region / place authority | counts and unknown rate by *asserted* place authority and by source-family cross-tab | A named geographic gap is documented against the project’s stated scope and has contextual primary records. | Place is inferred from URL/language/designer nationality, or an empty bin is presented as historical absence. |
| Era / date precision | counts by declared date bins plus `unknown`, `range`, and precision class | A predeclared period is sparse **after** date-precision disclosure and quality intake is available. | Dates are coerced to a single year, unknowns are dropped, or a new source shifts the period distribution without explanation. |
| Medium/object type | counts, unknown rate, controlled-term mapping rate by medium/type | A neglected medium is added with source provenance and mapped vocabulary. | Labels are free-text/mixed without mapping, or the apparent gap is a vocabulary artifact. |
| Institution / custody | source institution and collecting-context coverage; institution unknown rate | A different custody/collecting context broadens documented provenance. | More material comes from the same institutional lineage while its share is unreported. |
| Rights / visual federation | positive rights statement rate, resolvable source-link rate, provider-policy class | A provider supplies explicit statement/policy and stable attribution path. | A visual is treated as reusable because it is publicly linked, hotlinkable, or discoverable. |
| TRACE evidence | accepted claims/relations with source-root and review status; contested/held counts | A small release-pinned relation set passes evidence and review gates. | Any proposed relation rests on similarity, co-time, co-place, medium, or opaque legacy layout alone. |

**Suggested release gates (not quotas):** (1) 100% of advertised faceted counts have denominators and `UNKNOWN`; (2) 100% of source-family and custody claims resolve through a governed registry; (3) every targeted intake carries source, date/precision, object-type and rights/provenance disposition or is visibly held; (4) an independent stratified manual audit of the new/cleaned batch logs its error and reversal rate; (5) no release reports a geographic/period “gap” without distinguishing *not collected*, *not described*, and *absent from this frame*. EU data-quality guidance makes completeness measurable as empty-field rate and connects complete metadata to human and machine findability [S5]; use that measurement discipline, but do not mistake field completeness for historical truth.

### Quantified, staged next decision

1. **First, baseline (Days 1–3):** normalize source family/institution and produce 2-way tables for research eligibility × region, era, medium, source family, and custody, retaining unknowns. Current values for those distributions are **UNKNOWN**, not zero, because a governed source registry does not yet exist [S6].
2. **Then, cleaning pilot (Days 4–7):** choose a documented stratified subset of the 4,957 unknown-tier and 2,971 metadata-supported rows; publish attempted, verified, held, rejected, and reviewer-reversed counts by stratum. Do not extrapolate the pilot rate to the corpus.
3. **Only then, conditional intake:** authorize a small batch only when it names the gap, provenance family, expected metadata/rights level, and expected effect on a published metric. If it fails gates, retain or reject it visibly; do not lower the evidence threshold to preserve a count target.
4. **Reassess at release candidate:** prioritize evidence coverage and diversity of independently governed source families over total N. A 16,000-object corpus with a transparent 70% verified coverage and documented source breadth would be a stronger research release than a 20,000-object corpus whose additional objects are predominantly unknown-tier from the same source lineage. This comparison is a policy example, not a forecast.

## 4. What 20,000 could mean—and cannot mean

There can be practical value in added objects: more discovery entry points, preservation of source links, and targeted coverage of a genuinely documented gap. It is an **infrastructure/product capacity outcome**. It becomes a research outcome only when the acquisition design records why a stratum was selected, what universe/scope it is compared with, the source/custody constraints, and how the new records improve usable evidence rather than merely volume.

Therefore:

- retain `TARGET_20000_IS_ACCEPTANCE_GATE=false` permanently for this release;
- do not set 20,000 as a launch, funding, academic, or TRACE-acceptance criterion;
- if a later public target is needed, express it as a quality target (for example, “all released records have a source-family, date precision, rights/provenance state and missingness label”) rather than a raw-object target;
- do not promise universal/global coverage or balance merely because source counts span multiple locations.

## 5. Implications for TRACE and public positioning

The present corpus can honestly support **Global Atlas / coverage and missingness exploration** and source-bounded **research-tree membership** only if labels identify them as release-specific and non-causal. It cannot publicly support an influence map or object-relation trace: `TRACE_ELIGIBLE_OBJECTS=0` is an all-object hold. A `TRACE Preview` or `Evidence Trace (no accepted relations in this release)` is defensible only if the screen leads with its evidence boundary and shows claims/sources/provenance as unavailable rather than visualizing legacy edges.

This conservative position is a methodological asset: it makes an archive's data-quality and interpretive limits inspectable. It is not a substitute for relations, and it must not be advertised as an influence network. The zero relation result should redirect two-week work toward release metadata, missingness visibility, and a minimal evidence workflow—not toward synthetic graph density.

## 6. Risks and anti-patterns

- **Denominator laundering:** using 15,923, 7,995, Search, review, or a UI subset interchangeably. Every statistic must name its population.
- **Coverage theatre:** a filled map/timeline based on a source-concentrated or date-imputed frame reads as comprehensive. Use explicit unknown and source filters.
- **Category collapse:** “held,” “unavailable,” “not digitized,” “not reusable,” and “not historically present” are different propositions.
- **Intake-induced imbalance:** broad scraping/import can amplify the best-digitized institutions, English-language descriptions, particular media, or copyright-safe periods. The literature warns that collection/digitization bias can transit into datasets and platforms [S1, S2].
- **TRACE inflation:** graph positions, co-occurrence, or old display edges are not a reviewable semantic relation; zero accepted relations should remain zero.

## Source register

| ID | Title | Author / institution | Year | URL / DOI | Accessed | Source category | Specific support |
|---|---|---|---:|---|---|---|---|
| S1 | *Digital History and the Politics of Digitization* | Andreas Fickers & Juliane Tatarinov? **Author metadata requires verification; cited via publisher page** | 2023 | https://academic.oup.com/dsh/article/38/2/830/6702047 | 2026-08-16 | Peer-reviewed journal | Digitization and appraisal selection can reproduce silences/power relations; global digitization statistics are incomplete. Author field is deliberately marked uncertain rather than guessed. |
| S2 | *What do they make us see: a comparative study of cultural bias in online databases of two large museums* | Journal of Documentation / Emerald Publishing | 2022 | https://doi.org/10.1108/JD-02-2022-0047 | 2026-08-16 | Peer-reviewed journal | Online museum databases/API/Wikidata can differ in geographic bias; collection construction decisions create omissions. |
| S3 | *The Digital Black Atlantic* (chapter) | Jessica Marie Johnson, Mark V. Campbell & others / Debates in the Digital Humanities | 2021 | https://dhdebates.gc.cuny.edu/read/the-digital-black-atlantic/section/353b3dd5-c4dc-404b-bf68-07e65c40e03a | 2026-08-16 | Scholarly edited volume | Finding aids/digital archival descriptions are socially constructed and purposefully incomplete; users need context. |
| S4 | *Publishing Framework* | Europeana Foundation | 2026 (updated) | https://pro.europeana.eu/index.php/post/publishing-framework | 2026-08-16 | Official cultural-heritage framework | Separates quality of metadata/content, rights, and ability to surface/reuse; supports quality-tier rather than count-only framing. |
| S5 | *Data Quality Guidelines* | Publications Office of the European Union | 2021 | https://op.europa.eu/webpub/op/data-quality-guidelines/en/ | 2026-08-16 | Official data-quality guidance | Defines metadata completeness through empty fields and links detailed metadata to discoverability/reuse. |
| S6 | *v49 Missingness Baseline* and *Research Corpus Policy* | graphic_design_archive, release-pinned local audit | 2026 | `docs/audits/v49-authority-research-delta/11_MISSINGNESS_BASELINE.json`; `09_RESEARCH_CORPUS_POLICY.md` | 2026-08-16 | Primary project evidence | Exact 15,923/7,995/7,928/0 counts, held reasons, unmeasured source-family concentration, 9,393 unsafe edge arrays, and non-gate 20,000 policy. |

## Final recommendation

**CORPUS_GROWTH_RECOMMENDATION=STOP_UNTARGETED_GROWTH_CLEAN_AND_MEASURE_FIRST.**

Reopen acquisition only as a documented intervention against a measured provenance, regional, temporal, medium, institutional, or evidence-quality gap. Its success condition is a more inspectable and better-supported corpus—not `N=20,000`.

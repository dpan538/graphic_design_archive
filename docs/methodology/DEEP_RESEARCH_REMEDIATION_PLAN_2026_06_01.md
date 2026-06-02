# Deep Research Remediation Plan

Date: 2026-06-01

Status: active execution plan

This document converts the five latest Deep Research reports into a durable
implementation plan. It is intended to survive context compaction and coordinate
future capture, grouping, metrics, and publication-surface work.

Related review:

- `docs/research-reviews/DEEP_RESEARCH_2026_06_01_INTEGRATION_REVIEW_v0.md`

## Working Principle

The archive must stop treating capture volume as progress by itself. Progress now means:

1. broader and better-classified source coverage;
2. preserved source records with explicit provenance;
3. layered image evidence metrics;
4. stronger public-surface gates;
5. lower noise in contemporary capture.

No raw capture row should automatically become a main sheet. Public surfaces are generated
after source classification, evidence scoring, linkage/grouping, rights review, and surface
assignment.

## Problem 1: Source Breadth Is Too Narrow

Current risk:

- The project still leans too heavily on large Western/institutional APIs and a small set
  of repeatable sources.
- Source count alone is not meaningful unless source family, region, language, protocol,
  and rights posture are known.

Target:

- Build a `source_prospect_registry_v2` before the next large capture pass.
- Aim for roughly 200 classified candidate sources, but do not treat the raw number as
  success if the sources are weak repost/discovery pages.

Required fields:

- `source_prospect_id`
- `source_name`
- `source_url`
- `region_group`
- `subregion`
- `country_or_territory`
- `language_scripts`
- `source_family`
- `source_role`
- `protocol_hints`
- `rights_posture`
- `expected_image_path`
- `expected_text_path`
- `credibility_tier`
- `capture_priority`
- `known_limitations`
- `recommended_adapter`
- `seed_query_or_discovery_route`
- `last_checked`

Source families to cover:

- national library / public library / municipal archive;
- university repository / special collection;
- newspaper / magazine / OCR portal;
- OAI-PMH / IIIF / Omeka / CONTENTdm / DSpace / Kramerius / ArchivesSpace;
- community / activist / Indigenous / diaspora archive;
- film poster / festival / design school / studio archive;
- government cultural database;
- independent design archive or publication;
- web archive / born-digital preservation route;
- social or repost platform as discovery-only.

Execution steps:

1. Generate `data/source_prospect_registry_v2.csv`.
2. Add `docs/capture/SOURCE_PROSPECT_REGISTRY_v2.md`.
3. Probe candidates in small protocol-family batches.
4. Promote only repeatable, rights-readable sources into capture adapters.

Acceptance checks:

- At least 200 candidate sources classified, or a documented reason why the first pass
  stops lower.
- Non-Western and local/community/government/university sources are explicitly counted.
- Discovery-only sources are marked and cannot publish main sheets by themselves.

## Problem 2: Duplicate And Overlapping Records Are Not Yet Structured Enough

Current risk:

- Duplicate-looking records can appear as separate sheets and look like a bug.
- Collapsing them too aggressively would erase source provenance.

Target:

- Preserve every source record.
- Build a linkage candidate layer before public-surface generation.
- Merge navigationally, never evidentially.

Required output tables:

- `data/source_record_linkage_candidates_v1.csv`
- `data/source_record_group_memberships_v1.csv`

Required linkage relation labels:

- `same_entity_confirmed`
- `possibly_same_as`
- `same_work_different_manifestation`
- `same_visual_item_different_carrier`
- `digital_surrogate_of`
- `translation_of`
- `derived_from`
- `documents`
- `related_but_not_same`

Candidate signals:

- identical or near-identical source URL;
- shared local identifier, accession number, call number, issue number, shelfmark;
- repeated image URL or perceptual hash;
- same title plus close date/place/medium/source family;
- same publication title with issue-level variants;
- same campaign/studio/event/festival cluster;
- same visual composition across carrier or edition.

Execution steps:

1. Add a linkage candidate generator that reads current capture CSVs.
2. Keep `source_record_id` rows intact.
3. Generate candidate groups with relation type and confidence.
4. Do not auto-collapse groups into public sheets until reviewed.
5. Feed grouped records into surface assignment as composite, dossier, card, slip,
   bookmark, or text page candidates.

Acceptance checks:

- Repeated titles such as same-source batches are grouped rather than published as
  unrelated main sheets.
- Grouping output lists source records and relation labels.
- No source row is deleted or overwritten.

## Problem 3: Image Coverage Metrics Are Too Blunt

Current risk:

- A single image-coverage percentage can hide whether images are open, source-hosted,
  publication-grade, or merely source-return visible.
- IMG02 can be useful but must not be reported as open-image proof.

Target:

- Replace one image percentage with layered image evidence metrics.
- Report metrics by period and by source family.

Required metrics:

- `source_visible_coverage`
- `publication_grade_coverage`
- `open_image_coverage`
- `rights_labeled_coverage`
- `unclear_image_state_rate`
- `anchor_image_available_rate`
- `support_image_available_rate`
- `duplicate_image_url_rate`

Required period bands:

- `pre_1930`
- `1930_1970`
- `1970_2000`
- `2000_2026`

Execution steps:

1. Add or update an audit script for layered image metrics.
2. Split metrics by period, region group, source family, and IMG state.
3. Detect repeated image URLs and repeated source-hosted thumbnails.
4. Flag records where many sheets use the same image.
5. Do not promote IMG00/unclear records to main sheets unless they are intentionally
   text-led and routed through text page / bookmark / rights appendix logic.

Acceptance checks:

- Metrics distinguish source-visible from open-image.
- Period-split metrics are printed in capture reports.
- Duplicate-image warnings are visible before rebuild/publication.

## Problem 4: Public Surface Assignment Is Too Generous

Current risk:

- Too many thin records become main sheets.
- Appendix pages can repeat as placeholders.
- Text pages, cards, slips, and bookmarks are underused or not linked as research units.

Target:

- Recalculate surface assignment using stronger gates.
- Treat main sheet as a research unit, not a default row renderer.

Provisional surface gates:

- `main_sheet`: strong identity, source return, explicit rights state, meaningful visual
  evidence or strong text-led justification, high completeness, and research-unit value.
- `subsheet`: downgraded former main-sheet candidate. It can be visually or textually strong,
  but does not carry enough research-unit weight to stand as the top page. It may have its
  own appendix, text sheet, card, slip, or bookmark children.
- `appendix`: table/evidence-led subsheet for rights, source/citation, relation/classification,
  protocol/context, statement, or typed-index material.
- `text_sheet`: reading-led image/text page for OCR, source description, contextual notes, or
  source excerpts.
- `card`: compact record with image or title plus limited text.
- `slip`: card-bound text supplement for provenance, uncertainty, date, or short notes.
- `bookmark`: lowest fallback/orientation pointer, unresolved lead, external original location,
  or very sparse source route.

Hierarchy:

```text
main sheet
  -> subsheet
    -> appendix
    -> text sheet
    -> card
      -> slip
    -> bookmark
```

Appendix rules:

- One appendix per evidence class per research unit.
- Reuse/inherit appendix evidence downward unless a child record differs materially.
- Suppress placeholder appendices.
- AX01 can support IMG00/01/02/03, but must use real rights/source evidence.
- Repeated consecutive AX01 pages are a generation bug unless each page has materially
  different evidence.

Execution steps:

1. Update the surface assignment policy before rebuilding public payloads.
2. Add group-aware surface generation inputs.
3. Add appendix de-duplication / inheritance logic.
4. Route weak rows into subsheet, appendix, text sheet, card, slip, bookmark, or grouped
   evidence packet.
5. Generate a surface assignment report before frontend rebuild.

Acceptance checks:

- Thin records no longer inflate main sheet counts.
- AX01 pages are not repeated without distinct evidence.
- Text pages appear where strong source text exists.
- Cards/slips/bookmarks exist as real publication surfaces, not just visual labs.

## Problem 5: Contemporary Capture Needs Stronger Noise Filtering

Current risk:

- 1990-2026 capture can ingest generic editorial, portfolio, social, event, ticketing,
  jobs, press-release, or repost pages that do not document design history.

Target:

- Contemporary capture must classify page/source type before scoring.
- Discovery platforms can generate leads but cannot become primary sources without
  provenance.

Decision bands:

- `include`: direct design record plus usable metadata or strong archival context.
- `downgrade`: plausible but missing provenance, date, credits, or primary-source standing.
- `exclude`: routine admin/legal/hiring/ticketing/commerce/repost/trend content.

Positive signals:

- poster, identity, campaign, publication, magazine, typeface, specimen, signage,
  wayfinding, UI, icon, title sequence, archive, collection, object, credits, designed by,
  commissioned by, year, medium, designer, client, critique, review.

Negative signals:

- jobs, careers, tickets, preview party, press release, register, call for entries,
  submission guide, terms, privacy, cookies, shipping, cart, checkout, membership,
  donate, newsletter-only, RFP, tender.

Execution steps:

1. Add contemporary source-type classification before content scoring.
2. Store noise decision and exclusion reason for each rejected or downgraded URL.
3. Mark Pinterest/Instagram/Tumblr/Are.na/Behance-style pages as discovery-only unless
   provenance is established.
4. Keep historically valuable but thin local/community pages in downgrade/manual-review,
   not immediate exclusion.

Implementation status, 2026-06-01:

- `scripts/contemporary_noise_filter.py` implements the reusable filter.
- `scripts/audit_contemporary_noise_filter_v1.py` audits existing 1970-2026 and
  adjacent capture rows.
- The filter is integrated into late-period, source-breadth, independent-Asia,
  and edge-WordPress capture scripts.
- Initial audit result: 281 rows; 243 include candidates, 16 downgrade
  candidates, 22 review leads, 0 discovery-only, 0 excluded noise.

Acceptance checks:

- Capture reports include include/downgrade/exclude counts.
- Rejected URLs have recorded reasons.
- Social/discovery leads cannot become main sheets without corroboration.

## Execution Order

1. Source prospect registry v2.
2. Layered image/source metrics audit.
3. Linkage/group candidate generation.
4. Revised surface assignment gates.
5. Appendix inheritance and repetition suppression.
6. Contemporary noise filter integration.
7. Controlled capture by source family and region.
8. Public payload rebuild only after assignment report passes.

## Commit And Safety Constraints

- Do not stage unrelated frontend edits from the parallel frontend window.
- Do not commit raw payloads before running `scripts/audit_secret_patterns.py`.
- Redact possible API keys, tokens, analytics keys, and source-page secrets from raw HTML.
- Capture reports must state whether a batch is source-prospecting, source-record capture,
  or public-surface publishing.
- Public-surface rebuilds should be deliberate and reported; capture alone should not
  silently change the frontend.
- Capture-phase or source-scope ranges such as `1970-2026` must not appear as
  public object, movement, or sheet chronology. Use
  `scripts/audit_public_date_range_leaks_v1.py` after public payload rebuilds.

## Current Next Task

Start with `source_prospect_registry_v2`.

The first implementation task should create:

- `scripts/generate_source_prospect_registry_v2.py`
- `data/source_prospect_registry_v2.csv`
- `docs/capture/SOURCE_PROSPECT_REGISTRY_v2.md`

The registry should be broad enough to guide future capture and conservative enough to
avoid treating weak repost/inspiration sources as archival evidence.

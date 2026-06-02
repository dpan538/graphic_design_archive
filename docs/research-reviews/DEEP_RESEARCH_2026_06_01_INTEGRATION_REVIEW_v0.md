# Deep Research Integration Review v0

Date: 2026-06-01

Reviewed reports:

- `Rights-Aware Source Discovery for a Distributed Graphic Design History Archive Index.docx`
- `Provenance-First Record Linkage for a Graphic Design History Archive.docx`
- `Rights-Aware Visual Evidence Standard for a Graphic Design Archive Index.docx`
- `Publication-Surface Logic for a Graphic Design History Archive.docx`
- `Inclusion and Noise Filtering for Contemporary Graphic Design Archive Capture.docx`

## Core Finding

The five reports support the archive-box system, but they make one important correction:
the next phase should not simply add more rows. It should expand the source universe,
classify source trust and protocol families, preserve every source record, and publish
only the strongest public surfaces.

The archive should be a distributed evidence index. Major museum APIs remain useful,
but they are only one source family. The next capture strategy must actively include
community archives, newspapers, magazines, university repositories, municipal portals,
poster collections, activist archives, film documentation centers, government cultural
databases, web archives, and local/regional discovery layers.

## Adopted Rules

### Source Discovery

Source discovery should proceed by source family and protocol, not by broad design
keywords alone.

Priority source families:

- custodial archives, national libraries, municipal archives, university special collections;
- newspaper, magazine, OCR, and periodical portals;
- OAI-PMH, IIIF, Omeka, WordPress REST, CONTENTdm, DSpace, Kramerius, ArchivesSpace/EAD;
- community, activist, Indigenous, diaspora, and identity-based archives;
- film, poster, festival, design-school, and born-digital web archives;
- regional aggregators such as Japan Search, NDL Search, LA Referencia, Archives Portal Europe, ArchiveGrid, Kramerius registry, and comparable local routers.

Blogs, portfolios, Pinterest-style repost boards, commercial inspiration sites, and social
platforms are discovery leads by default, not sources of record, unless they provide
custody, stable identifiers, context, rights, and source-level metadata.

### Record Linkage

Repeated or overlapping records should not be silently deduplicated.

Operational rule: merge navigationally, never evidentially.

Every encountered source keeps its own source record. Public display can then choose:

- `composite_main_record`: same entity, same layer, strong identity evidence;
- `grouped_appendix_or_dossier`: coherent cluster, but differences in manifestation, carrier, language, edition, issue, or unresolved identity;
- `separate_record`: identity is weak, disputed, or historically distinct.

The linkage process must classify entity layer before matching: work/design concept,
manifestation/edition, item/object, event, agent, movement, publication title, visual
record, or digital surrogate.

Strong anchors include accession numbers, call numbers, issue numbers, shelfmarks,
persistent identifiers, colophon data, edition statements, signed inscriptions, and image
or scan anchors. Title similarity alone is not enough.

### Visual Evidence

Image coverage must be reported in layers, not as one inflated percentage.

Required coverage metrics:

- source-visible coverage: at least one lawful visual witness or provider return path;
- publication-grade coverage: at least one image adequate for sheet publication and citation;
- open-image coverage: image can be locally displayed/reused under open or public-domain terms;
- rights-labeled coverage: visible image has explicit display state and rights note;
- unclear image state: should stay below a strict warning threshold.

For this project, the user-facing launch target remains high: published design records
should approach full source-visible coverage and full rights-labeled coverage. This does
not mean 100% open-image coverage, and it does not justify copying images locally.

Main sheets should normally carry one anchor image plus one to three supporting images.
Six images is a soft maximum before overflow to appendix. The image should identify the
object, while support images must add distinct evidence such as verso, interior spread,
detail, variant, scale, process, inscription, or sequence.

### Surface Publication

Do not force every record into a main sheet.

Public surfaces should follow record strength:

- main sheet: strong identity, source return, rights clarity, meaningful visual evidence, and enough metadata/context to read as a research unit;
- text page: strong documentary value but weak or restricted lawful image access;
- appendix: evidence overflow, rights/source/citation/relation complexity, image sequences, or cluster documentation;
- card: compact, stable, citable minimal record;
- slip: strong visual evidence but weak metadata, clearly provisional;
- bookmark: historically useful pointer, unresolved lead, or external/original-location note.

Appendix repetition must be limited. Use one appendix per evidence class per research
unit and inherit downward unless a child record materially differs. Placeholder appendices
should be suppressed. If an appendix only says that nothing is known, keep that as a
one-line status on the relevant sheet/card/slip instead.

### Contemporary Noise Filtering

Contemporary capture should use three bands:

- include: direct evidence plus usable metadata or strong archival context;
- downgrade: plausible design record but weak provenance, date, credits, or primary-source standing;
- exclude: routine administrative, legal, hiring, ticketing, commerce, repost, or generic trend content with little design-historical evidence.

Scripts should classify source type before page scoring:

- primary archive/object/award domains;
- designer, studio, or client-origin domains;
- independent archives/publications;
- social/discovery platforms;
- administrative/transactional environments.

Social platforms and repost networks can preserve leads, but should not become primary
evidence unless the original source has disappeared and the record is explicitly marked
as a downgraded surrogate.

## Required System Adjustments

1. Build a `source_prospect_registry_v2` with source family, region, language/script,
   protocol hints, rights posture, expected image path, expected text path, and source
   credibility tier.
2. Add period-split image metrics: pre-1930, 1930-1970, 1970-2000, 2000-2026.
3. Add source-breadth metrics: Western/non-Western, institutional/community, custodial/
   aggregator/editorial/discovery-only, protocol family, and region group.
4. Add linkage candidates before public-surface promotion: same entity, possible same,
   same work different manifestation, same visual item different carrier, digital surrogate,
   translation, derived from, documents, related but not same.
5. Recalculate main-sheet eligibility using stronger gates. Thin records should become
   cards, slips, bookmarks, text pages, or grouped appendices rather than weak sheets.
6. Change appendix generation from per-record automatic insertion to evidence-class
   inheritance. Repeated AX01 pages should collapse into one rights appendix at the
   research-unit level unless a child has genuinely different rights evidence.
7. Add regional grouping metadata for public navigation: continent or macro-region,
   subregion, country/territory/place. This supports regional browsing without turning
   time into a folder axis.
8. Keep raw payloads redacted and run `scripts/audit_secret_patterns.py` before every
   commit that includes raw HTML, JSON, or extracted source text.

## Next Capture Direction

The next capture pass should not target one more broad chronological tranche yet.
It should first expand and classify sources.

Recommended order:

1. Create a 200-source prospect registry from the source-discovery report families.
2. Probe sources by protocol family and region, not by English keywords alone.
3. Promote only repeatable, rights-readable sources into adapter candidates.
4. Run small adapter-specific captures that preserve raw source records and do not
   automatically publish thin records as main sheets.
5. Generate linkage/group candidates from repeated titles, repeated images, issue-level
   records, campaign clusters, publication series, and same-source batches.

## Policy Consequences

The project should stop treating high image percentage as a single health score. A
record can be visually discoverable, publication-grade, open, rights-restricted, or only
source-return visible. These are different states and should be reported separately.

The project should also stop treating source count as raw volume. Two hundred weak
repost sites would be worse than fifty properly classified local, community, university,
government, newspaper, IIIF/OAI, and special-collection sources. The goal is source
breadth with provenance, not just a bigger list.


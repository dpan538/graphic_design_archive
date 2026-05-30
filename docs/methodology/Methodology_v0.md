# Methodology v0

**Project:** Modern Graphic Design History Archive Index  
**Working definition:** A rights-aware archive index and research framework for modern graphic design history.  
**Date:** 2026-05-29  
**Status:** Internal methodology draft, not a public manifesto.

## 1. Project Definition

This project is a rights-aware archive index and research framework for modern graphic design history. It does not attempt to replace original archives, produce a textbook, deliver a course, become a museum education platform, or construct a single visual or historical narrative. Its primary task is to organize distributed resources into a readable, searchable, and traceable structure.

The project connects works, designers, institutions, movements, media, technologies, places, historical nodes, texts, source records, citations, and rights information. Its value comes from making dispersed materials easier to locate, compare, cite, and return to their original institutional contexts.

The public system should remain methodologically restrained. It may support later interpretation, including research on recurrence, reuse, non-linear time, historical memory, and visual structures, but it should not force those hypotheses into the interface as predetermined conclusions. The website provides a framework and research method; any later humanistic argument should be developed from the accumulated records, classifications, logs, and evidence.

## 2. Core Principles

### 2.1 Integrity

Integrity means that the system must not misrepresent what it knows, where it learned it, or what it is allowed to show.

The project must:

- distinguish original source metadata from normalized local metadata;
- distinguish archival fact, editorial classification, and research inference;
- distinguish visual resemblance from documented historical relation;
- distinguish metadata rights, object rights, and image rights;
- never imply that linked external collections are owned or reproduced by this project;
- preserve source names, source URLs, access dates, citations, and rights statements;
- expose uncertainty rather than hiding it behind clean interface labels;
- avoid using AI-generated text as evidence.

### 2.2 Reproducibility

Reproducibility means that another researcher should be able to understand how the archive index was assembled and, where possible, rebuild a comparable version from documented sources and rules.

The project must preserve:

- a source registry;
- data ingestion logs;
- raw source snapshots or source references where legally and technically possible;
- normalization scripts or mapping rules;
- classification criteria;
- relation assertion rules;
- record version history;
- dataset release snapshots;
- documentation for search, metadata, rights, and citation policy.

The website is not the only research output. The reusable research object should include the schema, source registry, sample records, transformations, documentation, and versioned exports.

## 3. System Analogy

The project should be understood as a living research system rather than a single line of history.

- **Skeleton:** historical spine, categories, and hierarchical reading structure.
- **Blood circulation:** source registry, external archive links, metadata movement, and update workflows.
- **Nervous system:** global search, indexes, cross-references, and internal navigation.
- **Immune system:** rights review, citation requirements, provenance trails, uncertainty fields, and editorial review.

This analogy is useful because it prevents the project from becoming either a simple timeline or an uncontrolled graph. Humanistic research depends on several interdependent systems: chronology, evidence, classification, circulation, verification, and interpretation.

## 4. Historical Framework

The project uses a historical spine for orientation, not as a totalizing story. The spine is a curated reading structure that allows records to be located within broad historical conditions. It should remain revisable.

The current scope begins with writing, printing, reproduction, and industrialized visual communication as preconditions, but the dense focus is modern and contemporary graphic design from the nineteenth century to the present.

Initial historical spine nodes may include:

1. Writing, printing, and reproduction as preconditions.
2. Industrial print, lithography, advertising, posters, and mass circulation.
3. Arts and Crafts, Art Nouveau, reform movements, and early modern visual culture.
4. Constructivism, Bauhaus, New Typography, and avant-garde print culture.
5. Swiss Style, International Typographic Style, systems, grids, and information design.
6. Corporate identity, editorial design, branding, and institutional communication.
7. Protest graphics, feminist graphics, decolonial graphics, counterpublics, and social movements.
8. Postmodern graphic design, desktop publishing, independent type, and digital production.
9. Web, interface, platform visual culture, and networked visual communication.

These nodes are not chapters of a textbook. They are entry points that help users read, search, and return to source materials.

## 5. Archive Index Method

The project should prioritize indexing over possession.

For each relevant resource, the system should record:

- what the resource is;
- where it is held or published;
- who created, commissioned, printed, published, collected, described, or digitized it;
- how it is dated;
- which medium, process, format, or technology it involves;
- which movement, period, theme, place, or institution it may be associated with;
- how the project knows this;
- what can and cannot be displayed;
- how users should cite and revisit the source.

The project should not aim to gather images aggressively. When image rights are unclear, the system should provide metadata and external links rather than local display. When IIIF manifests or permitted thumbnails are available, they may be embedded only with required attribution and rights information.

## 6. Workflow v0

The workflow should proceed in four major phases. The project should not begin with a polished front end or AI features.

1. **Methodology and framework validation:** validate the historical spine, movement taxonomy, source strategy, classification rules, rights policy, and reproducibility standards. This includes targeted Deep Research tasks that produce verifiable lists of movements, nodes, source types, and candidate collections.
2. **Search and indexing validation:** test whether records can be searched, filtered, cited, linked, and returned to source archives without requiring local image possession. This can begin with manually curated sample records.
3. **Database and ingestion system:** build the canonical schema, source registry, ingestion logs, normalization workflow, and export pipeline.
4. **Frontend and local WebLLM:** design the reading/search interface only after the data model and search behavior are stable. WebLLM belongs at the end of the process as an optional, local, packaged browser-side enhancement.

The first engineering prototype should therefore be a searchable research index, not a visual website.

### 6.1 Source Discovery

Identify potential sources through research relevance, accessibility, rights clarity, metadata quality, and historical coverage. Each source begins as a candidate in the source registry.

Source registry fields:

- source ID;
- source name;
- source type;
- institution or maintainer;
- geographic coverage;
- historical coverage;
- media coverage;
- access method;
- API or dataset URL;
- terms of use URL;
- rights policy;
- citation recommendation;
- metadata quality notes;
- update frequency;
- ingestion status;
- last reviewed date;
- reviewer notes.

### 6.2 Rights Review

Before ingestion or display, classify each source by rights risk.

Rights states:

- `metadata_open`: metadata may be stored and reused.
- `metadata_limited`: metadata may be indexed only under source terms.
- `image_open`: image may be displayed or copied under an open license.
- `image_embed_only`: image may be shown through source-hosted embed or IIIF only.
- `thumbnail_only`: only thumbnails may be displayed.
- `link_only`: no local image display; link to source.
- `unknown`: do not display image until reviewed.

The system must separately track metadata rights, image rights, and object rights. A public-domain artwork can still have a restricted digital surrogate. Open metadata does not imply open images.

### 6.3 Ingestion

Ingestion should be conservative and documented.

Allowed ingestion modes:

- official API;
- official open dataset;
- IIIF manifest;
- manually entered citation record;
- manually entered source registry record;
- limited HTML extraction only when allowed by terms, robots policy, and source stability;
- no image scraping unless rights and terms clearly permit it.

Raw ingested material should be stored as received when permitted. If raw storage is not allowed or unnecessary, the system should store the source URL, access date, record identifier, and extraction log.

The project should treat scraping as a classification and indexing aid, not as a collection-building strategy. Since many important graphic design materials are not formally collected by museums or archives, the project may need to discover distributed traces across institutional websites, periodicals, exhibition pages, catalogues, studio sites, bibliographies, and web archives. Even then, the default output should be link, citation, metadata, and classification, not copied media.

### 6.4 Normalization

Normalize only what is needed for search, classification, citation, and relation modeling.

Required normalized fields for Launch records:

- local ID;
- entity type;
- preferred title or label;
- original title or label;
- creator or agent display;
- creator role;
- date display;
- date start;
- date end;
- place display;
- medium or process;
- format or object type;
- holding institution;
- source name;
- source record URL;
- source record ID;
- citation;
- rights URI or rights note;
- image policy;
- historical spine node;
- theme tags;
- related entity IDs;
- uncertainty note;
- last verified date;
- local record version.

### 6.5 Entity Resolution

Entity resolution must be cautious. The system should not merge entities only because names are similar.

Resolution evidence may include:

- source authority identifier;
- Wikidata QID;
- Getty ULAN ID;
- VIAF ID;
- ORCID;
- ROR for institutions;
- identical source record links;
- matching dates and biographical context;
- documented institutional affiliation.

When uncertain, the system should use `possibly_same_as` rather than merging records.

### 6.6 Classification

Classification should be explicit and reversible.

Each classification should record:

- classification type;
- assigned value;
- source of classification;
- whether it came from the original source, controlled vocabulary, or editorial judgment;
- confidence level;
- reviewer;
- date assigned.

Classification types may include:

- period;
- movement;
- medium;
- technology;
- object type;
- place;
- institution;
- theme;
- historical spine node.

### 6.7 Relation Assertion

Relations should be typed edges, not generic related links.

Core relation types:

- `created_by`;
- `designed_by`;
- `printed_by`;
- `published_by`;
- `commissioned_by`;
- `held_by`;
- `described_by_source`;
- `depicted_in_image`;
- `uses_medium`;
- `uses_technology`;
- `associated_with_movement`;
- `located_in`;
- `active_in`;
- `trained_at`;
- `taught_at`;
- `exhibited_at`;
- `discussed_in_text`;
- `cited_by_text`;
- `same_as`;
- `possibly_same_as`;
- `visually_resembles`;
- `editorially_associated_with`.

Important rule: `visually_resembles` is not evidence of influence. It should be treated as a weak relation unless supported by additional evidence.

Each relation must include:

- subject entity;
- predicate;
- object entity;
- source or citation;
- assertion type;
- confidence;
- created by;
- reviewed by;
- created date;
- version.

### 6.8 Editorial Review

Records should move through states:

1. `candidate`
2. `source_reviewed`
3. `rights_reviewed`
4. `ingested`
5. `normalized`
6. `classified`
7. `relation_reviewed`
8. `published`
9. `deprecated`

Only records with source, citation, rights status, and at least one reviewed classification should be published.

### 6.9 Publication

Publication should expose enough structure for public reading without overclaiming.

Each public record should show:

- title or label;
- entity type;
- source;
- source link;
- citation;
- rights and display policy;
- historical spine node;
- categories;
- related entities;
- uncertainty notes where applicable;
- last verified date.

The public interface should avoid ranking mechanisms that imply importance unless the ranking basis is explicit.

### 6.10 Refresh and Versioning

External records change. The system should support rechecking and versioning.

For each source:

- record last checked date;
- store source last modified date where available;
- compare current source response against previous response;
- log field-level changes where feasible;
- preserve local editorial changes separately from source changes;
- release periodic versioned exports.

## 7. Data Model v0

### 7.1 Core Entities

- `WorkObject`: poster, book, magazine, type specimen, advertisement, identity system, package, website, interface, ephemera, or other design artifact.
- `Person`: designer, artist, editor, printer, typographer, curator, historian, collector, writer.
- `Organization`: museum, archive, school, publisher, studio, company, political group, professional association.
- `MovementPeriod`: movement, period, formation, style category, or historical grouping.
- `MediumTechnology`: letterpress, lithography, offset, phototypesetting, desktop publishing, web, interface system, platform.
- `Place`: country, region, city, route, or historically specific location.
- `TextPublication`: book, article, catalogue essay, exhibition text, course bibliography, website essay, interview.
- `Theme`: propaganda, modernity, capitalism, gender, colonialism, global modernisms, labor, information systems, visual identity, network culture.
- `Source`: institution, database, archive, publication, dataset, API, or collection.
- `SourceRecord`: a specific external object page, API response, dataset row, IIIF manifest, or bibliographic record.
- `ImageAsset`: source-hosted image, thumbnail, IIIF canvas, digital surrogate, or local permitted asset.
- `Assertion`: a statement made by the project, linked to evidence and confidence.
- `Citation`: human-readable and machine-readable source reference.

### 7.2 Relation Model

The graph should be implemented as typed relations over stable entities. It does not require a native graph database in the Launch.

Minimum relation fields:

- relation ID;
- subject entity ID;
- predicate;
- object entity ID;
- source record ID;
- citation ID;
- assertion status;
- confidence;
- note;
- created at;
- updated at;
- reviewer.

## 8. Database Decision v0

### 8.1 Recommended Canonical Database

Use PostgreSQL as the canonical application database for the Launch and early production version.

Reasons:

- strong relational integrity for entities, sources, citations, and assertions;
- typed edge tables can model the archive graph without introducing a separate graph database too early;
- JSONB can preserve source-specific raw fields alongside normalized fields;
- built-in full-text search supports indexed text search through `tsvector` and `tsquery`;
- optional `pgvector` can support semantic search later without moving to a separate vector database;
- mature backup, migration, and hosting ecosystem.

The project should not start with Neo4j or a specialized graph database. A graph database may become useful later, but the Launch needs auditability, citation, and editorial workflow more than graph visualization performance.

### 8.2 Reproducibility Layer

PostgreSQL should not be the only durable research object. Each public release should export:

- JSONL records;
- CSV tables for entities, relations, sources, citations, and assertions;
- SQL schema;
- a read-only SQLite or DuckDB snapshot for local exploration;
- a changelog;
- a data dictionary.

SQLite FTS5 can be used for a portable local search snapshot because it is explicitly designed for full-text search over document collections. This supports reproducibility and offline review.

### 8.3 Optional Search and Vector Layer

The Launch should use deterministic lexical search first. Semantic search is optional.

Recommended staged approach:

1. PostgreSQL full-text search for titles, descriptions, people, institutions, texts, themes, and source records.
2. Faceted filters over historical node, entity type, medium, place, source, rights status, date range, and movement.
3. Optional pgvector embeddings for semantic similarity after the metadata model stabilizes.
4. Optional LanceDB only if the project later requires a separate multimodal or vector-heavy research layer.

Do not make vector search the primary source of truth. It is a retrieval aid, not an evidentiary method.

## 9. Search and WebLLM Decision v0

### 9.1 Search as Core Function

The global search box is a core research access point. It should help users find and read records, not generate ungrounded historical interpretation.

Search should support:

- keyword search;
- phrase search;
- entity search;
- source search;
- date range filtering;
- historical node filtering;
- medium and technology filtering;
- place filtering;
- rights filtering;
- text and bibliography search;
- result snippets with source context;
- stable result URLs where possible.

Search results should show why an item matched: title, source field, text excerpt, theme, person, place, or relation.

### 9.2 WebLLM Position

WebLLM should be treated as an optional peripheral tool, not a foundation of the archive index. It must be local, browser-side, and packaged with the project or loaded as a project-controlled local asset. It should not call a hosted LLM API for ordinary public use.

Possible uses:

- query expansion;
- translating user questions into structured filters;
- summarizing already retrieved search results;
- helping users understand fields and source types;
- suggesting related search terms;
- generating temporary reading aids from cited records.

Prohibited uses:

- inventing historical claims;
- classifying records without review;
- replacing citations;
- deciding rights status;
- merging entities;
- producing public summaries without source grounding.

### 9.3 Recommended WebLLM Stack

If local browser-based LLM functionality is added, use MLC WebLLM as the primary candidate because it runs LLM inference in the browser with WebGPU acceleration and exposes an OpenAI-compatible API. It should run in a web worker so it does not block the interface. The implementation goal is local inference, not API-mediated chat.

However, many users will not have reliable WebGPU support or enough local memory. Therefore:

- WebLLM must be optional;
- the site must remain fully usable without it;
- model availability should be detected at runtime;
- the system should provide a no-AI fallback;
- model choice should be configurable rather than hard-coded in the methodology.

For semantic embeddings or lightweight local similarity, evaluate Transformers.js with WebGPU support. This may be more appropriate than a full chat model for query expansion and semantic search experiments.

Initial decision:

- **Launch:** no WebLLM required.
- **Database/search phase:** no WebLLM required.
- **Frontend phase:** no WebLLM required unless search and reading workflows are already stable.
- **Final enhancement phase:** test packaged local WebLLM as a client-side query assistant.
- **Alternative enhancement:** test Transformers.js embeddings for local semantic search experiments.
- **Rule:** AI features may assist retrieval, but all public records and claims must remain citation-bound.

## 10. Potential Source Strategy

### 10.1 Tier A: Official APIs and Open Datasets

These should be prioritized for Launch because they support reproducibility and lower-risk ingestion.

- **V&A Collections API:** strong design and decorative arts coverage; JSON/CSV; images and metadata under V&A terms; useful for design history, provenance, and data exploration.
- **Cooper Hewitt Collections API / GitHub data:** design-focused collection; GraphQL API; large object set; useful for design object metadata.
- **MoMA Collection Dataset:** CC0 metadata on GitHub; useful for canonical modern art and design records; images are not included and require separate licensing.
- **Smithsonian Open Access:** API and GitHub access; many CC0 assets; useful where open image display is needed.
- **Europeana APIs:** cross-institutional European cultural heritage metadata; EDM model; search, record, and IIIF APIs.
- **DPLA API:** U.S. cultural heritage aggregator using a metadata application profile and JSON-LD; useful for broad discovery and crosswalks.
- **Harvard Art Museums API:** objects, people, exhibitions, publications, and galleries; useful for museum-linked records.
- **The Met Collection API:** useful for open access collection metadata and images where relevant.
- **Library of Congress JSON API:** useful for posters, prints, photographs, books, periodicals, and public-domain or rights-described materials.
- **Art Institute of Chicago API:** REST-style JSON access to public collection data; useful for posters, prints, typography-adjacent works, and institutional metadata.
- **Cleveland Museum of Art Open Access API:** open metadata and images for public-domain works; useful as a lower-rights-risk image and metadata source.
- **Rijksmuseum Data Services:** OAI-PMH, Search API, and LDES access to collection metadata; useful for European print, poster, and visual culture records.
- **NYPL Digital Collections API:** useful for posters, prints, ephemera, photographs, maps, books, and public-domain digital collection records.
- **Wellcome Collection APIs:** catalogue and IIIF access for visual culture, books, journals, archives, manuscripts, and objects; useful for health, public information, and print culture histories.
- **Getty Museum Collection / Getty data services:** useful for collection records, authority data, and vocabulary-linked cultural heritage metadata.
- **Yale LUX:** useful as a linked-data precedent and possible cross-collection discovery source.

### 10.2 Tier B: Design-Specific Archives and Databases

These are historically important but may require manual indexing, link-only records, or permission-aware handling.

- Letterform Archive;
- People’s Graphic Design Archive;
- Design Reviewed;
- Fonts In Use;
- Bauhaus-Archiv;
- Museum für Gestaltung Zürich poster collection;
- Poster House;
- Center for the Study of Political Graphics;
- East Asian Graphics Archive;
- local university, studio, and designer archives.
- AIGA Design Archives;
- RIT Cary Graphic Arts Collection;
- Herb Lubalin Study Center;
- Milton Glaser Design Study Center and Archives;
- Isotype Collection and related Otto and Marie Neurath sources;
- Typotheque articles and type-history resources;
- Eye magazine archive;
- Design Observer archive;
- Slanted archive;
- digital studio archives and designer-maintained project pages;
- regional graphic design archives and independent documentation projects.

Tier B sources should generally begin as source registry entries and manually curated records. Automated scraping should not be assumed. For sources without formal APIs, the correct first step is to record them as linkable evidence sources, inspect rights and terms, and use manual or semi-automated indexing only where permitted.

### 10.3 Tier C: Textual and Bibliographic Sources

These sources support historical spine construction and interpretation. They should usually be represented as citation and text nodes rather than bulk-ingested object records.

- design history books;
- journal articles;
- exhibition catalogues;
- catalogue essays;
- course bibliographies;
- interviews;
- manifestos;
- institutional histories;
- digitized periodicals where rights allow;
- public domain texts;
- OCR-derived text corpora with documented source and quality.
- Internet Archive records where metadata, rights, and item stability are sufficient;
- HathiTrust records and bibliographic metadata where access allows;
- Gallica / BnF APIs for French books, periodicals, posters, and visual print culture;
- Chronicling America for historical newspaper advertising, layout, typography, and public visual communication;
- institutional digitized magazines and design periodicals;
- library catalogues and finding aids;
- thesis and dissertation repositories;
- conference proceedings and design education syllabi.

### 10.4 Authority and Vocabulary Sources

Use controlled vocabularies where they improve consistency, but do not force all design-specific terms into inadequate external categories.

Potential authorities:

- Getty AAT for object types, processes, and styles;
- Getty ULAN for artists and designers;
- Getty TGN for places;
- Wikidata for multilingual identifiers and cross-links;
- VIAF for name authority;
- ORCID for contemporary researchers and contributors;
- ROR for institutions;
- Library of Congress Subject Headings for subject terms;
- RightsStatements.org for standardized rights statements.

The local vocabulary must allow project-specific terms where external vocabularies are incomplete.

## 11. Interface Method v0

The interface should serve reading, search, and traceability. It should not overperform as a spectacle of data visualization.

Required interface components:

- global search;
- historical spine / tree view;
- source registry;
- entity detail page;
- source record detail page;
- citation and rights panel;
- related records panel;
- filters and facets;
- uncertainty and provenance notes.

Optional interface components:

- lightweight graph view;
- timeline view;
- map view;
- word frequency view;
- corpus search;
- WebLLM-assisted query expansion.

The tree structure should be readable before it is visually impressive. The graph view should be an aid, not the project’s main claim.

## 12. Word Frequency and Text Search

Word frequency, corpus search, and term tracking are useful peripheral research tools. They can help show how certain terms, concepts, or design ideas appear across texts and periods.

Possible research terms:

- grid;
- system;
- identity;
- communication;
- modern;
- universal;
- function;
- ornament;
- information;
- corporate;
- vernacular;
- propaganda;
- interface;
- user;
- network;
- platform.

These tools should be presented as evidence aids, not proof engines. Frequency does not equal importance. The system should show corpus scope, OCR quality, source distribution, and date coverage.

## 13. Framework Validation Before Launch

Before the database Launch, the project needs a structured framework validation phase.

Outputs:

- a comprehensive movement and historical node map;
- a medium and technology taxonomy;
- a source universe list;
- a rights-risk map by source type;
- a first-pass keyword and search vocabulary;
- a list of candidate records for each historical node;
- a classification rulebook that explains how a record is attached to a node.

Deep Research should be used here to produce structured, verifiable lists rather than broad theoretical summaries. The output should be suitable for conversion into CSV or database seed records.

The historical node map should include not only canonical movements but also media regimes, regional formations, institutional systems, publishing formats, labor contexts, political uses, and digital/interface transitions. The goal is not to impose a final story, but to create a searchable framework into which records can be placed and revised.

## 14. Launch Scope

The Launch should prove the method, not the total history.

Recommended Launch:

- 7-9 historical spine nodes;
- 4-6 source collections;
- 60-100 object or source records;
- 20-30 person, institution, movement, medium, place, and text records;
- source registry;
- rights policy;
- citation model;
- metadata schema;
- PostgreSQL database;
- JSONL/CSV export;
- global search;
- historical tree view;
- record detail page;
- related records panel;
- no required WebLLM.

Launch success criteria:

- every public record has a source link and citation;
- every public record has a rights state;
- every public classification can be traced to source metadata or editorial rule;
- every relation has a type and confidence level;
- records can be exported and inspected outside the website;
- search returns understandable results with source context.

## 15. Research Documentation Set

The project should maintain the following documents from the start:

- `README.md`: public overview.
- `Methodology_v0.md`: current methodology.
- `SOURCE_REGISTRY.md` or database-backed source registry export.
- `DATA_DICTIONARY.md`: fields, entity types, relation types.
- `RIGHTS_POLICY.md`: image, metadata, object rights handling.
- `INGESTION_PROTOCOL.md`: allowed source and ingestion methods.
- `CLASSIFICATION_RULES.md`: historical nodes, movement tags, medium tags.
- `RELATION_RULES.md`: relation definitions and evidence requirements.
- `CHANGELOG.md`: project and data release changes.
- `CITATION.cff`: citation metadata for the project.
- `prompts/DEEP_RESEARCH_NODE_MAP_PROMPT.md`: prompt for validating historical nodes, movements, media, and source universe.

## 16. Immediate Next Steps

1. Freeze this Methodology v0 as the first internal charter.
2. Run targeted Deep Research to validate the historical node and movement framework.
3. Run targeted Deep Research to expand and classify the source universe.
4. Create a starter source registry with 30-50 candidate sources.
5. Define the first version of the entity and relation schema.
6. Choose the first 4-6 Launch sources.
7. Select 7-9 initial historical spine nodes from the larger validated node map.
8. Create sample records manually before automating ingestion.
9. Build a small PostgreSQL schema and seed dataset.
10. Implement deterministic search before AI-assisted search.
11. Add rights and citation panels before adding visual graph features.
12. Export the first reproducible dataset snapshot.
13. Leave local packaged WebLLM until the final enhancement stage.

## 17. Reference Links Consulted

- MLC WebLLM: https://github.com/mlc-ai/web-llm
- MLC WebLLM JavaScript SDK: https://llm.mlc.ai/docs/deploy/webllm.html
- Hugging Face Transformers.js WebGPU guide: https://huggingface.co/docs/transformers.js/guides/webgpu
- PostgreSQL full text search types: https://www.postgresql.org/docs/current/datatype-textsearch.html
- SQLite FTS5: https://www.sqlite.org/fts5.html
- pgvector: https://github.com/pgvector/pgvector
- LanceDB documentation: https://docs.lancedb.com/
- V&A Collections API: https://developers.vam.ac.uk/guide/v2/welcome.html
- Cooper Hewitt Collections API: https://apidocs.cooperhewitt.org/api-home/
- MoMA Collection Dataset: https://github.com/MuseumofModernArt/collection
- Smithsonian Open Access: https://www.si.edu/openaccess
- Europeana APIs: https://www.europeana.eu/en/apis
- DPLA Field Reference: https://pro.dp.la/developers/field-reference
- Harvard Art Museums API: https://harvardartmuseums.org/collections/api
- Library of Congress JSON/YAML API: https://www.loc.gov/apis/json-and-yaml/
- Art Institute of Chicago API: https://api.artic.edu/docs
- Cleveland Museum of Art Open Access API: https://www.clevelandart.org/open-access-api
- Rijksmuseum Data Services: https://data.rijksmuseum.nl/docs
- NYPL Digital Collections API: https://api.repo.nypl.org/
- Wellcome Collection Developers: https://developers.wellcomecollection.org/
- Getty data services: https://data.getty.edu/
- Yale LUX documentation: https://project-lux.github.io/documentation/
- Chronicling America API: https://www.loc.gov/apis/additional-apis/chronicling-america-api/
- Gallica search API: https://api.bnf.fr/fr/api-gallica-de-recherche
- RightsStatements.org documentation: https://rightsstatements.org/en/documentation/
- IIIF Presentation API: https://iiif.io/api/presentation/4.0/

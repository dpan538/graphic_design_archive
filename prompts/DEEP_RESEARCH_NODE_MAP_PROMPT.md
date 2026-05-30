# Deep Research Prompt: Historical Nodes, Movements, Sources, and Search Framework

I am developing a project defined as:

**A rights-aware archive index and research framework for modern graphic design history.**

The project does not replace original archives, does not copy collections, does not build a course or textbook, and does not impose a single visual or historical narrative. It is a searchable, readable, citation-bound index that connects distributed works, texts, people, institutions, movements, media, technologies, places, and historical nodes back to their original sources.

The project prioritizes indexing over possession. It should provide metadata, citation, source links, rights status, classification, and search access. It should almost never copy images unless rights clearly allow it. It is a window into distributed archives, not a new archive that absorbs everything.

Previous research established the need for integrity and reproducibility:

- every record must have source, citation, rights state, and access date;
- source metadata must be separated from normalized metadata;
- editorial classification must be separated from source fact;
- visual resemblance must be separated from documented relation;
- AI may assist search later but cannot become evidence;
- WebLLM, if used, must be local/browser-side and belongs only at the final enhancement stage.

Please conduct a deep research study to validate the project framework before database implementation.

## Research Goal

Produce a comprehensive, structured framework for indexing modern graphic design history. The output should be practical enough to become seed data for a database or CSV source registry.

Do not write a general essay. Produce structured lists, taxonomies, tables, and methodological notes.

## 1. Historical Spine and Node Map

Create a comprehensive map of historical nodes in graphic design history, from preconditions to contemporary networked visual communication.

Include:

- writing, inscription, manuscript, and early reproduction as background;
- printing, movable type, engraving, lithography, chromolithography, and industrial print;
- nineteenth-century commercial print, advertising, posters, magazines, newspapers, packaging, and illustrated press;
- Arts and Crafts, Art Nouveau, Jugendstil, Secession, and reform movements;
- Futurism, Dada, De Stijl, Constructivism, Suprematism, Productivism, and photomontage;
- Bauhaus, New Typography, modernist typography, avant-garde books and magazines;
- propaganda, wartime graphics, public information, state design, and political communication;
- Swiss Style, International Typographic Style, grids, systems, information design, wayfinding;
- corporate identity, branding, editorial systems, packaging systems, and design management;
- postwar design schools, professional organizations, design awards, exhibitions, and canon formation;
- protest graphics, counterpublics, feminist graphics, queer graphics, Black graphic histories, Indigenous and decolonial graphics, labor graphics;
- postmodern graphic design, vernacular design, punk, zines, independent publishing, subculture graphics;
- phototypesetting, Letraset, desktop publishing, PostScript, digital type, independent type foundries;
- web design, interface design, screen typography, browser culture, networked media, social platforms, templates, and algorithmic visual communication;
- contemporary global graphic design, regional modernisms, platform aesthetics, generative design, and AI-assisted visual production.

For each node, provide:

- node name;
- approximate date range;
- geographic centers and transnational routes;
- associated movements or formations;
- key media and technologies;
- key object types;
- key people, institutions, schools, publishers, studios, or collectives;
- likely archive/source types;
- search keywords;
- common metadata fields needed;
- rights risk level;
- notes on under-documented or non-canonical histories.

## 2. Movement and Formation Taxonomy

List as many relevant movements, formations, schools, tendencies, and named historical groupings as possible.

Do not restrict the list to canonical Western movements.

Include:

- canonical movements;
- regional movements;
- design schools;
- publishing cultures;
- technical regimes;
- political graphics formations;
- typography movements;
- poster movements;
- magazine and editorial cultures;
- identity and systems-design formations;
- digital/interface formations;
- counter-histories and under-documented formations.

For each item, provide:

- name;
- alternate names;
- date range;
- region;
- associated people/institutions;
- representative media;
- relation to graphic design;
- source confidence;
- recommended search terms;
- possible authority identifiers if available.

## 3. Medium, Technology, and Format Taxonomy

Create a taxonomy of media, technologies, and formats relevant to graphic design history.

Include:

- letterpress;
- woodcut;
- engraving;
- etching;
- lithography;
- chromolithography;
- screen printing;
- offset lithography;
- halftone;
- photomontage;
- phototypesetting;
- dry transfer;
- Letraset;
- paste-up;
- mechanical artwork;
- type specimen;
- magazine;
- newspaper;
- poster;
- book jacket;
- exhibition catalogue;
- corporate identity manual;
- packaging;
- signage;
- wayfinding;
- map;
- information graphic;
- zine;
- website;
- interface;
- digital font;
- template;
- social media graphic;
- motion graphic;
- generative visual system.

For each, provide:

- definition;
- date range;
- relation to graphic design;
- associated source types;
- metadata fields needed;
- search keywords;
- rights/display issues.

## 4. Source Universe

List potential sources for indexing modern graphic design history.

Prioritize sources that can be used for link, citation, metadata, and discovery. Do not assume image copying.

Include:

- museum collection APIs;
- cultural heritage aggregators;
- libraries and digital collections;
- design-specific archives;
- typography databases;
- poster archives;
- political graphics archives;
- periodical archives;
- newspaper archives;
- book and catalogue repositories;
- university special collections;
- designer/studio archives;
- professional organization archives;
- exhibition archives;
- web archives;
- regional and non-Western design archives;
- community archives;
- independent documentation projects;
- open datasets;
- authority and vocabulary sources.

For each source, provide:

- name;
- URL;
- source type;
- access method: API, dataset, search interface, IIIF, OAI-PMH, manual only, unknown;
- geographic/historical coverage;
- relevance to graphic design;
- likely record types;
- rights and terms summary;
- metadata quality estimate;
- whether automated ingestion seems appropriate;
- whether link-only indexing is safer;
- recommended priority: Launch, Launch, Later, or Reference Only.

## 5. Search Vocabulary

Produce an initial search vocabulary for the project.

Include:

- movement terms;
- medium and technology terms;
- object type terms;
- institutional terms;
- thematic terms;
- regional terms;
- multilingual terms where important;
- terms likely to retrieve graphic design materials from general museum APIs;
- terms likely to retrieve graphic design materials from library, newspaper, and periodical archives.

The vocabulary should support deterministic search first. Do not design this around AI search.

## 6. Rights and Indexing Strategy

For each source category, recommend a rights-safe indexing strategy.

Use categories:

- metadata only;
- link only;
- thumbnail only;
- IIIF/embed only;
- open image allowed;
- manual review required;
- do not ingest.

Explain how to avoid copyright conflict while still making the source discoverable.

## 7. Database Seed Output

Provide structured output that can later be transformed into:

- `historical_nodes.csv`;
- `movements.csv`;
- `media_technologies.csv`;
- `source_registry.csv`;
- `search_vocabulary.csv`;
- `rights_strategy.csv`.

Please include suggested column names for each CSV.

## 8. Deliverables

Please produce:

1. a historical node map;
2. a movement and formation taxonomy;
3. a medium/technology/format taxonomy;
4. an expanded source universe;
5. a rights-safe indexing strategy;
6. a search vocabulary;
7. suggested CSV schemas;
8. recommended Launch subset;
9. risks and gaps;
10. bibliography and source links.

The response should be rigorous, practical, and structured for implementation. It should support a project that first validates methodology and search framework, then builds the database, then designs the frontend, and only finally considers local packaged WebLLM as an optional search assistant.

# Deep Research Prompt: Conceptual Frontend Design for a Rights-Aware Graphic Design History Index

> **Superseded note (2026-05-29):** Do not run this prompt as-is. It was written before the launch-complete global coverage requirement and still uses phased/MVP language. It remains useful only as a generic IA, precedent, and accessibility supplement. After the global coverage baseline is accepted, rewrite the frontend/visual archive research prompt from the current database, coverage, rights, geography, date, and search contracts.

I am developing a project defined as:

**A rights-aware archive index and research framework for modern graphic design history.**

The project does not replace original archives, does not copy collections, does not build a course or textbook, and does not impose a single visual or historical narrative. It is a searchable, readable, citation-bound index that connects distributed works, texts, people, institutions, movements, media, technologies, places, and historical nodes back to their original sources.

## Context for This Research

**Already decided (Methodology v0):**

- Primary value: indexing over possession; metadata, citation, source links, rights status, classification, and search—not local image hoarding.
- Core principles: **integrity** (provenance, uncertainty, rights separation) and **reproducibility** (exports, schema, documented rules).
- Interface must serve **reading, search, and traceability**; it must not overperform as a spectacle of data visualization.
- **Required** UI areas: global search; historical spine / tree view; source registry; entity detail; source record detail; citation and rights panel; related records; filters/facets; uncertainty and provenance notes.
- **Optional** (later): lightweight graph, timeline, map, word frequency, corpus search, local WebLLM query assist.
- **MVP frontend scope:** global search, historical tree view, record detail page, related records panel—**no required WebLLM**.
- AI must not invent history, classify without review, decide rights, merge entities, or replace citations. WebLLM, if ever added, is browser-local and optional only.

**Parallel workstreams:**

1. **Database / backend (handled separately):** PostgreSQL canonical store; typed relations; source registry; rights states; ingestion logs; PostgreSQL full-text search; JSONL/CSV/SQLite export for reproducibility. Assume entity types such as WorkObject, Person, Organization, MovementPeriod, MediumTechnology, Place, TextPublication, Theme, Source, SourceRecord, ImageAsset, Assertion, Citation.
2. **Framework validation (separate Deep Research):** historical node map, movement taxonomy, source universe, search vocabulary—outputs may become CSV seed data.
3. **This research:** conceptual frontend design—information architecture, interaction patterns, visual direction, and UX rules—**before** high-fidelity implementation.

**Assume** framework Deep Research and database schema may be incomplete when you start. Design for the **method** and **MVP record model**, not for a fixed brand or final dataset size. Where data is uncertain, specify UI behavior for empty, partial, conflicting, or `possibly_same_as` states.

Do not write a general essay. Produce structured lists, tables, wireframe descriptions, component inventories, and decision records suitable for a design spec and later handoff to implementation.

---

## Research Goal

Produce a **conceptual frontend design package** for the public research index: how researchers, students, curators, and designers should **read, search, filter, cite, and return to source archives** without the interface implying ownership, canon, or a single historical story.

The output should be practical enough to become:

- an information architecture document;
- low-fidelity wireframe briefs (textual, screen-by-screen);
- a component and pattern library outline;
- UX writing / microcopy guidelines;
- accessibility and rights-display requirements;
- a phased UI roadmap aligned with MVP → Phase 2.

---

## 1. Comparable Systems and Design Precedents

Survey **15–25** existing projects, sites, or scholarly tools relevant to this product type. Include a mix of:

- museum and library collection search (e.g. V&A, Cooper Hewitt, Europeana, DPLA patterns);
- design-specific archives and indexes (e.g. Letterform Archive, Fonts In Use, People’s Graphic Design Archive—where public UI exists);
- humanities / linked-data / citation-first interfaces;
- archive aggregators and “window” indexes that link out rather than host media;
- **negative precedents**: timeline-heavy design history sites, graph-first explorers, AI-summary-first museum chat UIs, Pinterest-style visual feeds that obscure provenance.

For each precedent, provide:

- name and URL;
- product type;
- what it does well for **search, reading, citation, rights**;
- what it does poorly or what risks it introduces for **our** project;
- transferable patterns (with caution notes);
- relevance: **MVP inspiration**, **Phase 2**, or **avoid**.

End with a short **synthesis**: 5–8 non-negotiable UX lessons and 5–8 anti-patterns to avoid.

---

## 2. Primary Users, Tasks, and Success Criteria

Define **4–6** primary user types (e.g. design historian, studio practitioner, museum educator, graduate student, independent researcher, rights reviewer).

For each user type:

- goals when visiting the index;
- typical tasks (find object, compare sources, cite in writing, check image policy, explore a historical node, audit provenance);
- frustrations with existing tools;
- what “success” looks like in one session;
- what the interface must **not** trick them into believing.

Provide a **task → screen** matrix mapping top 12 tasks to required UI surfaces.

Define **MVP usability success criteria** aligned with methodology (e.g. user can cite a record in under 60 seconds; rights state visible without scrolling on mobile; source link always one click away).

---

## 3. Information Architecture

Propose a complete **site map** and **navigation model** for MVP and Phase 2.

Include:

- top-level sections;
- URL strategy principles (stable record URLs, facet state in query params vs path);
- how **historical spine**, **entity types**, **source registry**, and **search** relate in navigation;
- whether browse and search are peers or search-primary;
- how **external source institutions** appear in IA (not as “our collections”).

Deliver:

- site map (text tree);
- navigation rationale;
- recommended **homepage** purpose and modules for MVP;
- glossary / help / methodology pages needed for integrity.

---

## 4. Core Screens and Wireframe Briefs (Textual)

For each screen below, provide: **purpose**, **primary user**, **key modules**, **data dependencies**, **empty/error states**, **mobile vs desktop notes**, and **accessibility requirements**.

**MVP screens (required):**

1. Homepage / entry
2. Global search results
3. Historical spine / tree browse
4. Entity detail (WorkObject, Person, Organization, etc.—note variants)
5. Source record detail (external object page mirror)
6. Source registry list and source detail
7. Citation and rights panel (may be persistent drawer or section—justify choice)
8. Related records panel
9. Faceted filter UI (shared pattern)

**Phase 2 screens (outline only):**

10. Lightweight relation graph view
11. Timeline browse
12. Map / place browse
13. Text corpus / word-frequency explorer
14. Dataset export / about / changelog for reproducibility

Wireframe briefs should be **detailed enough** to sketch in Figma without inventing layout pixel-by-pixel: describe content hierarchy, sticky regions, and what must never be hidden.

---

## 5. Search Experience Design

Design the **search-first** experience for deterministic lexical search (not AI-first).

Specify:

- search box placement and behavior (instant vs submit, scope toggles);
- query syntax support (phrase, fielded search if any);
- result card fields and **“why matched”** snippets;
- sorting options (and which sorts are **disallowed** because they imply importance without basis);
- filters/facets: historical node, entity type, medium, place, source, rights status, date range, movement, theme;
- zero-results and low-confidence states;
- saved searches / shareable URLs (if recommended);
- how **rights filtering** works in UI (e.g. “show only link-only records”).

Provide **3–5** example search scenarios with expected result presentation (sample JSON fields acceptable).

---

## 6. Historical Spine / Tree Interaction

The historical spine is a **reading structure**, not a textbook chapter list.

Research and propose:

- tree vs outline vs nested list vs hybrid;
- how many levels deep for MVP;
- how nodes show counts without implying completeness;
- how records attach to multiple nodes;
- how to show **editorial vs source-derived** classification on nodes;
- revision/version messaging (“framework subject to change”);
- interaction between tree selection and search results.

Provide a recommended **default landing** behavior: spine-first vs search-first, with rationale.

---

## 7. Record Detail, Provenance, and Uncertainty UX

Define how the interface exposes **integrity** without clutter.

Required treatments:

- source name, source URL, access date, citation (human + machine-readable if shown);
- separation of **source metadata** vs **normalized local fields**;
- rights state (`metadata_open`, `link_only`, `thumbnail_only`, `image_embed_only`, etc.) and what displays for each;
- image display rules: embed, thumbnail, placeholder, external link only;
- uncertainty notes, confidence on relations, `possibly_same_as`;
- relation list grouped by predicate type;
- deprecated record state;
- last verified date;
- “return to source archive” as primary action hierarchy.

Provide **microcopy examples** (EN; note where zh-CN localization should be planned).

Provide **do / don’t** table for provenance display.

---

## 8. Rights, Attribution, and Legal Clarity in UI

Research how comparable projects surface rights without legal overload.

Deliver:

- rights panel content model;
- iconography vs text-only (recommendation);
- attribution line patterns for IIIF/embed/thumbnail;
- warnings when user might mistake index for rights holder;
- terms links and `RightsStatements.org` display patterns;
- researcher-facing “how to cite this index vs cite the source” guidance.

---

## 9. Visual and Typographic Direction (Conceptual Only)

This project should not look like a generic SaaS dashboard or a viral design portfolio.

Research and propose **3 distinct conceptual directions** (name each direction). For each:

- mood keywords;
- reference sites (non-copying);
- typography strategy (historical sensitivity without pastiche);
- color system roles (semantic: source, uncertainty, rights warning, external link);
- density preference (scholarly compact vs airy museum);
- image treatment when thumbnails exist vs link-only;
- motion principles (minimal vs none for MVP);
- what to avoid (gradient hero, infinite masonry, “AI sparkle”, ranking badges).

Recommend **one direction** for MVP with rationale tied to integrity and reading.

**Do not** produce final brand assets; produce a **concept board brief** implementers can follow.

---

## 10. Component and Pattern Inventory

List reusable UI components for implementation:

- search bar, result card, facet chip, spine tree node, entity header, relation row, citation block, rights badge, source badge, uncertainty callout, external link button, empty state, deprecated banner, export link, version footer.

For each component:

- purpose;
- required props/fields (map to data model conceptually);
- states (default, loading, error, partial, restricted);
- accessibility notes (ARIA roles, keyboard).

---

## 11. Responsive, Performance, and Offline-Adjoining Behavior

Specify:

- mobile-first constraints for citation and rights (must remain visible);
- performance expectations for search (skeleton vs pagination);
- handling large relation lists;
- optional offline use via exported SQLite snapshot (if UI should mention it);
- image lazy-load and failure behavior;
- no WebGPU / WebLLM dependency in MVP layouts.

---

## 12. Accessibility, Internationalization, and Scholarly Usability

Cover:

- WCAG-oriented requirements for search and tree;
- keyboard navigation for spine and facets;
- readable typography for long metadata sessions;
- language strategy (UI in EN first? bilingual metadata display?);
- diacritics and non-Latin names in search;
- print-friendly record view or export for footnotes;
- screen reader behavior for external links and rights warnings.

---

## 13. Content Design and Tone

Define voice principles: restrained, methodological, non-canonical.

Provide:

- labels for entity types and relation types (consistent with methodology predicates);
- how to phrase “we do not know” and low confidence;
- homepage explanatory copy (short);
- about/methodology page outline;
- error messages that do not blame the user for sparse data.

---

## 14. Phase Roadmap and MVP Cut Line

Produce a table:

| Feature | MVP | Phase 2 | Later | Notes |
|---------|-----|---------|-------|-------|

Explicitly mark **out of scope** for MVP: graph as hero, map, word frequency, WebLLM, social features, user accounts, comments, ranking feeds, image galleries without rights.

Align with implementation order: **search + detail + rights/citation before graph/timeline**.

---

## 15. Handoff Artifacts for Engineering (Codex / Dev)

Assume PostgreSQL + API or SSR frontend will be built after this research.

Provide:

- recommended **frontend architecture** options (e.g. static site + API, Next.js SSR, etc.) with tradeoffs for a citation-heavy index—no final lock required, but decision criteria;
- API/UI contract notes: which fields each screen needs;
- suggested **design tokens** structure;
- open questions requiring database team input;
- risks if UI is built before seed data exists (mitigations).

---

## 16. Deliverables Checklist

Please produce all of the following:

1. Comparable systems analysis table
2. User types and task matrix
3. Site map and navigation model
4. Textual wireframe briefs for MVP screens (9+)
5. Search UX specification
6. Historical spine interaction specification
7. Provenance/uncertainty/rights UX specification with microcopy samples
8. Three visual directions + one MVP recommendation
9. Component inventory
10. Accessibility and i18n notes
11. Phase roadmap table
12. Engineering handoff notes
13. Top 10 open questions and recommended user tests (low-cost)
14. Annotated bibliography and URLs

---

## Output Format Requirements

- Use headings, tables, and bullet lists throughout.
- When recommending a pattern, state **tradeoffs** and **why it fits a rights-aware index**.
- Flag anything that risks implying **ownership**, **canon**, **influence**, or **AI authority**.
- Prefer decisions that keep the interface **readable before impressive**.
- Where useful, include ASCII wireframe sketches in code blocks.
- Optional: suggest filenames for design docs (e.g. `IA_v0.md`, `WIREFRAMES_MVP_v0.md`, `UX_WRITING_v0.md`).

The response should be rigorous, practical, and structured for a design phase that precedes high-fidelity UI implementation. It should complement—not duplicate—the framework validation Deep Research focused on historical nodes, sources, and CSV seed data.

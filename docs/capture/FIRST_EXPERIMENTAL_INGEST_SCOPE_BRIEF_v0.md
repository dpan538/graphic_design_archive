# First Experimental Ingest Scope Brief v0

**Status:** Planning bridge before new Deep Research.

This brief records why another Deep Research pass is needed before actual crawling.

## Reason

The database now has a global coverage skeleton and a source/rights policy skeleton. The next missing decision is not "can we crawl?" but "what should the first controlled ingest represent?"

The first ingest must not become a convenience sample of open Western museum APIs. It needs to test whether the framework can hold:

- canonical and noncanonical modernism;
- commercial, editorial, typographic, political, vernacular, and digital materials;
- Europe, the U.S., Japan, Korea, China, Latin America, South Asia, Southeast Asia, MENA, Africa, and Oceania/Pacific;
- records with images and records that must stay link-only;
- source-language metadata and authority ambiguity;
- event-based, movement-based, person-based, institution-based, and medium-based classification.

## Current Constraint

The first ingest should be small enough to review manually, but broad enough to test the system.

Working assumption before research:

- 36-60 source records;
- 12-18 movements/formations;
- 10-16 event nodes;
- 10-14 sources;
- image states represented across `IMG00` through `IMG03`, with `IMG04` available for pure text/continuation pages;
- majority of historically sensitive records remain `IMG00`.

This is not a reduced project scope. It is a test set for the database and interface grammar.

## Research Prompt

Use:

- `prompts/DEEP_RESEARCH_FIRST_INGEST_SCOPE_PROMPT.md`

## Expected Decision From Report

The report should tell us:

- which movements/events must be included in the first ingest;
- which sources should be used for each;
- which records are safe for metadata-only, link-only, thumbnail, IIIF/embed, or open-image handling;
- which seed files need patching before ingest;
- whether source terms review is enough to begin the first controlled ingest.

## Current Bias Warning

The project already contains global coverage seed rows, but the active experimental shortlist is still source-behavior oriented. It tests `IMG00` through `IMG03`, but it does not yet guarantee that the first ingest represents the historical and geographic breadth of the framework.

The next Deep Research pass should therefore evaluate movement/event coverage, not only source feasibility.

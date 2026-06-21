# Research Packet Structure Method v1

Status: pre-rebuild methodology contract  
Date: 2026-06-21

This method defines the final-phase archive structure for research packets.
The project is no longer primarily in source-expansion mode. The main task is
to organize existing surfaces into readable, rights-aware research packets
without forcing weak or unresolved records into stronger roles.

## 1. Core Principle

A research packet is not a flat sequence of pages. It is a curated tree with
node-level explanation and optional text-page expansion.

The packet tree can contain:

```text
cover_main
  normal_main
    text
    sub_sheet
      text
      card
      appendix
        text
        card
    appendix
      text
      card
```

Text pages are pure explanatory pages. They carry extended writing, but they
do not replace the need for every structural node to explain itself.

## 2. Node Types

### Cover Main

`cover_main` is the first page of a research packet. It is the packet's curated
entry point and should explain:

- packet title and scope;
- period span and actual captured years;
- region or global/transnational scope rationale;
- source-family logic;
- rights/image-state summary;
- why the packet exists;
- recommended reading path;
- unresolved relation or classification questions.

A cover main is not necessarily a single design object. It may anchor a topic,
series, project, institution, movement, source-family packet, global platform,
or cross-border design context.

### Normal Main

`normal_main` is a research-bearing node inside a packet. It may represent a
specific work, project, institution, series member, issue, campaign, or
significant source object. It can have its own text pages and does not need to
be demoted just because a cover main organizes it.

Normal main pages can have:

- direct text pages;
- sub sheets;
- appendices;
- cards.

### Sub Sheet

`sub_sheet` is a strong relation node below a normal main. A sub sheet should
exist only when the relation is explicit enough to explain:

- member of same project, campaign, series, issue, exhibition, movement,
  studio, school, institutional program, or source-side grouping;
- variant, companion, support work, or related object in the same packet;
- regional/period/theme sub-branch with clear packet relevance.

Same source platform, same year, or same broad region is not enough.

Each sub sheet should have at least one child text page, card, or appendix.

### Text Page

`text` is pure explanatory writing. It can attach to cover main, normal main,
sub sheet, or appendix. Text pages can contain:

- historical context;
- design analysis;
- source relation;
- rights/display note;
- classification rationale;
- editorial annotation;
- uncertainty note;
- reading guide;
- global/transnational scope rationale.

Text is not the only place where explanation exists. Each node still needs a
short node summary and relation note.

### Appendix

`appendix` carries evidence that is weaker than sub-sheet membership or too
detailed for the main reading path. It may attach to normal main or sub sheet.
Appendix nodes may have their own text pages and cards.

Appendix is appropriate for:

- source register evidence;
- rights evidence;
- OCR/source text;
- metadata;
- bibliography/citation trails;
- alternate source evidence;
- unresolved relation notes;
- object evidence too thin for sub-sheet status.

Appendix is not a dumping ground for failed records. It should still explain
why the evidence matters.

### Card

`card` is the smallest visual or excerpt unit. It usually contains an image,
title, source cue, small note, or lightweight context. Cards are usually leaf
nodes below sub sheets or appendices.

Cards are appropriate for:

- pure visual evidence;
- image/title records;
- event/context photographs;
- weak profile snippets;
- related but non-anchor material;
- small source excerpts.

## 3. Minimum Packet Shape

Every mature packet should have:

- one cover main;
- at least one normal main or one main group;
- each normal main should have at least one sub sheet unless it is explicitly
  marked as a standalone object packet;
- each sub sheet should have at least one text, card, or appendix;
- appendix may have text and card children.

Recommended minimum text targets:

| Packet scale | Structure target | Minimum text target |
|---|---:|---:|
| Small packet | 1 normal main, at least 1 sub | about 2 text pages |
| Medium packet | 3-5 sub sheets | about 5-8 text pages |
| Large packet | 10+ sub sheets | about 15 text pages |

Medium and large packets must have at least one editorial page. Small packets
may also have an editorial page when the source text is thin or the relation is
curatorially important.

## 4. Node-Level Explanation

Every non-card node should expose node metadata:

```text
node_title
node_type
node_summary
relation_to_parent
source_basis
scope_policy
confidence_status
children
text_pages
```

This is separate from text pages. The node summary should be short enough for
the packet tree and folder directory.

## 5. Folder Directory

Folder directory should stop behaving like an engineering register. It should
be a reader-facing packet index.

It should show:

- cover main;
- normal main nodes;
- sub sheets;
- appendices;
- card counts;
- text counts;
- global/region scope;
- source family;
- rights/image state;
- packet confidence;
- unresolved flags.

The folder directory should reveal packet structure without requiring the user
to open every page.

## 6. Reading Note

Reading note is curated editorial material. It is not a bookmark, not a raw
folder register, and not an engineering status message.

A reading note should explain:

- what this folder or packet helps the reader study;
- why the packet is organized this way;
- where to start reading;
- which nodes are core;
- which nodes are appendix/card evidence;
- which relations remain uncertain;
- why global/transnational scope is accepted or still under review;
- how rights/image state affects visual reading.

Large and medium packets should have a dedicated editorial reading note page.
Small packets may have one when the content is sparse but the packet needs
curatorial framing.

## 7. Global / Transnational Scope

Global/transnational scope is a valid archive category. A contemporary graphic
design archive with no global platforms, organizations, networks, or
cross-border design contexts would be suspicious.

Do not force country assignment when:

- the source platform is a cross-border contemporary showcase;
- the organization is explicitly international or transnational;
- the project, movement, network, or publication is not country-bound;
- the source-side evidence frames the work globally.

However, global scope must not hide unresolved metadata. Use:

- `global_site_acceptable_with_relation_review` for contemporary showcase or
  design-network sites;
- `global_host_requires_scope_review` for aggregator/host platforms where
  global may mean unresolved region;
- `region_specific_or_not_global` when region is sufficiently specific;
- `global_scope_manual_review` when no safe policy exists yet.

## 8. Frontend Contract

The frontend should eventually support:

- Content panel as packet tree;
- Context as optional visual relation view;
- Reading note as curated editorial guide;
- Text pages as extended prose;
- Appendix nodes with their own text/card children;
- Card leaves;
- Cover main vs normal main distinction;
- Global/transnational scope markers;
- actual year span separate from five-year bucket grouping.

WebLLM is not required for this structure. A functional search/navigation
assistant can operate over packet metadata, reading notes, source summaries,
and node relations.

## 9. Safety

This method does not authorize:

- image downloads;
- rights upgrades;
- IMG01/IMG03 upgrades;
- source-authority upgrades;
- forced country assignment;
- automatic main-to-sub demotion;
- automatic packet creation from source platform alone.

All packet roles remain reviewable until rebuild and frontend contract checks
pass.

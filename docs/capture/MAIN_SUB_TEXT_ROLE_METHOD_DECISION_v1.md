# Main/Sub/Text Role Method Decision v1

Scope: project method decision for page-role review after the rights-aware
methodology deep research report.

This document is a methodology layer. It does not rebuild surfaces, does not
apply overrides, does not download images, and does not change rights or image
states.

## Decision Position

The project should continue with a packet-first, rights-aware role system.
Main sheets should be treated first as provisional research-packet anchors and
only secondarily as object pages. The project should not bulk-demote main
sheets, and it should not preserve every image-bearing object as a main sheet.

The next safe action is a structured validation review, followed only by a
small sandbox override test for high-confidence, low-risk role changes.

## Method Sources

This decision synthesizes:

- The project prefreeze method discussion and 320-row validation packet.
- The deep research report: `Rights Aware Methodology for a Graphic Design
  Archive.docx`.
- Archival principles from multilevel description and evidence transparency.
- Work/image/source separation used by visual-resource description.
- Rights-aware display discipline: source visibility and rights evidence are
  publication gates, not automatic role or image-state boosters.

## Page Role Taxonomy

### Main Sheet

A main sheet is the smallest publishable unit that can honestly anchor a
research claim and organize adjacent evidence without misleading the reader.

It may be:

- a single work with clear standalone design-historical force,
- a project or campaign,
- a series, issue, or periodical packet,
- a studio, institution, or source-rich packet,
- a regional or scarcity packet,
- a movement/theme/visual-language packet when the inclusion rule is explicit.

Main status requires at least one of:

- strong relation density,
- source depth,
- impact or representativeness,
- visual/design specificity,
- movement/theme relevance,
- region scarcity with transparent caution,
- clear editorial need that can support non-filler text.

Main status must not be granted just because an object has an image, appears in
a prestigious source, or belongs to a large API/source family.

### Sub Sheet

A sub sheet is a substantial object/source record that gains meaning under a
stronger parent packet. Sub status is structural, not a judgment that the work
is historically unimportant.

Typical sub relations:

- variant of,
- issue of,
- campaign member,
- series member,
- source-cluster counterpart,
- regional instance,
- project component,
- periodical/page component.

### Text Sheet

A text sheet is an interpretive page. It should explain why a packet exists,
how its members relate, what evidence supports that grouping, what cannot be
claimed safely, and how rights/source limits affect interpretation.

Text is required when metadata alone cannot explain the packet. It is not
required merely to raise text-page counts.

### Card

A card is a lightweight contextual witness. It keeps useful context visible
without making the item carry packet-anchor authority.

Common card cases:

- event photographs,
- memory documentation,
- supporting people/institution notes,
- repeated views,
- minor contextual documents,
- weak but useful source witnesses,
- commemorative traces when not themselves the design object under study.

### Appendix

An appendix holds evidence and control material that should remain available
without interrupting the reading path.

Common appendix cases:

- rights evidence,
- provenance notes,
- source indexes,
- typed indexes,
- API verification,
- metadata verification,
- description assertion evidence,
- legal/reuse caution.

## Research Packet Anchor Score

The score is a review-assist and triage tool only. It is not an autopublisher,
not a rights upgrader, and not an image-state upgrader.

Positive factors:

- relation density,
- source depth,
- impact or representativeness,
- visual/design specificity,
- movement/theme relevance,
- period span or historical rupture,
- region scarcity,
- editorial need,
- source authority and corroboration.

Gate or ceiling factors:

- rights state,
- source visibility,
- image state,
- object/source distinction.

Penalty factors:

- duplicate or variant risk,
- event/photo/stamp risk,
- geography ambiguity,
- weak Commons-only file evidence,
- source-family overdominance,
- natural-history/geology drift,
- contemporary platform/studio cluster shallow evidence.

## Role Decision Sequence

1. Identify the descriptive unit: work, project, series, issue, campaign,
   institution packet, regional packet, source witness, or evidence record.
2. Separate object, image surrogate, source page, institution/provider, and
   rights/provenance evidence.
3. Confirm minimal source and rights evidence. This step can block publication
   but cannot upgrade role or image state.
4. Decide whether the record functions as packet anchor or packet member.
5. Assess text need by complexity, not by word count.
6. Assign one role outcome and record rationale, confidence, relation type, and
   blocker class.

## Role Outcomes

| Outcome | Use when | Minimum evidence | Do not use when |
| --- | --- | --- | --- |
| `keep_main` | Record already anchors a coherent research claim or packet. | Clear identity, source-visible evidence, explicit rights posture, strong relation or standalone justification. | Main exists only because an image exists. |
| `main_needs_text` | Anchor is valid but cannot be honestly read without interpretive context. | Same as keep_main, but interpretive frame is missing. | Text would only restate metadata. |
| `sub_under_packet` | Record is substantial but structurally dependent on a stronger packet. | Candidate parent and relation type can be stated. | No meaningful parent exists yet. |
| `card_context` | Record is a contextual witness rather than argument-bearing anchor. | Source-visible useful context. | Material is primarily evidentiary/legal. |
| `appendix_evidence` | Material verifies or controls interpretation. | Rights/provenance/source/API/index evidence. | Reader needs it as narrative context first. |
| `manual_hold` | Ambiguity is too high for safe assignment. | Blocker can be named. | Team is tempted to infer rights, geography, objecthood, or parentage. |
| `exclude_or_deprioritize` | False positive, duplicate-noise, or too weak for current release priority. | Evidence justifies exclusion/deprioritization. | Exclusion would hide a real research path. |

## Text Sheet Complexity Index

Start every candidate packet at zero. Add one point for each:

- non-trivial relation density,
- span across more than one decade or historical rupture,
- more than one major source family,
- regional scarcity or contested place assignment,
- rights/provenance caution that materially limits interpretation,
- movement/theme complexity,
- source-family or duplicate caution that requires explanation.

Interpretation:

- 0: no separate text required unless reviewer adds a reason.
- 1-2: one text sheet or integrated interpretive note.
- 3-4: one to two text sheets.
- 5+: reconsider packet design before adding more text; the argument may be too
  fragmented.

Every text sheet should answer:

- What is the packet about?
- Why is it grouped this way?
- What evidence supports the grouping?
- What cannot yet be claimed safely?
- How should the reader use the sources and rights information?

## Manual-Only Blocker Classes

The following classes should not be automatically converted into main/sub/text
roles without review:

- rights-sensitive upgrades,
- image-state upgrades,
- contested or transnational geography,
- weak Commons-only object pages,
- event/photo/memory documentation,
- stamps and commemorative records,
- natural-history/geology false positives,
- duplicate or migrated image variants,
- contemporary platform/studio clusters with shallow historical context,
- underdocumented region records where source depth is thin but scarcity is
  high.

## Automation Boundary

Allowed for high-confidence suggestions:

- `appendix_evidence` for source/rights/API/index evidence.
- `card_context` for obvious contextual witnesses.
- `sub_under_packet` only when a parent and relation type are explicit.

Not allowed:

- keep-main decisions,
- rights upgrades,
- image-state upgrades,
- contested geography normalization,
- broad source-family packetization,
- non-main demotion based only on short text.

## Validation Thresholds Before Sandbox Override

Before any sandbox role override test:

- At least 25% of the validation packet should be calibrated by manual or
  second-pass review.
- Role agreement target: about 80% or better on reviewed rows.
- Method fail target: 10% or below.
- Main-sensitive lanes must pass stricter review than support/card lanes.
- Any recurring failure in rights inference, image-state inference, regional
  unfairness, source-family bias, duplicate handling, event/photo records, or
  stamp records pauses the pilot.

## Current Project Decision

The method is strong enough for initial review and candidate scoring. It is not
yet strong enough for broad role reassignment. The next step is to run an
initial Codex review of the 320-row packet and produce a high-confidence
sandbox-candidate list. Only that list may be considered for a small test.

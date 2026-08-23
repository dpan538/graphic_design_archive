# Context Governance v1 validation

## Frozen meaning

The public epistemic role is `project_curated_context`. The three allowed kinds are `medium`, `theme`, and `movement_context`. Publication state is independent of the immutable source state: all 16,106 governed public representations are `published`, while every source candidate remains `proposed`.

This separation prevents a Context publication decision from becoming a `TraceSemanticEdge`, accepted historical fact, or assertion of historical movement membership. The governed connection kind is `context_representation`, with registry-controlled wording `classified as`, `themed as`, and `curated within`.

## Registry and assignment audit

| Kind | Terms | Representations | Object coverage | Same-kind multi-value objects | Published | Qualified | Held | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Medium | 10 | 7,995 | 7,995 | 0 | 7,995 | 0 | 0 | 0 |
| Theme | 8 | 7,996 | 7,995 | 1 | 7,996 | 0 | 0 | 0 |
| Movement context | 7 | 115 | 110 | 5 | 115 | 0 | 0 | 0 |
| Total | 25 | 16,106 | 7,995 | 6 | 16,106 | 0 | 0 | 0 |

All unique terms, same-kind multi-value structures, abnormal labels, near concepts, identity conflicts, and movement structures received explicit review. The collision and normalization review found zero same-ID conflicting labels, duplicate-label identities, case-only variants, punctuation-only variants, whitespace variants, malformed labels, or exact/normalized cross-kind reuse. Candidate near concepts remain distinct because their kinds, source identities, and permitted meanings differ.

All 115 movement rows were audited across seven terms. Each decision is `PUBLISH_AS_PROJECT_CURATED_CONTEXT`; none authorizes definitive historical membership, affiliation, influence, contact, causation, chronology, rank, or inter-record relation.

## Explanations and provenance

Every visible representation resolves exactly one of `CTX-MEDIUM`, `CTX-THEME`, or `CTX-MOVEMENT`. The registry supplies definition, why shown, source basis, permitted interpretation, prohibited interpretations, connection language, accessibility wording, and policy version. Governed visual, inspector, accessible-row, and export structures consume this registry rather than deriving scholarly meaning from labels.

Each representation also resolves a public provenance record with basis `project_curated_typed_membership`, safe source kind, source state `proposed`, mapping-policy version, governance-policy version, and governance decision. Raw folder identity, internal UUID, source locator, and membership-node duplication are prohibited.

```text
UNEXPLAINED_VISIBLE_NODE_COUNT=0
UNRESOLVED_EXPLANATION_CODE_COUNT=0
PROVENANCE_RESOLUTION_FAILURE_COUNT=0
PUBLIC_ID_COLLISION_COUNT=0
```

## Field and domain decisions

Every Context-adjacent field has an explicit disposition. Safe title, surface ID, source-reported attribution, object type, date display, and source name orient the selected-record root without becoming nodes or edges. Typed medium, theme, and movement become controlled representations. Their source memberships are explanation/provenance only. Raw medium, source detail, descriptions, notes, and subjects remain source/provenance concerns. Images, rights, and semantic topology are excluded.

All 7,996 public typed region rows, covering 93 region terms on 7,995 records, are `DEFER_TO_SPACETIME`. Context creates zero region nodes, performs no geographic normalization, and adds no Spacetime implementation.

## Required invariants

The authoritative governance verifier reports `PASS` for all 22 required invariants. The machine-readable evidence contains aggregate counts and sanitized failure registers only; it contains no source-row dump, raw folder identity, UUID, or held identity.

## Decision

`CONTEXT_V1_DECISION=CONTEXT_V1_CLOSED`

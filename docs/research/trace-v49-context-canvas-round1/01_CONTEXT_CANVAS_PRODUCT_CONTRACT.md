# Context Canvas Product Contract

Normative terms `MUST`, `MUST NOT`, and `SHOULD` define the functional contract for `/trace/context-canvas`.

## Inputs and ownership

- The semantic input MUST be a read-only `TraceContextDataset` or a backward-compatible extension.
- The prototype MUST use a synthetic, public-safe fixture marked `fixtureKind=synthetic-contract-only`, `historicalEvidence=false`, and `publicReleaseData=false`.
- The fixture MUST contain neutral labels and no internal UUID, held/private record, private URL, raw payload, or fabricated real-object claim.
- Composition state MUST contain only UI-owned values: template identity, visible stable entity IDs, world positions, selection, viewport, and history.
- Canonical entities and connections MUST NOT be copied into persistence or mutated by a reducer, renderer, inspector, or export path.

## User capabilities

The user MAY choose a template; add an available entity by button, keyboard, or palette drag; move a visible entity; hide a non-root entity; select one entity or connection; inspect metadata; pan; zoom; fit; auto-arrange; reset the view; reset the canvas; undo/redo composition changes; and export the full composition as PNG.

The user MUST NOT create or edit canonical entities, archival fields, assignments, memberships, predicates, semantic edges, or evidence. There is no connection handle, freehand edge gesture, `Add Relationship` command, editable relation label, review action, server mutation, or database write.

## Entity contract

Each canvas node is keyed by the entity's stable public reference and reads its label and kind from the dataset. Exactly one node may exist per stable entity ID. The selected archive object is the root node, is always present, and cannot be hidden.

Adding a hidden entity changes only visibility and position. Adding an already visible entity MUST select/focus the existing node without adding a duplicate or history entry for semantic data. Hiding returns the entity to the palette and hides its incident rendered connections while leaving the dataset intact.

## Connection contract

| Rendered category | Source type | Endpoints | Inspector minimum | Meaning constraint |
|---|---|---|---|---|
| `controlled_assignment` | `TraceControlledAssignment` | `subject` → `value` | assignment type, state, subject, value | Descriptive assignment; not a semantic relation |
| `curated_membership` | `TraceCuratedMembership` | `member` → `container` | membership type, state, member, container | Curated containment/pathway; not a semantic relation |
| `semantic_edge` | accepted `TraceSemanticEdge` | `subject` → `object` | predicate ID, accepted status, evidence-reference count | Explicit registered predicate only |

For every dataset connection `c`, rendering is the pure predicate:

```text
render(c) = visible(endpointA(c)) AND visible(endpointB(c))
```

The UI MUST never infer a connection from proximity, shared values, co-occurrence, palette activity, or geometry. Each rendered connection retains its source category and stable canvas connection ID. Synthetic contract fixtures may exercise all three categories; they MUST NOT be represented as historical evidence.

## Composition behavior

- Template application MUST produce a deterministic initial composition and replace, not merge with, positions from the previous template.
- Add, hide, committed node move, template change, and auto-arrange MUST create bounded history entries.
- Pointer movement during a drag MUST preview continuously but create one history entry at drag end.
- Pan and zoom MUST NOT enter composition history.
- Exactly zero or one primary item is selected; selection stores `{kind, id}`, never an object copy.
- Background selection clears the primary selection.
- Active template switching MUST cancel transient drag or pan state before applying the new composition.

## Inspector and equivalent representation

For an entity, the inspector shows only verified available fields: display label, entity kind, stable public reference, availability/state when present, and canvas status. Connection panels show only the category-specific fields in the table above. The inspector MUST NOT synthesize scholarly explanation.

The dataset's `accessibleRows` is the semantic reference representation. Every visible semantic connection MUST have a corresponding accessible row; the graphical SVG MUST not be the only way to understand the dataset.

## Persistence and reset

Persistence is local-browser-only and versioned by release manifest, selected stable record ID, Context Canvas schema version, template ID, and template version. It may store visible stable IDs, finite world positions, selected template, and a finite viewport. It MUST reject incompatible versions, unknown/private IDs, duplicates, non-finite values, and invalid zoom, then initialize from the current template.

`Reset View` changes only the viewport. `Reset Canvas` clears the current workspace's saved composition and reapplies the current template. Neither action changes source data.

## Route and release boundary

The route is unlinked, noindex, and clearly labeled as a functional prototype. It MUST NOT alter current `/trace`, global navigation, ArchiveShell, Search, legacy TRACE v48, or canonical release artifacts. It MUST NOT import Search, AI, embeddings, maps, Spacetime, or Exploration Field code.

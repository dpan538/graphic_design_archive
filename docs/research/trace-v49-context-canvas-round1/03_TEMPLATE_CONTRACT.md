# Context Canvas Template Contract

## Interface

Each template is an immutable registry entry with:

```ts
interface ContextCanvasTemplate {
  readonly templateId:
    | "context-overview"
    | "descriptive-context"
    | "curated-context"
    | "full-context";
  readonly version: 1;
  readonly label: string;
  readonly description: string;
  readonly selectEntityIds: (dataset: TraceContextDataset) => readonly string[];
  readonly initialLayout: "typed-lanes-v1";
  readonly defaultZoomBehavior: "fit-content";
}
```

`templateId` and `version` are persistence identities, not translated display strings. A version changes only when the selection or initial-layout result can change for the same dataset.

The default template is `context-overview` version `1`.

## Registry

| Template ID | Selection rule | Initial lanes | Default view |
|---|---|---|---|
| `context-overview` | Root plus all eligible context entities when the dataset has at most nine associations; above that envelope, root plus a stable representative set from controlled assignments and curated memberships | root, controlled, curated, semantic if selected | Fit all selected nodes with padding |
| `descriptive-context` | Root plus endpoints of all eligible controlled assignments | root, controlled | Fit all selected nodes with padding |
| `curated-context` | Root plus endpoints of all eligible curated memberships | root, curated | Fit all selected nodes with padding |
| `full-context` | Root plus endpoints of every eligible controlled assignment, curated membership, and accepted semantic edge | root, controlled, curated, semantic | Fit all selected nodes with padding |

At the measured v49 maximum (nine associations), `context-overview` intentionally selects all eligible items and may equal `full-context`. The distinction remains stable for future governed datasets. If the overview exceeds the envelope, representatives are selected by category, then stable connection ID, with balanced category inclusion before filling the remaining budget; no score, randomness, or semantic inference is allowed.

## Eligibility

Only entities and connections already present in the supplied public-safe dataset are eligible. Hidden, held, private, unpublished-to-the-projection, or unknown external endpoints are excluded. The root selected record is always first and cannot be excluded. A semantic edge is eligible only if supplied as an accepted `TraceSemanticEdge`; templates never manufacture one.

## Determinism

Initialization MUST:

1. derive the eligible connection subset without mutating or reordering source arrays;
2. collect endpoint stable IDs and de-duplicate by stable ID;
3. place the root first;
4. classify remaining entities by their source connection category;
5. stable-sort each lane by normalized display label, then stable ID;
6. call the pure `typed-lanes-v1` layout;
7. derive visible connections from the dataset and visible endpoint set;
8. compute the default fit viewport from known node bounds.

The same dataset bytes, template ID, and template version MUST yield deep-equal visible IDs, positions, connection geometry, and initial viewport. No random value, clock, DOM measurement, insertion order, or prior persisted position participates.

## Switching and reset

Selecting a different template cancels active pointer interactions, commits one history transition, and replaces the visible set, positions, selection, and default viewport with the target template output. It MUST NOT merge old positions into the new template. Undo may restore the complete prior composition snapshot.

`Reset Canvas` deletes only the current persistence key and reapplies the currently selected template version. A persistence schema/template-version mismatch performs the same safe reinitialization automatically.

Template labels, descriptions, and provisional coordinates are redesignable. IDs, semantic selection boundaries, determinism, and reset behavior are functional contracts.

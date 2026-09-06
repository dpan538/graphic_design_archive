import "server-only";

import { createHash } from "node:crypto";
import explanationRegistryJson from "../../../../../generated/trace-context-v1/explanation-registry.json";
import type {
  PublicContextDataset,
  PublicContextExplanation,
  PublicContextRepresentation,
  PublicContextRepresentationKind,
} from "@/features/trace-v49/context/governed/types";

/* Context Canvas — the fixed synthetic stress fixture (§7g), for LAYOUT
   TESTING ONLY. Development builds serve it at ?state=stress and
   ?state=stress-missing. It borrows nothing from any archive object: a
   long title, a long attribution, a long type string; four Medium terms
   (one long), six Theme terms (two long), three Movement terms — or none,
   in the "missing" variant. Its identifiers are well-formed but derived
   from the word "stress", its labels say what they are, and the page
   carries a banner: it is not a production record and not a claim that
   any object carries this composition. The release identity is taken
   from the real dataset it is built on and the governed explanations
   from the projection's own registry (all three kinds, whatever the base
   record carries), so the adapter's contracts hold. */

export type StressVariant = "full" | "missing";

const KIND_TAG: Readonly<Record<PublicContextRepresentationKind, "MEDIUM" | "THEME" | "MOVEMENT">> = Object.freeze({
  medium: "MEDIUM",
  theme: "THEME",
  movement_context: "MOVEMENT",
});
const SOURCE_KIND: Readonly<Record<PublicContextRepresentationKind, "medium" | "theme" | "movement">> = Object.freeze({
  medium: "medium",
  theme: "theme",
  movement_context: "movement",
});
const EXPLANATION_CODE: Readonly<Record<PublicContextRepresentationKind, string>> = Object.freeze({
  medium: "CTX-MEDIUM",
  theme: "CTX-THEME",
  movement_context: "CTX-MOVEMENT",
});

const LABELS: Readonly<Record<PublicContextRepresentationKind, readonly string[]>> = Object.freeze({
  medium: Object.freeze([
    "Stress medium 1 — poster",
    "Stress medium 2 — portfolio cover",
    "Stress medium 3 — an intentionally long medium label written to test how a term wraps inside a chip on the canvas",
    "Stress medium 4 — letterhead",
  ]),
  theme: Object.freeze([
    "Stress theme 1 — commercial communication",
    "Stress theme 2 — an intentionally long theme label written to test wrapping, clamping and the inspector's heading",
    "Stress theme 3 — typographic experiment",
    "Stress theme 4 — another intentionally long theme label, long enough to run to a third line in a dense band",
    "Stress theme 5 — civic graphics",
    "Stress theme 6 — public information",
  ]),
  movement_context: Object.freeze([
    "Stress movement 1 — a synthetic movement context",
    "Stress movement 2 — another synthetic movement context",
    "Stress movement 3 — a third synthetic movement context",
  ]),
});

const hex = (seed: string) => createHash("sha256").update(`stress-fixture:${seed}`).digest("hex");

function representation(kind: PublicContextRepresentationKind, label: string, index: number): PublicContextRepresentation {
  const termId = `CTX:${KIND_TAG[kind]}:${hex(`term:${kind}:${index}`)}`;
  return Object.freeze({
    id: `CTXA:${hex(`representation:${kind}:${index}`)}`,
    kind,
    termId,
    label,
    epistemicRole: "project_curated_context",
    publicationState: "published",
    explanationCode: EXPLANATION_CODE[kind],
    provenance: Object.freeze({
      provenanceId: `CTXP:${hex(`provenance:${kind}:${index}`)}`,
      basis: "project_curated_typed_membership",
      sourceKind: SOURCE_KIND[kind],
      sourceState: "proposed",
      mappingPolicyVersion: "trace-context-governance-mapping-v1",
      governancePolicyVersion: "context-governance-v1",
      decision: "PUBLISHED",
    }),
  });
}

export const STRESS_STABLE_ID = "SURF-STRESSFIXTURE0001";

export function buildStressFixture(base: PublicContextDataset, variant: StressVariant): PublicContextDataset {
  const kinds: PublicContextRepresentationKind[] = variant === "missing"
    ? ["medium", "theme"]
    : ["medium", "theme", "movement_context"];
  const representations = Object.freeze(kinds.flatMap((kind) =>
    LABELS[kind].map((label, index) => representation(kind, label, index))));
  const registry = (explanationRegistryJson as unknown as { entries: readonly PublicContextExplanation[] }).entries;
  const explanations = Object.freeze(kinds.map((kind) => {
    const entry = registry.find((e) => e.explanationCode === EXPLANATION_CODE[kind]);
    if (!entry) throw new Error(`Stress fixture: the registry has no explanation for ${kind}.`);
    return entry;
  }));
  const explanationByCode = new Map(explanations.map((e) => [e.explanationCode, e]));
  const title = "Stress fixture — an intentionally long selected-object title written to test the canvas, the rail and the inspector";
  return Object.freeze({
    ...base,
    selectedRecord: Object.freeze({
      surfaceId: STRESS_STABLE_ID,
      title,
      rootMetadata: Object.freeze({
        creatorAttribution: "Stress attribution — a long synthetic attribution string with several names; not a person in the archive",
        objectType: "stress object type; an intentionally long, semicolon-separated synthetic type string; for layout testing only",
        dateDisplay: "1900–1999 (synthetic)",
        sourceName: "Synthetic stress fixture (no source institution)",
      }),
    }),
    availability: "ready",
    representations,
    explanations,
    counts: Object.freeze({
      representations: representations.length,
      byKind: Object.freeze({
        medium: representations.filter((r) => r.kind === "medium").length,
        theme: representations.filter((r) => r.kind === "theme").length,
        movementContext: representations.filter((r) => r.kind === "movement_context").length,
      }),
    }),
    accessibleRows: Object.freeze([
      Object.freeze({
        id: `selected:${STRESS_STABLE_ID}`,
        category: "selected_record" as const,
        label: title,
        explanationCode: null,
        values: Object.freeze([]),
      }),
      ...representations.map((r) => Object.freeze({
        id: `representation:${r.id}`,
        category: "context_representation" as const,
        label: `${title} — ${explanationByCode.get(r.explanationCode)?.connectionLabel ?? ""} — ${r.label}`,
        explanationCode: r.explanationCode,
        values: Object.freeze([]),
      })),
    ]),
  });
}

/* synthetic coverage counts for the fixture's terms — numbers made up for
   the layout, labelled as such by the banner */
export function stressCoverage(dataset: PublicContextDataset): Readonly<Record<string, number>> {
  return Object.freeze(Object.fromEntries(
    dataset.representations.map((r, i) => [r.termId, 100 + ((i * 137) % 900)]),
  ));
}

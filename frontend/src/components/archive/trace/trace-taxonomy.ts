import type { RelationFamily, TraceEdge, TraceGraph, TraceNode } from "./trace-types";

export type TraceTypeStatus = "documented" | "analytical" | "absent_in_v48";

export interface TraceTypeDefinition {
  id: string;
  code: string;
  label: string;
  family: RelationFamily;
  count: number;
  status: TraceTypeStatus;
  definition: string;
  evidenceRequirement: string;
  allowedAssertion: string;
  prohibitedInference: string;
}

export interface TraceSelection {
  edgeId: string;
  nodeId: string;
}

export const TRACE_FAMILY_META: Record<
  RelationFamily,
  { code: string; label: string; question: string }
> = {
  source_provenance: {
    code: "SP",
    label: "Source / provenance",
    question: "Which documented source, creator or collection route supports the object?",
  },
  time_place: {
    code: "TG",
    label: "Time / geography",
    question: "Which recorded date or place statement locates the object?",
  },
  medium_context: {
    code: "MC",
    label: "Medium / context",
    question: "Which recorded medium, type or context statement situates the object?",
  },
  historical_influence: {
    code: "HI",
    label: "Historical influence",
    question: "Which source explicitly documents a historical influence claim?",
  },
};

export const TRACE_TYPE_DEFINITIONS: TraceTypeDefinition[] = [
  {
    id: "has_type", code: "MC-TYPE", label: "Has type", family: "medium_context", count: 34884, status: "documented",
    definition: "Connects an object to a recorded object or design type.",
    evidenceRequirement: "The type must be present in the object-level source metadata or audited candidate record.",
    allowedAssertion: "The source classifies the object with this type.",
    prohibitedInference: "Type similarity does not establish authorship, movement membership or influence.",
  },
  {
    id: "associated_with_context", code: "MC-CONTEXT", label: "Associated with context", family: "medium_context", count: 25403, status: "documented",
    definition: "Connects an object to an explicitly recorded contextual descriptor.",
    evidenceRequirement: "The context must be quoted or normalized from an identified object-level field.",
    allowedAssertion: "The record explicitly associates the object with this context.",
    prohibitedInference: "Context adjacency is not a historical or causal relationship.",
  },
  {
    id: "associated_with_place", code: "TG-PLACE", label: "Associated with place", family: "time_place", count: 16069, status: "documented",
    definition: "Connects an object to its audited object-level geographic statement.",
    evidenceRequirement: "Use object place or an explicitly documented circulation place; never institution location or creator nationality.",
    allowedAssertion: "The object record supports an association with the named place.",
    prohibitedInference: "The place does not prove production coordinates, travel, diffusion or influence.",
  },
  {
    id: "documented_by", code: "SP-DOC", label: "Documented by", family: "source_provenance", count: 15929, status: "documented",
    definition: "Connects an object to the source record that documents it.",
    evidenceRequirement: "A stable official record or auditable source page must resolve to the object.",
    allowedAssertion: "This source record documents the selected object.",
    prohibitedInference: "Documentation does not imply creation, ownership or historical influence.",
  },
  {
    id: "created_by", code: "SP-CREATOR", label: "Created by", family: "source_provenance", count: 10006, status: "documented",
    definition: "Connects an object to a creator attribution recorded by the source.",
    evidenceRequirement: "The source must explicitly provide the creator or credited authorship string.",
    allowedAssertion: "The source attributes creation to this named entity.",
    prohibitedInference: "A name match alone does not resolve authority identity or influence.",
  },
  {
    id: "has_material_or_technique", code: "MC-TECH", label: "Has material or technique", family: "medium_context", count: 9992, status: "documented",
    definition: "Connects an object to a recorded material, process or production technique.",
    evidenceRequirement: "The material or technique must come from object metadata or source description.",
    allowedAssertion: "The source records this material or technique for the object.",
    prohibitedInference: "Technique similarity does not establish chronology, authorship or influence.",
  },
  {
    id: "associated_with_research_cluster", code: "MC-CLUSTER", label: "Associated with research cluster", family: "medium_context", count: 2920, status: "analytical",
    definition: "Places an object in a documented project research cluster.",
    evidenceRequirement: "The cluster assignment must be retained as an explicit analytical classification.",
    allowedAssertion: "The project analyses this object inside the named cluster.",
    prohibitedInference: "A research cluster is not a historical movement or influence network.",
  },
  {
    id: "associated_with_theme", code: "MC-THEME", label: "Associated with theme", family: "medium_context", count: 2920, status: "analytical",
    definition: "Connects an object to an explicit curatorial or research theme.",
    evidenceRequirement: "The theme must be recorded in the audited candidate or source context.",
    allowedAssertion: "The object is analysed under this theme.",
    prohibitedInference: "Theme co-membership does not prove contact or influence.",
  },
  {
    id: "has_medium", code: "MC-MEDIUM", label: "Has medium", family: "medium_context", count: 2920, status: "documented",
    definition: "Connects an object to its recorded medium statement.",
    evidenceRequirement: "Retain the source medium string or an auditable display normalization.",
    allowedAssertion: "The object is recorded in this medium.",
    prohibitedInference: "Medium is a display and evidence category, not a causal lineage.",
  },
  {
    id: "part_of_collection", code: "SP-COLLECTION", label: "Part of collection", family: "source_provenance", count: 2906, status: "documented",
    definition: "Connects an object to a named source collection.",
    evidenceRequirement: "The object-level source must identify collection membership.",
    allowedAssertion: "The source places the object in this collection.",
    prohibitedInference: "Collection membership does not locate production or establish influence.",
  },
  {
    id: "part_of_series", code: "SP-SERIES", label: "Part of series", family: "source_provenance", count: 2325, status: "documented",
    definition: "Connects an object to an explicitly named series.",
    evidenceRequirement: "Series membership must be present in the source record.",
    allowedAssertion: "The object belongs to the recorded series.",
    prohibitedInference: "Series order does not automatically encode chronology or influence.",
  },
  {
    id: "circulated_in", code: "TG-CIRC", label: "Circulated in", family: "time_place", count: 122, status: "documented",
    definition: "Connects an object to a place where circulation is explicitly documented.",
    evidenceRequirement: "The source must distinguish circulation place from repository and creator location.",
    allowedAssertion: "Evidence records circulation in this place.",
    prohibitedInference: "Circulation does not by itself prove origin, reception or influence.",
  },
  {
    id: "issued_by", code: "SP-ISSUER", label: "Issued by", family: "source_provenance", count: 122, status: "documented",
    definition: "Connects an object to an explicitly recorded issuing entity.",
    evidenceRequirement: "The issuer must be named in the source record.",
    allowedAssertion: "The source records this entity as issuer.",
    prohibitedInference: "Issuer identity does not automatically establish designer or printer.",
  },
  {
    id: "classified_as", code: "MC-CLASS", label: "Classified as", family: "medium_context", count: 110, status: "documented",
    definition: "Connects an object to a source or project classification.",
    evidenceRequirement: "The classification and its originating vocabulary must remain traceable.",
    allowedAssertion: "The identified vocabulary classifies the object this way.",
    prohibitedInference: "Classification equivalence does not establish historical equivalence.",
  },
  {
    id: "dated_to", code: "TG-DATE-TO", label: "Dated to", family: "time_place", count: 110, status: "documented",
    definition: "Records the closing year of an object date range.",
    evidenceRequirement: "The end date must be present in object-level evidence.",
    allowedAssertion: "The documented date range ends in this year.",
    prohibitedInference: "A date range is not an influence direction.",
  },
  {
    id: "associated_with_year", code: "TG-YEAR", label: "Associated with year", family: "time_place", count: 25, status: "documented",
    definition: "Connects an object to a year explicitly stated in contextual evidence.",
    evidenceRequirement: "The year and evidence field must remain visible.",
    allowedAssertion: "The record explicitly associates the object with this year.",
    prohibitedInference: "Temporal proximity alone does not imply contact or influence.",
  },
  {
    id: "credited_to", code: "MC-CREDIT", label: "Credited to", family: "medium_context", count: 25, status: "documented",
    definition: "Preserves a source credit string that is not promoted to resolved creator authority.",
    evidenceRequirement: "Retain the literal credit and its source field.",
    allowedAssertion: "The source supplies this credit.",
    prohibitedInference: "A credit string must not be silently upgraded to resolved authorship.",
  },
  {
    id: "part_of_campaign", code: "MC-CAMPAIGN", label: "Part of campaign", family: "medium_context", count: 19, status: "documented",
    definition: "Connects an object to an explicitly named campaign.",
    evidenceRequirement: "Campaign membership must be object-level and source-linked.",
    allowedAssertion: "The source identifies this object as part of the campaign.",
    prohibitedInference: "Campaign membership does not establish creator identity or influence.",
  },
  {
    id: "uses_language", code: "MC-LANGUAGE", label: "Uses language", family: "medium_context", count: 13, status: "documented",
    definition: "Connects an object to a language explicitly visible or recorded.",
    evidenceRequirement: "The language must be recorded by the source or directly evidenced by the object.",
    allowedAssertion: "The object uses or is recorded in this language.",
    prohibitedInference: "Language does not establish nationality, place or influence.",
  },
  {
    id: "dated", code: "TG-DATED", label: "Dated", family: "time_place", count: 2, status: "documented",
    definition: "Connects an object to an explicitly documented date statement.",
    evidenceRequirement: "The date must be object-level and source-linked.",
    allowedAssertion: "The source dates the object accordingly.",
    prohibitedInference: "Date adjacency is not a historical influence edge.",
  },
  {
    id: "influenced_by", code: "HI-INFLUENCE", label: "Influenced by", family: "historical_influence", count: 0, status: "absent_in_v48",
    definition: "A reserved relation for an explicit, source-documented historical influence claim.",
    evidenceRequirement: "Requires a direct scholarly or primary-source statement naming the influence relationship.",
    allowedAssertion: "No active v48 edge currently satisfies this requirement.",
    prohibitedInference: "Never derive this edge from similarity, co-occurrence, shared place, shared date or shared medium.",
  },
];

export const TRACE_TYPE_BY_ID = new Map(
  TRACE_TYPE_DEFINITIONS.map((definition) => [definition.id, definition]),
);

export function traceTypeFor(label: string): TraceTypeDefinition {
  return TRACE_TYPE_BY_ID.get(label) ?? {
    id: label,
    code: `${TRACE_FAMILY_META.medium_context.code}-OTHER`,
    label: label.replaceAll("_", " "),
    family: "medium_context",
    count: 0,
    status: "documented",
    definition: "A source-labelled TRACE relation retained without a registered display definition.",
    evidenceRequirement: "The object-level source field and evidence URL must remain visible.",
    allowedAssertion: "Only the literal recorded relationship may be stated.",
    prohibitedInference: "Do not infer historical influence or authority identity.",
  };
}

export function tracePeerNode(
  edge: TraceEdge,
  rootId: string,
  nodes: Map<string, TraceNode>,
) {
  if (edge.subject === rootId) return nodes.get(edge.object);
  if (edge.object === rootId) return nodes.get(edge.subject);
  return nodes.get(edge.object) ?? nodes.get(edge.subject);
}

export function buildTraceMarks(graph: TraceGraph) {
  const nodeIds = graph.nodes
    .map((node) => node.id)
    .filter((id) => id !== graph.object.nodeId)
    .sort();
  const nodeMarks = new Map<string, string>([[graph.object.nodeId, "OBJ"]]);
  nodeIds.forEach((id, index) => nodeMarks.set(id, `N${String(index + 1).padStart(2, "0")}`));

  const familyIndexes = new Map<RelationFamily, number>();
  const edgeMarks = new Map<string, string>();
  [...graph.edges]
    .sort((left, right) => left.id.localeCompare(right.id))
    .forEach((edge) => {
      const next = (familyIndexes.get(edge.family) ?? 0) + 1;
      familyIndexes.set(edge.family, next);
      edgeMarks.set(
        edge.id,
        `${TRACE_FAMILY_META[edge.family].code}-E${String(next).padStart(2, "0")}`,
      );
    });

  return { nodeMarks, edgeMarks };
}

export function selectionForEdge(graph: TraceGraph, edge: TraceEdge): TraceSelection {
  const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
  const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
  return { edgeId: edge.id, nodeId: peer?.id ?? edge.object };
}

export function diagramModeForFamily(family: RelationFamily) {
  if (family === "source_provenance") return "sources" as const;
  if (family === "time_place") return "geography" as const;
  return "medium" as const;
}

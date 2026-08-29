import "server-only";

import { createHash } from "node:crypto";
import { getExplorationV2ReadModel } from "./read-model.server.ts";
import {
  TRACE_EXPLORATION_V2_API_VERSION,
} from "./types.ts";
import type {
  ExplorationV2AssociationDto,
  ExplorationV2AssociationRecord,
  ExplorationV2CategoryDto,
  ExplorationV2CategoryRecord,
  ExplorationV2CompositionDto,
  ExplorationV2CompositionRecord,
  ExplorationV2ExportManifestDto,
  ExplorationV2ExportRequest,
  ExplorationV2MapDto,
  ExplorationV2MapNodeDto,
  ExplorationV2PlainTextTreeDto,
  ExplorationV2ReadModel,
  ExplorationV2StateDto,
  ExplorationV2StateRecord,
  ExplorationV2VocabularyDto,
  ExplorationV2VocabularyRecord,
  JsonValue,
} from "./types.ts";

interface ExplorationV2Index {
  readonly categoryByEntry: ReadonlyMap<string, ExplorationV2CategoryRecord>;
  readonly vocabularyById: ReadonlyMap<string, ExplorationV2VocabularyRecord>;
  readonly associationById: ReadonlyMap<string, ExplorationV2AssociationRecord>;
}

interface TreeLink {
  readonly nodeId: string;
  readonly associationId: string;
}

let cachedIndex: ExplorationV2Index | undefined;

function canonicalJson(value: JsonValue): string {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") {
    return JSON.stringify(value) ?? "null";
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const record = value as { readonly [key: string]: JsonValue };
  return `{${Object.keys(record).sort(compareCodePoints).map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`).join(",")}}`;
}

function canonicalHash(value: JsonValue): string {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

function compareCodePoints(left: string, right: string): number {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0) ?? 0);
  const rightPoints = Array.from(right, (character) => character.codePointAt(0) ?? 0);
  const length = Math.min(leftPoints.length, rightPoints.length);
  for (let index = 0; index < length; index += 1) {
    if (leftPoints[index] !== rightPoints[index]) return leftPoints[index] - rightPoints[index];
  }
  return leftPoints.length - rightPoints.length;
}

function labelForCategory(category: ExplorationV2CategoryRecord): string {
  return category.label;
}

function getIndex(): ExplorationV2Index {
  if (cachedIndex) return cachedIndex;
  const model = getExplorationV2ReadModel();
  cachedIndex = {
    categoryByEntry: new Map(model.categories.map((item) => [item.category_entry_id, item])),
    vocabularyById: new Map(model.vocabulary.map((item) => [item.vocabulary_id, item])),
    associationById: new Map(model.associations.map((item) => [item.association_id, item])),
  };
  return cachedIndex;
}

function requireCategory(categoryEntryId: string): ExplorationV2CategoryRecord {
  const category = getIndex().categoryByEntry.get(categoryEntryId);
  if (!category) throw new Error("DERIVATION_CATEGORY_MISSING");
  return category;
}

function requireVocabulary(vocabularyId: string): ExplorationV2VocabularyRecord {
  const vocabulary = getIndex().vocabularyById.get(vocabularyId);
  if (!vocabulary) throw new Error("DERIVATION_VOCABULARY_MISSING");
  return vocabulary;
}

function requireAssociation(associationId: string): ExplorationV2AssociationRecord {
  const association = getIndex().associationById.get(associationId);
  if (!association) throw new Error("DERIVATION_ASSOCIATION_MISSING");
  return association;
}

function requireComposition(model: ExplorationV2ReadModel, compositionId: string): ExplorationV2CompositionRecord {
  const composition = model.compositions[compositionId];
  if (!composition) throw new Error("DERIVATION_COMPOSITION_MISSING");
  return composition;
}

export function toExplorationV2CategoryDto(category: ExplorationV2CategoryRecord): ExplorationV2CategoryDto {
  return {
    category_id: category.category_id,
    category_entry_id: category.category_entry_id,
    label: labelForCategory(category),
    ...(category.entry_label ? { entry_label: category.entry_label } : {}),
    ...(category.description ? { description: category.description } : {}),
    composition_ids: [...category.composition_ids],
    initial_state_id: category.initial_state_id,
  };
}

export function toExplorationV2VocabularyDto(vocabulary: ExplorationV2VocabularyRecord): ExplorationV2VocabularyDto {
  return {
    vocabulary_id: vocabulary.vocabulary_id,
    canonical_label: vocabulary.canonical_label,
    attested_forms: [...(vocabulary.attested_forms ?? [vocabulary.canonical_label])],
    language: vocabulary.language ?? "en",
    ...(vocabulary.scope_note ? { scope_note: vocabulary.scope_note } : {}),
    ...(vocabulary.ambiguity_note ? { ambiguity_note: vocabulary.ambiguity_note } : {}),
    ...(vocabulary.activation_status ? { activation_status: vocabulary.activation_status } : {}),
  };
}

export function toExplorationV2AssociationDto(association: ExplorationV2AssociationRecord): ExplorationV2AssociationDto {
  const [leftId, rightId] = association.endpoint_vocabulary_ids;
  const leftLabel = requireVocabulary(leftId).canonical_label;
  const rightLabel = requireVocabulary(rightId).canonical_label;
  return {
    association_id: association.association_id,
    endpoint_vocabulary_ids: [leftId, rightId],
    endpoint_labels: association.endpoint_labels
      ? [association.endpoint_labels[0], association.endpoint_labels[1]]
      : [leftLabel, rightLabel],
    support_status: association.support_status,
    ...(association.strength !== undefined ? { strength: association.strength } : {}),
    ...(association.confidence !== undefined ? { confidence: association.confidence } : {}),
    generic_association_only: true,
    association_accessible_description: association.association_accessible_description
      ?? `${leftLabel} is available to explore with ${rightLabel} as a qualified generic association.`,
    explicit_non_claims: [...(association.explicit_non_claims ?? [
      "causation",
      "influence",
      "chronology",
      "hierarchy",
      "direction",
      "equivalence",
    ])],
  };
}

export function toExplorationV2CompositionDto(composition: ExplorationV2CompositionRecord): ExplorationV2CompositionDto {
  return {
    composition_id: composition.composition_id,
    category_entry_id: composition.category_entry_id,
    seed_id: composition.seed_id,
    seed_node_id: composition.seed_node_id,
    node_ids: [...composition.node_ids],
    association_ids: [...composition.association_ids],
    topology_family: composition.topology_family,
    semantic_hash: composition.semantic_hash,
    label: composition.label,
    description: composition.description,
  };
}

export function toExplorationV2StateDto(state: ExplorationV2StateRecord): ExplorationV2StateDto {
  return {
    state_id: state.state_id,
    state_hash: state.state_hash,
    category_entry_id: state.category_entry_id,
    composition_id: state.composition_id,
    seed_id: state.seed_id,
    focused_node_id: state.focused_node_id,
    expanded_node_ids: [...state.expanded_node_ids],
    visible_node_ids: [...state.visible_node_ids],
    visible_association_ids: [...state.visible_association_ids],
    available_actions: [...state.available_actions],
    semantic_hash: state.semantic_hash,
    presentation_hash: state.presentation_hash,
    database_snapshot: state.database_snapshot,
  };
}

function sortedLinks(links: readonly TreeLink[]): readonly TreeLink[] {
  return [...links].sort((left, right) => {
    const leftLabel = requireVocabulary(left.nodeId).canonical_label;
    const rightLabel = requireVocabulary(right.nodeId).canonical_label;
    return compareCodePoints(leftLabel, rightLabel)
      || compareCodePoints(left.nodeId, right.nodeId)
      || compareCodePoints(left.associationId, right.associationId);
  });
}

function renderTreeLines(
  rootNodeId: string,
  children: ReadonlyMap<string, readonly string[]>,
  ascii: boolean,
): readonly string[] {
  const lines: string[] = [requireVocabulary(rootNodeId).canonical_label];
  const branch = ascii ? "+-- " : "├── ";
  const lastBranch = ascii ? "`-- " : "└── ";
  const continuation = ascii ? "|   " : "│   ";
  const blank = "    ";

  const appendChildren = (nodeId: string, prefix: string): void => {
    const nodeChildren = children.get(nodeId) ?? [];
    nodeChildren.forEach((childId, index) => {
      const last = index === nodeChildren.length - 1;
      lines.push(`${prefix}${last ? lastBranch : branch}${requireVocabulary(childId).canonical_label}`);
      appendChildren(childId, `${prefix}${last ? blank : continuation}`);
    });
  };
  appendChildren(rootNodeId, "");
  return lines;
}

export function deriveExplorationV2Tree(
  model: ExplorationV2ReadModel,
  state: ExplorationV2StateRecord,
): ExplorationV2PlainTextTreeDto {
  const visibleNodes = new Set(state.visible_node_ids);
  const adjacency = new Map<string, TreeLink[]>(state.visible_node_ids.map((nodeId) => [nodeId, []]));
  for (const associationId of state.visible_association_ids) {
    const association = requireAssociation(associationId);
    const [leftId, rightId] = association.endpoint_vocabulary_ids;
    if (!visibleNodes.has(leftId) || !visibleNodes.has(rightId)) throw new Error("DERIVATION_EDGE_OUTSIDE_VISIBLE_STATE");
    adjacency.get(leftId)?.push({ nodeId: rightId, associationId });
    adjacency.get(rightId)?.push({ nodeId: leftId, associationId });
  }

  const visited = new Set<string>([state.focused_node_id]);
  const traversal: string[] = [state.focused_node_id];
  const treeAssociations: string[] = [];
  const children = new Map<string, string[]>();
  const queue: string[] = [state.focused_node_id];
  while (queue.length > 0) {
    const nodeId = queue.shift();
    if (!nodeId) break;
    for (const link of sortedLinks(adjacency.get(nodeId) ?? [])) {
      if (visited.has(link.nodeId)) continue;
      visited.add(link.nodeId);
      traversal.push(link.nodeId);
      treeAssociations.push(link.associationId);
      children.set(nodeId, [...(children.get(nodeId) ?? []), link.nodeId]);
      queue.push(link.nodeId);
    }
  }
  if (visited.size !== state.visible_node_ids.length) throw new Error("DERIVATION_VISIBLE_GRAPH_DISCONNECTED");

  const unicodeLines = renderTreeLines(state.focused_node_id, children, false);
  const asciiLines = renderTreeLines(state.focused_node_id, children, true);
  return {
    tree_version: "trace-exploration-plain-text-tree-v2",
    composition_id: state.composition_id,
    root_node_id: state.focused_node_id,
    tree_node_ids: traversal,
    tree_association_ids: treeAssociations,
    visible_association_ids: [...state.visible_association_ids],
    plain_text_tree: unicodeLines.join("\n"),
    plain_text_tree_ascii: asciiLines.join("\n"),
  };
}

function roundPosition(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}

function deriveMapNodes(state: ExplorationV2StateRecord, tree: ExplorationV2PlainTextTreeDto): readonly ExplorationV2MapNodeDto[] {
  const expanded = new Set(state.expanded_node_ids);
  return tree.tree_node_ids.map((nodeId, index) => {
    const count = tree.tree_node_ids.length;
    const angle = count === 1 ? 0 : (-Math.PI / 2) + ((Math.PI * 2 * index) / count);
    const normalisedX = count === 1 ? 0.5 : 0.5 + (Math.cos(angle) * 0.38);
    const normalisedY = count === 1 ? 0.5 : 0.5 + (Math.sin(angle) * 0.38);
    return {
      ...toExplorationV2VocabularyDto(requireVocabulary(nodeId)),
      focused: nodeId === state.focused_node_id,
      expanded: expanded.has(nodeId),
      position: {
        normalised_x: roundPosition(normalisedX),
        normalised_y: roundPosition(normalisedY),
      },
    };
  });
}

export function deriveExplorationV2Map(
  model: ExplorationV2ReadModel,
  state: ExplorationV2StateRecord,
): ExplorationV2MapDto {
  const category = requireCategory(state.category_entry_id);
  const composition = requireComposition(model, state.composition_id);
  if (!category.composition_ids.includes(composition.composition_id)) throw new Error("DERIVATION_COMPOSITION_OUTSIDE_CATEGORY");
  const tree = deriveExplorationV2Tree(model, state);
  const nodes = deriveMapNodes(state, tree);
  const associations = state.visible_association_ids.map((id) => toExplorationV2AssociationDto(requireAssociation(id)));
  return {
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    database_snapshot: model.database.database_snapshot_id,
    map_id: category.category_entry_id,
    is_initial_state: category.initial_state_id === state.state_id,
    category: toExplorationV2CategoryDto(category),
    state: toExplorationV2StateDto(state),
    composition: toExplorationV2CompositionDto(composition),
    nodes,
    associations,
    plain_text_tree: tree,
    map_summary: `${labelForCategory(category)}: ${nodes.length} visible terms and ${associations.length} qualified generic associations.`,
  };
}

function safeFilenamePart(value: string): string {
  const normalised = value.normalize("NFKD").replace(/[^a-zA-Z0-9_-]+/gu, "-").replace(/^-+|-+$/gu, "").toLowerCase();
  return normalised.slice(0, 72) || "exploration";
}

export function deriveExplorationV2ExportManifest(
  model: ExplorationV2ReadModel,
  state: ExplorationV2StateRecord,
  request: ExplorationV2ExportRequest,
): ExplorationV2ExportManifestDto {
  const map = deriveExplorationV2Map(model, state);
  const identity: JsonValue = {
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    render_version: "trace-exploration-portrait-png-v2",
    database_snapshot: model.database.database_snapshot_id,
    state_hash: state.state_hash,
    state_presentation_hash: state.presentation_hash,
    composition_id: state.composition_id,
    export_preset: request.export_preset,
    theme_token_set: request.theme_token_set,
  };
  const presentationHash = canonicalHash(identity);
  const exportId = `TEV2-${presentationHash.slice(0, 24)}`;
  const filenameCategory = safeFilenamePart(map.category.category_id);
  const externallySupportedCount = map.associations.filter(
    (association) => association.support_status === "ACTIVE_EXTERNALLY_SUPPORTED",
  ).length;
  const sourceSupportedCount = map.associations.filter(
    (association) => association.support_status === "ACTIVE_SOURCE_SUPPORTED",
  ).length;
  if (externallySupportedCount + sourceSupportedCount !== map.associations.length) {
    throw new Error("DERIVATION_ASSOCIATION_SUPPORT_STATUS_MISMATCH");
  }
  return {
    manifest_version: "trace-exploration-export-manifest-v2",
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    render_version: "trace-exploration-portrait-png-v2",
    export_id: exportId,
    database_snapshot: model.database.database_snapshot_id,
    map_id: map.map_id,
    state_id: state.state_id,
    state_hash: state.state_hash,
    category_entry_id: state.category_entry_id,
    composition_id: state.composition_id,
    seed_id: state.seed_id,
    export_preset: request.export_preset,
    theme_token_set: request.theme_token_set,
    dimensions: { width: 1080, height: 1620 },
    category: map.category,
    nodes: map.nodes,
    associations: map.associations,
    plain_text_tree: map.plain_text_tree,
    node_count: map.nodes.length,
    association_count: map.associations.length,
    provenance_summary: {
      association_count: map.associations.length,
      externally_supported_count: externallySupportedCount,
      source_supported_count: sourceSupportedCount,
      generic_association_only: true,
      source_locators_withheld_from_public_export: true,
    },
    semantic_hash: state.semantic_hash,
    presentation_hash: presentationHash,
    export_alt_text: `${map.category.label} exploration map with ${map.nodes.length} terms and ${map.associations.length} qualified generic associations.`,
    suggested_filename: `trace-exploration-${filenameCategory}-${state.state_hash.slice(0, 12)}-${request.theme_token_set}.png`,
  };
}

export function getExplorationV2CategoryByEntry(categoryEntryId: string): ExplorationV2CategoryRecord | undefined {
  return getIndex().categoryByEntry.get(categoryEntryId);
}

export function getExplorationV2VocabularyById(vocabularyId: string): ExplorationV2VocabularyRecord | undefined {
  return getIndex().vocabularyById.get(vocabularyId);
}

export function getExplorationV2AssociationById(associationId: string): ExplorationV2AssociationRecord | undefined {
  return getIndex().associationById.get(associationId);
}

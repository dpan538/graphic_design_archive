import "server-only";

import {
  TRACE_EXPLORATION_V2_ACTIONS,
} from "./types.ts";
import type {
  ExplorationV2Action,
  ExplorationV2CategoryId,
  ExplorationV2ReadModel,
  ExplorationV2StateRecord,
} from "./types.ts";

const CATEGORY_ORDER: readonly ExplorationV2CategoryId[] = ["region", "theme", "medium", "movement"];

function compareCodePoints(left: string, right: string): number {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0) ?? 0);
  const rightPoints = Array.from(right, (character) => character.codePointAt(0) ?? 0);
  const length = Math.min(leftPoints.length, rightPoints.length);
  for (let index = 0; index < length; index += 1) {
    if (leftPoints[index] !== rightPoints[index]) return leftPoints[index] - rightPoints[index];
  }
  return leftPoints.length - rightPoints.length;
}

function sameOrderedValues(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function stateKey(compositionId: string, focusedNodeId: string, expandedNodeIds: readonly string[]): string {
  return JSON.stringify([compositionId, focusedNodeId, [...expandedNodeIds].sort(compareCodePoints)]);
}

export interface ExplorationV2DerivedTransition {
  readonly transition_key: string;
  readonly action: ExplorationV2Action;
  readonly target_id: string;
  readonly next_state: ExplorationV2StateRecord;
}

export class ExplorationV2TransitionIndex {
  readonly transitionCount: number;
  private readonly stateByKey = new Map<string, ExplorationV2StateRecord>();
  private readonly adjacencyByComposition = new Map<string, ReadonlyMap<string, readonly string[]>>();
  private readonly categoryIdByEntry = new Map<string, ExplorationV2CategoryId>();
  private readonly compositionIdsByCategory = new Map<ExplorationV2CategoryId, readonly string[]>();
  private readonly rootByComposition = new Map<string, ExplorationV2StateRecord>();
  private readonly topRootByCategory = new Map<ExplorationV2CategoryId, ExplorationV2StateRecord>();

  constructor(private readonly model: ExplorationV2ReadModel) {
    const associationById = new Map(model.associations.map((item) => [item.association_id, item]));
    for (const category of model.categories) {
      this.categoryIdByEntry.set(category.category_entry_id, category.category_id);
    }
    for (const categoryId of CATEGORY_ORDER) {
      const entries = model.categories
        .filter((category) => category.category_id === categoryId)
        .sort((left, right) => compareCodePoints(left.category_entry_id, right.category_entry_id));
      const initial = entries[0] ? model.states[entries[0].initial_state_id] : undefined;
      if (!initial) throw new Error("TRANSITION_DERIVATION_INVALID:category_root");
      this.topRootByCategory.set(categoryId, initial);
      this.compositionIdsByCategory.set(categoryId, Object.values(model.compositions)
        .filter((composition) => this.categoryIdByEntry.get(composition.category_entry_id) === categoryId)
        .map((composition) => composition.composition_id)
        .sort(compareCodePoints));
    }

    for (const composition of Object.values(model.compositions)) {
      if (!composition.seed_node_id || !composition.node_ids.includes(composition.seed_node_id)) {
        throw new Error("TRANSITION_DERIVATION_INVALID:composition_seed_node");
      }
      const adjacency = new Map<string, Set<string>>(composition.node_ids.map((nodeId) => [nodeId, new Set()]));
      for (const associationId of composition.association_ids) {
        const association = associationById.get(associationId);
        if (!association) throw new Error("TRANSITION_DERIVATION_INVALID:association");
        const [leftId, rightId] = association.endpoint_vocabulary_ids;
        if (!adjacency.has(leftId) || !adjacency.has(rightId)) {
          throw new Error("TRANSITION_DERIVATION_INVALID:association_endpoint");
        }
        adjacency.get(leftId)?.add(rightId);
        adjacency.get(rightId)?.add(leftId);
      }
      this.adjacencyByComposition.set(composition.composition_id, new Map(
        [...adjacency].map(([nodeId, neighbours]) => [nodeId, [...neighbours].sort(compareCodePoints)]),
      ));
    }

    for (const state of Object.values(model.states)) {
      const key = stateKey(state.composition_id, state.focused_node_id, state.expanded_node_ids);
      if (this.stateByKey.has(key)) throw new Error("TRANSITION_DERIVATION_INVALID:duplicate_state_key");
      this.stateByKey.set(key, state);
    }

    let transitionCount = 0;
    for (const composition of Object.values(model.compositions)) {
      const expectedStateCount = composition.node_ids.length * (2 ** composition.node_ids.length);
      const compositionStates = Object.values(model.states).filter((state) => state.composition_id === composition.composition_id);
      if (compositionStates.length !== expectedStateCount) {
        throw new Error("TRANSITION_DERIVATION_INVALID:incomplete_state_space");
      }
      const root = this.stateByKey.get(stateKey(composition.composition_id, composition.seed_node_id ?? "", []));
      if (!root) throw new Error("TRANSITION_DERIVATION_INVALID:composition_root");
      this.rootByComposition.set(composition.composition_id, root);
    }
    for (const category of model.categories) {
      const canonicalCompositionId = [...category.composition_ids].sort(compareCodePoints)[0];
      const canonicalRoot = canonicalCompositionId ? this.rootByComposition.get(canonicalCompositionId) : undefined;
      if (!canonicalRoot || category.initial_state_id !== canonicalRoot.state_id) {
        throw new Error("TRANSITION_DERIVATION_INVALID:category_initial_state");
      }
    }
    for (const state of Object.values(model.states)) {
      this.validateStateDerivation(state);
      for (const action of TRACE_EXPLORATION_V2_ACTIONS) transitionCount += this.targets(state, action).length;
    }
    this.transitionCount = transitionCount;
  }

  targets(state: ExplorationV2StateRecord, action: ExplorationV2Action): readonly string[] {
    const composition = this.model.compositions[state.composition_id];
    const adjacency = this.adjacencyByComposition.get(state.composition_id);
    if (!composition || !adjacency) return [];
    if (action === "SELECT_CATEGORY") return CATEGORY_ORDER;
    if (action === "FOCUS_NODE") return composition.node_ids;
    if (action === "MOVE_FOCUS") return adjacency.get(state.focused_node_id) ?? [];
    if (action === "EXPAND_NODE") {
      const expanded = new Set(state.expanded_node_ids);
      return state.visible_node_ids.filter((nodeId) => !expanded.has(nodeId));
    }
    if (action === "COLLAPSE_NODE") return state.expanded_node_ids;
    if (action === "SELECT_COMPOSITION") {
      const categoryId = this.categoryIdByEntry.get(state.category_entry_id);
      return categoryId ? this.compositionIdsByCategory.get(categoryId) ?? [] : [];
    }
    if (action === "RESET_CATEGORY" || action === "EXPORT_CURRENT_STATE") return [""];
    return [];
  }

  resolve(
    state: ExplorationV2StateRecord,
    action: ExplorationV2Action,
    targetId: string,
  ): ExplorationV2DerivedTransition | undefined {
    if (!this.targets(state, action).includes(targetId)) return undefined;
    let next: ExplorationV2StateRecord | undefined;
    if (action === "SELECT_CATEGORY") {
      next = this.topRootByCategory.get(targetId as ExplorationV2CategoryId);
    } else if (action === "FOCUS_NODE" || action === "MOVE_FOCUS") {
      next = this.stateByKey.get(stateKey(state.composition_id, targetId, state.expanded_node_ids));
    } else if (action === "EXPAND_NODE") {
      next = this.stateByKey.get(stateKey(state.composition_id, state.focused_node_id, [...state.expanded_node_ids, targetId]));
    } else if (action === "COLLAPSE_NODE") {
      next = this.stateByKey.get(stateKey(
        state.composition_id,
        state.focused_node_id,
        state.expanded_node_ids.filter((nodeId) => nodeId !== targetId),
      ));
    } else if (action === "SELECT_COMPOSITION") {
      next = this.rootByComposition.get(targetId);
    } else if (action === "RESET_CATEGORY") {
      const categoryId = this.categoryIdByEntry.get(state.category_entry_id);
      next = categoryId ? this.topRootByCategory.get(categoryId) : undefined;
    } else if (action === "EXPORT_CURRENT_STATE") {
      next = state;
    }
    return next ? {
      transition_key: `${state.state_hash}|${action}|${targetId}`,
      action,
      target_id: targetId,
      next_state: next,
    } : undefined;
  }

  private validateStateDerivation(state: ExplorationV2StateRecord): void {
    const composition = this.model.compositions[state.composition_id];
    const adjacency = this.adjacencyByComposition.get(state.composition_id);
    if (!composition || !adjacency || !composition.node_ids.includes(state.focused_node_id)) {
      throw new Error("TRANSITION_DERIVATION_INVALID:state_composition");
    }
    const expanded = [...state.expanded_node_ids].sort(compareCodePoints);
    if (!sameOrderedValues(expanded, state.expanded_node_ids) || expanded.some((nodeId) => !composition.node_ids.includes(nodeId))) {
      throw new Error("TRANSITION_DERIVATION_INVALID:state_expansion");
    }
    const visible = new Set<string>([state.focused_node_id, ...(adjacency.get(state.focused_node_id) ?? []), ...expanded]);
    for (const nodeId of expanded) for (const neighbour of adjacency.get(nodeId) ?? []) visible.add(neighbour);
    const expectedVisibleNodes = [...visible].sort(compareCodePoints);
    if (!sameOrderedValues(expectedVisibleNodes, state.visible_node_ids)) {
      throw new Error("TRANSITION_DERIVATION_INVALID:visible_nodes");
    }
    const visibleAssociations = composition.association_ids.filter((associationId) => {
      const association = this.model.associations.find((item) => item.association_id === associationId);
      return association?.endpoint_vocabulary_ids.every((nodeId) => visible.has(nodeId)) ?? false;
    }).sort(compareCodePoints);
    if (!sameOrderedValues(visibleAssociations, state.visible_association_ids)) {
      throw new Error("TRANSITION_DERIVATION_INVALID:visible_associations");
    }
    const expectedActions = TRACE_EXPLORATION_V2_ACTIONS.filter((action) => this.targets(state, action).length > 0);
    if (!sameOrderedValues(expectedActions, state.available_actions)) {
      throw new Error("TRANSITION_DERIVATION_INVALID:available_actions");
    }
  }
}

const transitionIndexes = new WeakMap<ExplorationV2ReadModel, ExplorationV2TransitionIndex>();

export function getExplorationV2TransitionIndex(model: ExplorationV2ReadModel): ExplorationV2TransitionIndex {
  const cached = transitionIndexes.get(model);
  if (cached) return cached;
  const created = new ExplorationV2TransitionIndex(model);
  transitionIndexes.set(model, created);
  return created;
}

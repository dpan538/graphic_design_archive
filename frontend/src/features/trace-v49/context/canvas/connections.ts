import type { TraceAccessibleRow, TracePublicDataRef } from "../../domain";
import type { TraceContextDataset } from "../types";
import {
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  contextCanvasEntityId,
  type ContextCanvasComposition,
  type ContextCanvasConnection,
  type ContextCanvasConnectionGeometry,
  type ContextCanvasEntityId,
  type ContextCanvasVisibleNode,
} from "./types";

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

export function deriveVisibleContextCanvasConnections(
  dataset: TraceContextDataset,
  visibleEntityIds: readonly ContextCanvasEntityId[],
): readonly ContextCanvasConnection[] {
  const visible = new Set(visibleEntityIds);
  const connections: ContextCanvasConnection[] = [];

  for (const assignment of dataset.controlledAssignments) {
    const sourceEntityId = contextCanvasEntityId(assignment.subject);
    const targetEntityId = contextCanvasEntityId(assignment.value);
    if (visible.has(sourceEntityId) && visible.has(targetEntityId)) {
      connections.push(Object.freeze({
        id: `connection:controlled_assignment:${assignment.id}`,
        connectionKind: "controlled_assignment",
        sourceEntityId,
        targetEntityId,
        accessibleRowId: `assignment:${assignment.id}`,
        assignment,
      }));
    }
  }

  for (const membership of dataset.curatedMemberships) {
    const sourceEntityId = contextCanvasEntityId(membership.member);
    const targetEntityId = contextCanvasEntityId(membership.container);
    if (visible.has(sourceEntityId) && visible.has(targetEntityId)) {
      connections.push(Object.freeze({
        id: `connection:curated_membership:${membership.id}`,
        connectionKind: "curated_membership",
        sourceEntityId,
        targetEntityId,
        accessibleRowId: `membership:${membership.id}`,
        membership,
      }));
    }
  }

  for (const semanticEdge of dataset.semanticEdges) {
    const sourceEntityId = contextCanvasEntityId(semanticEdge.subject);
    const targetEntityId = contextCanvasEntityId(semanticEdge.object);
    if (visible.has(sourceEntityId) && visible.has(targetEntityId)) {
      connections.push(Object.freeze({
        id: `connection:semantic_edge:${semanticEdge.id}`,
        connectionKind: "semantic_edge",
        sourceEntityId,
        targetEntityId,
        accessibleRowId: `semantic:${semanticEdge.id}`,
        semanticEdge,
      }));
    }
  }

  return Object.freeze(connections.sort((left, right) => compareText(left.id, right.id)));
}

export function visibleContextCanvasNodes(
  dataset: TraceContextDataset,
  composition: ContextCanvasComposition,
): readonly ContextCanvasVisibleNode[] {
  const refs = new Map(dataset.items.map((ref) => [contextCanvasEntityId(ref), ref]));
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const nodes: ContextCanvasVisibleNode[] = [];
  for (const id of composition.visibleEntityIds) {
    const ref = refs.get(id);
    const position = composition.positions[id];
    if (!ref || !position) continue;
    nodes.push(Object.freeze({ id, ref, position, isRoot: id === rootId }));
  }
  return Object.freeze(nodes.sort((left, right) => compareText(left.id, right.id)));
}

export function contextCanvasConnectionLabel(connection: ContextCanvasConnection): string {
  switch (connection.connectionKind) {
    case "controlled_assignment":
      return connection.assignment.assignmentType;
    case "curated_membership":
      return connection.membership.membershipType;
    case "semantic_edge":
      return connection.semanticEdge.predicateId;
  }
}

function label(ref: TracePublicDataRef | undefined, fallback: string): string {
  return ref?.label?.trim() || ref?.stableId || fallback;
}

function connectionAccessibleLabel(
  connection: ContextCanvasConnection,
  refs: ReadonlyMap<ContextCanvasEntityId, TracePublicDataRef>,
  accessibleRows: ReadonlyMap<string, TraceAccessibleRow>,
): string {
  const row = accessibleRows.get(connection.accessibleRowId);
  if (row) return `${connection.connectionKind}: ${row.label}`;
  return `${connection.connectionKind}: ${label(refs.get(connection.sourceEntityId), connection.sourceEntityId)} to ${label(refs.get(connection.targetEntityId), connection.targetEntityId)}`;
}

function precise(value: number): number {
  return Number(value.toFixed(3));
}

export function buildContextCanvasConnectionGeometry(
  dataset: TraceContextDataset,
  composition: ContextCanvasComposition,
): readonly ContextCanvasConnectionGeometry[] {
  const connections = deriveVisibleContextCanvasConnections(dataset, composition.visibleEntityIds);
  const refs = new Map(dataset.items.map((ref) => [contextCanvasEntityId(ref), ref]));
  const rows = new Map(dataset.accessibleRows.map((row) => [row.id, row]));
  const routeGroups = new Map<string, ContextCanvasConnection[]>();
  for (const connection of connections) {
    const key = `${connection.sourceEntityId}\u0000${connection.targetEntityId}`;
    const group = routeGroups.get(key) ?? [];
    group.push(connection);
    routeGroups.set(key, group);
  }

  const geometry: ContextCanvasConnectionGeometry[] = [];
  for (const connection of connections) {
    const source = composition.positions[connection.sourceEntityId];
    const target = composition.positions[connection.targetEntityId];
    if (!source || !target) continue;
    const sourceCenterX = source.x + CONTEXT_CANVAS_NODE_WIDTH / 2;
    const targetCenterX = target.x + CONTEXT_CANVAS_NODE_WIDTH / 2;
    const leftToRight = sourceCenterX <= targetCenterX;
    const sourceX = source.x + (leftToRight ? CONTEXT_CANVAS_NODE_WIDTH : 0);
    const targetX = target.x + (leftToRight ? 0 : CONTEXT_CANVAS_NODE_WIDTH);
    const sourceY = source.y + CONTEXT_CANVAS_NODE_HEIGHT / 2;
    const targetY = target.y + CONTEXT_CANVAS_NODE_HEIGHT / 2;
    const key = `${connection.sourceEntityId}\u0000${connection.targetEntityId}`;
    const group = routeGroups.get(key) ?? [connection];
    const laneIndex = group.findIndex((item) => item.id === connection.id);
    const laneOffset = (laneIndex - (group.length - 1) / 2) * 12;
    const middleX = (sourceX + targetX) / 2 + laneOffset;
    const path = [
      `M ${precise(sourceX)} ${precise(sourceY)}`,
      `H ${precise(middleX)}`,
      `V ${precise(targetY)}`,
      `H ${precise(targetX)}`,
    ].join(" ");
    geometry.push(Object.freeze({
      connection,
      path,
      labelX: precise(middleX + 6),
      labelY: precise((sourceY + targetY) / 2 - 6),
      accessibleLabel: connectionAccessibleLabel(connection, refs, rows),
    }));
  }
  return Object.freeze(geometry);
}

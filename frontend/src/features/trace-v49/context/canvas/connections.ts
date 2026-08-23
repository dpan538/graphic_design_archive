import type { TraceAccessibleRow, TracePublicDataRef } from "../../domain";
import type { TraceContextDataset } from "../types";
import {
  contextCanvasAccessibleRowsForMode,
  contextCanvasEntityRefsForMode,
  contextCanvasRepresentationByEntityId,
  getGovernedContextMetadata,
} from "./model";
import {
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  contextCanvasEntityId,
  type ContextCanvasComposition,
  type ContextCanvasConnection,
  type ContextCanvasConnectionGeometry,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasEntityId,
  type ContextCanvasVisibleNode,
} from "./types";

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

export function deriveVisibleContextCanvasConnections(
  dataset: TraceContextDataset,
  visibleEntityIds: readonly ContextCanvasEntityId[],
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): readonly ContextCanvasConnection[] {
  const visible = new Set(visibleEntityIds);
  const connections: ContextCanvasConnection[] = [];

  if (dataMode === "governed_context_v1") {
    if (!metadata) throw new Error("Governed Context connections require metadata.");
    const governed = getGovernedContextMetadata(dataMode, metadata);
    if (!governed) throw new Error("Governed Context metadata is unavailable.");
    const sourceEntityId = contextCanvasEntityId(dataset.selectedRecord);
    for (const representation of governed.representations) {
      const targetEntityId = contextCanvasEntityId({
        stableId: representation.termId,
        kind: "controlled_term",
      });
      if (visible.has(sourceEntityId) && visible.has(targetEntityId)) {
        connections.push(Object.freeze({
          id: `connection:context_representation:${representation.representationId}`,
          connectionKind: "context_representation",
          sourceEntityId,
          targetEntityId,
          accessibleRowId: `representation:${representation.representationId}`,
          representation,
        }));
      }
    }
    return Object.freeze(connections.sort((left, right) => compareText(left.id, right.id)));
  }

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

  if (dataMode === "synthetic_contract") for (const membership of dataset.curatedMemberships) {
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

  if (dataMode === "synthetic_contract") for (const semanticEdge of dataset.semanticEdges) {
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
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): readonly ContextCanvasVisibleNode[] {
  if (!metadata && dataMode !== "synthetic_contract") {
    throw new Error(`${dataMode} Context Canvas nodes require metadata.`);
  }
  const effectiveMetadata = metadata ?? {
    dataLabel: "synthetic contract fixture",
    mappingVersion: "synthetic-context-contract-v1",
    candidateState: "synthetic_contract" as const,
    historicalEvidence: false as const,
    governedPublicRelease: false,
    publicReleaseData: false,
    publicObjectCohortCount: dataset.counts.denominator,
  };
  const refs = new Map(
    contextCanvasEntityRefsForMode(dataset, dataMode, effectiveMetadata)
      .map((ref) => [contextCanvasEntityId(ref), ref]),
  );
  const representationByEntityId = contextCanvasRepresentationByEntityId(dataMode, effectiveMetadata);
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const nodes: ContextCanvasVisibleNode[] = [];
  for (const id of composition.visibleEntityIds) {
    const ref = refs.get(id);
    const position = composition.positions[id];
    if (!ref || !position) continue;
    nodes.push(Object.freeze({
      id,
      ref,
      position,
      isRoot: id === rootId,
      representation: representationByEntityId.get(id),
    }));
  }
  return Object.freeze(nodes.sort((left, right) => compareText(left.id, right.id)));
}

export function contextCanvasConnectionLabel(connection: ContextCanvasConnection): string {
  switch (connection.connectionKind) {
    case "context_representation":
      return connection.representation.connectionLabel;
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
  if (row) {
    const values = row.values.map((value) => `${value.label}: ${value.value}`).join("; ");
    return `${connection.connectionKind}: ${row.label}${values ? `; ${values}` : ""}`;
  }
  return `${connection.connectionKind}: ${label(refs.get(connection.sourceEntityId), connection.sourceEntityId)} to ${label(refs.get(connection.targetEntityId), connection.targetEntityId)}`;
}

function precise(value: number): number {
  return Number(value.toFixed(3));
}

export function buildContextCanvasConnectionGeometry(
  dataset: TraceContextDataset,
  composition: ContextCanvasComposition,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): readonly ContextCanvasConnectionGeometry[] {
  if (!metadata && dataMode !== "synthetic_contract") {
    throw new Error(`${dataMode} Context Canvas geometry requires metadata.`);
  }
  const effectiveMetadata = metadata ?? {
    dataLabel: "synthetic contract fixture",
    mappingVersion: "synthetic-context-contract-v1",
    candidateState: "synthetic_contract" as const,
    historicalEvidence: false as const,
    governedPublicRelease: false,
    publicReleaseData: false,
    publicObjectCohortCount: dataset.counts.denominator,
  };
  const connections = deriveVisibleContextCanvasConnections(
    dataset,
    composition.visibleEntityIds,
    dataMode,
    effectiveMetadata,
  );
  const refs = new Map(
    contextCanvasEntityRefsForMode(dataset, dataMode, effectiveMetadata)
      .map((ref) => [contextCanvasEntityId(ref), ref]),
  );
  const rows = new Map(
    contextCanvasAccessibleRowsForMode(dataset, dataMode, effectiveMetadata)
      .map((row) => [row.id, row]),
  );
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

import type { TraceContextDataset } from "../types";
import { autoArrangeContextCanvas } from "./layout";
import { contextCanvasEntityRefsForMode } from "./model";
import {
  contextCanvasEntityId,
  type ContextCanvasComposition,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasEntityId,
  type ContextCanvasTemplateId,
} from "./types";

export interface ContextCanvasTemplateContract {
  readonly templateId: ContextCanvasTemplateId;
  readonly version: 1 | 2;
  readonly label: string;
  readonly description: string;
  readonly entitySelectionRule:
    | "overview-with-capacity"
    | "controlled-assignment-context"
    | "curated-membership-context"
    | "all-published-context"
    | "all-governed-representations";
  readonly initialLayoutRule: "typed-lanes-v1";
  readonly defaultZoomBehavior: "fit-content";
}

export const CONTEXT_CANVAS_TEMPLATES: readonly ContextCanvasTemplateContract[] = Object.freeze([
  Object.freeze({
    templateId: "context-overview",
    version: 1,
    label: "Context overview",
    description: "Selected object with a representative cross-section of its available context.",
    entitySelectionRule: "overview-with-capacity",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
  Object.freeze({
    templateId: "descriptive-context",
    version: 1,
    label: "Descriptive context",
    description: "Selected object and available controlled assignments.",
    entitySelectionRule: "controlled-assignment-context",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
  Object.freeze({
    templateId: "curated-context",
    version: 1,
    label: "Curated context",
    description: "Selected object and curated memberships or research pathways.",
    entitySelectionRule: "curated-membership-context",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
  Object.freeze({
    templateId: "full-context",
    version: 1,
    label: "Full context",
    description: "Every available entity and validated connection in this Context dataset.",
    entitySelectionRule: "all-published-context",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
]);

const CONTROLLED_VALIDATION_CONTEXT_CANVAS_TEMPLATES: readonly ContextCanvasTemplateContract[] = Object.freeze([
  Object.freeze({
    templateId: "context-overview",
    version: 2,
    label: "Controlled candidates",
    description: "Selected object and its validation-only controlled-assignment candidates.",
    entitySelectionRule: "controlled-assignment-context",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
]);

export const GOVERNED_CONTEXT_CANVAS_TEMPLATES: readonly ContextCanvasTemplateContract[] = Object.freeze([
  Object.freeze({
    templateId: "context-overview",
    version: 2,
    label: "Context overview",
    description: "Selected object and every governed controlled Context representation.",
    entitySelectionRule: "all-governed-representations",
    initialLayoutRule: "typed-lanes-v1",
    defaultZoomBehavior: "fit-content",
  }),
]);

export function getContextCanvasTemplatesForMode(
  dataMode: ContextCanvasDataMode,
): readonly ContextCanvasTemplateContract[] {
  if (dataMode === "synthetic_contract") return CONTEXT_CANVAS_TEMPLATES;
  if (dataMode === "real_v49_validation") return CONTROLLED_VALIDATION_CONTEXT_CANVAS_TEMPLATES;
  return GOVERNED_CONTEXT_CANVAS_TEMPLATES;
}

export function getContextCanvasTemplate(
  templateId: ContextCanvasTemplateId,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
): ContextCanvasTemplateContract {
  const template = getContextCanvasTemplatesForMode(dataMode)
    .find((item) => item.templateId === templateId);
  if (!template) throw new Error(`Unknown Context Canvas template: ${templateId}`);
  return template;
}

function sorted(values: Iterable<ContextCanvasEntityId>): readonly ContextCanvasEntityId[] {
  return Object.freeze([...new Set(values)].sort((left, right) => left.localeCompare(right, "en")));
}

function controlledEntityIds(dataset: TraceContextDataset): readonly ContextCanvasEntityId[] {
  return sorted(dataset.controlledAssignments.flatMap((item) => [
    contextCanvasEntityId(item.subject),
    contextCanvasEntityId(item.value),
  ]));
}

function curatedEntityIds(dataset: TraceContextDataset): readonly ContextCanvasEntityId[] {
  return sorted(dataset.curatedMemberships.flatMap((item) => [
    contextCanvasEntityId(item.member),
    contextCanvasEntityId(item.container),
  ]));
}

function allEntityIds(dataset: TraceContextDataset): readonly ContextCanvasEntityId[] {
  return sorted(dataset.items.map(contextCanvasEntityId));
}

export function selectContextCanvasTemplateEntities(
  dataset: TraceContextDataset,
  templateId: ContextCanvasTemplateId,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): readonly ContextCanvasEntityId[] {
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  if (dataMode === "real_v49_validation") {
    if (templateId !== "context-overview") {
      throw new Error(`Template ${templateId} is not available in real_v49_validation mode.`);
    }
    return sorted([rootId, ...controlledEntityIds(dataset)]);
  }
  if (dataMode === "governed_context_v1") {
    if (!metadata) throw new Error("Governed Context template initialization requires metadata.");
    if (templateId !== "context-overview") {
      throw new Error(`Template ${templateId} is not available in governed_context_v1 mode.`);
    }
    return sorted(contextCanvasEntityRefsForMode(dataset, dataMode, metadata).map(contextCanvasEntityId));
  }
  switch (templateId) {
    case "descriptive-context":
      return sorted([rootId, ...controlledEntityIds(dataset)]);
    case "curated-context":
      return sorted([rootId, ...curatedEntityIds(dataset)]);
    case "full-context":
      return allEntityIds(dataset);
    case "context-overview": {
      const all = allEntityIds(dataset);
      if (all.length <= 16) return all;
      const controlled = controlledEntityIds(dataset).filter((id) => id !== rootId).slice(0, 6);
      const curated = curatedEntityIds(dataset).filter((id) => id !== rootId).slice(0, 6);
      return sorted([rootId, ...controlled, ...curated]);
    }
  }
}

export function initializeContextCanvasTemplate(
  dataset: TraceContextDataset,
  templateId: ContextCanvasTemplateId,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): ContextCanvasComposition {
  const template = getContextCanvasTemplate(templateId, dataMode);
  const visibleEntityIds = selectContextCanvasTemplateEntities(dataset, templateId, dataMode, metadata);
  return Object.freeze({
    templateId,
    templateVersion: template.version,
    visibleEntityIds,
    positions: autoArrangeContextCanvas(dataset, visibleEntityIds, dataMode, metadata),
  });
}

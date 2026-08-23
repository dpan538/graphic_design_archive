import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const canvasRoot = join(frontendRoot, "src/features/trace-v49/context/canvas");
const routeRoot = join(frontendRoot, "src/app/trace/context-canvas");
const jiti = createJiti(import.meta.url, {
  alias: { "@": join(frontendRoot, "src") },
});

// Import the renderer-independent modules directly. Importing the canvas barrel would
// also load React components, which this pure contract verifier intentionally avoids.
const types = await jiti.import(join(canvasRoot, "types.ts"));
const templates = await jiti.import(join(canvasRoot, "templates.ts"));
const layout = await jiti.import(join(canvasRoot, "layout.ts"));
const connections = await jiti.import(join(canvasRoot, "connections.ts"));
const viewport = await jiti.import(join(canvasRoot, "viewport.ts"));
const stateModule = await jiti.import(join(canvasRoot, "state.ts"));
const reducerModule = await jiti.import(join(canvasRoot, "reducer.ts"));
const persistence = await jiti.import(join(canvasRoot, "persistence.ts"));
const exportPng = await jiti.import(join(canvasRoot, "export-png.ts"));
const displayLabel = await jiti.import(join(canvasRoot, "display-label.ts"));
const fixture = await jiti.import(join(canvasRoot, "fixture.ts"));

const dataset = fixture.CONTEXT_CANVAS_SYNTHETIC_DATASET;
const datasetSnapshot = JSON.stringify(dataset);
const rootEntityId = types.contextCanvasEntityId(dataset.selectedRecord);
const entityIdByLabel = (label) => {
  const ref = dataset.items.find((item) => item.label === label);
  assert.ok(ref, `missing fixture entity: ${label}`);
  return types.contextCanvasEntityId(ref);
};
const mediumEntityId = entityIdByLabel("Medium B");
const pathwayEntityId = entityIdByLabel("Pathway D");
const semanticPeerEntityId = entityIdByLabel("Object J");
const checks = [];

function check(id, action) {
  action();
  checks.push(id);
}

function sorted(values) {
  return [...values].sort((left, right) => left.localeCompare(right, "en"));
}

function assertFinitePosition(position) {
  assert.ok(position);
  assert.equal(Number.isFinite(position.x), true);
  assert.equal(Number.isFinite(position.y), true);
}

const templateIds = templates.CONTEXT_CANVAS_TEMPLATES.map((item) => item.templateId);
const expectedTemplateCounts = new Map([
  ["context-overview", 10],
  ["descriptive-context", 5],
  ["curated-context", 5],
  ["full-context", 10],
]);
const initializedTemplates = new Map(
  templateIds.map((templateId) => [
    templateId,
    templates.initializeContextCanvasTemplate(dataset, templateId),
  ]),
);
const fullComposition = initializedTemplates.get("full-context");
const descriptiveComposition = initializedTemplates.get("descriptive-context");
assert.ok(fullComposition);
assert.ok(descriptiveComposition);

check("CONTEXT-CANVAS-TEMPLATE-001 four deterministic initial templates", () => {
  assert.deepEqual(templateIds, [
    "context-overview",
    "descriptive-context",
    "curated-context",
    "full-context",
  ]);
  assert.equal(new Set(templateIds).size, 4);
  for (const contract of templates.CONTEXT_CANVAS_TEMPLATES) {
    const composition = initializedTemplates.get(contract.templateId);
    assert.ok(composition);
    assert.equal(contract.version, 1);
    assert.equal(contract.initialLayoutRule, "typed-lanes-v1");
    assert.equal(contract.defaultZoomBehavior, "fit-content");
    assert.ok(contract.label.trim());
    assert.ok(contract.description.trim());
    assert.equal(composition.templateId, contract.templateId);
    assert.equal(composition.templateVersion, contract.version);
    assert.equal(composition.visibleEntityIds.length, expectedTemplateCounts.get(contract.templateId));
    assert.equal(composition.visibleEntityIds.includes(rootEntityId), true);
    assert.deepEqual(sorted(Object.keys(composition.positions)), sorted(composition.visibleEntityIds));
    for (const entityId of composition.visibleEntityIds) {
      assertFinitePosition(composition.positions[entityId]);
    }
  }
});

const arrangedForward = layout.autoArrangeContextCanvas(dataset, fullComposition.visibleEntityIds);
const arrangedReverse = layout.autoArrangeContextCanvas(
  dataset,
  [...fullComposition.visibleEntityIds].reverse(),
);
const geometryForward = connections.buildContextCanvasConnectionGeometry(dataset, fullComposition);
const geometryAgain = connections.buildContextCanvasConnectionGeometry(dataset, fullComposition);

check("CONTEXT-CANVAS-LAYOUT-001 deterministic typed-lane layout", () => {
  assert.deepEqual(arrangedForward, fullComposition.positions);
  assert.deepEqual(arrangedReverse, arrangedForward);
  assert.equal(Object.keys(arrangedForward).length, fullComposition.visibleEntityIds.length);
  assert.equal(new Set(Object.values(arrangedForward).map(({ x, y }) => `${x}:${y}`)).size,
    fullComposition.visibleEntityIds.length);
});

check("CONTEXT-CANVAS-GEOMETRY-001 deterministic orthogonal geometry", () => {
  assert.deepEqual(geometryAgain, geometryForward);
  assert.equal(geometryForward.length, 9);
  for (const item of geometryForward) {
    assert.match(item.path, /^M -?\d+(?:\.\d+)? -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)? V -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)?$/);
    assert.doesNotMatch(item.path, /NaN|Infinity/);
    assert.ok(item.accessibleLabel.startsWith(`${item.connection.connectionKind}:`));
  }
});

const emptyBounds = layout.computeContextCanvasBounds([], {});
const oneNodePositions = { [rootEntityId]: { x: 50, y: 30 } };
const oneNodeBounds = layout.computeContextCanvasBounds([rootEntityId], oneNodePositions);
const oneNodeFit = layout.fitContextCanvasViewport(oneNodeBounds, { width: 800, height: 600 }, 56);

check("CONTEXT-CANVAS-FIT-001 empty and one-node content", () => {
  assert.deepEqual(emptyBounds, { x: 0, y: 0, width: 0, height: 0, empty: true });
  assert.deepEqual(layout.fitContextCanvasViewport(emptyBounds, { width: 800, height: 600 }), {
    x: 0,
    y: 0,
    zoom: 1,
  });
  assert.deepEqual(oneNodeBounds, {
    x: 50,
    y: 30,
    width: types.CONTEXT_CANVAS_NODE_WIDTH,
    height: types.CONTEXT_CANVAS_NODE_HEIGHT,
    empty: false,
  });
  assert.deepEqual(
    layout.fitContextCanvasViewport(oneNodeBounds, { width: 800, height: 600 }, 56),
    oneNodeFit,
  );
  assert.ok(oneNodeFit.zoom >= types.CONTEXT_CANVAS_MIN_ZOOM);
  assert.ok(oneNodeFit.zoom <= types.CONTEXT_CANVAS_MAX_ZOOM);
  assertFinitePosition(oneNodeFit);
});

check("CONTEXT-CANVAS-VIEWPORT-001 world-screen conversion and safe viewport", () => {
  const world = { x: 19.25, y: -8.5 };
  const view = { x: 120, y: -35, zoom: 1.75 };
  const screen = viewport.contextCanvasWorldToScreen(world, view);
  const roundTrip = viewport.contextCanvasScreenToWorld(screen, view);
  assert.ok(Math.abs(roundTrip.x - world.x) < 1e-10);
  assert.ok(Math.abs(roundTrip.y - world.y) < 1e-10);

  const anchored = { x: 417, y: 263 };
  const anchoredWorld = viewport.contextCanvasScreenToWorld(anchored, view);
  const zoomed = viewport.zoomContextCanvasAtPoint(view, anchored, 2.25);
  const anchoredAfterZoom = viewport.contextCanvasWorldToScreen(anchoredWorld, zoomed);
  assert.ok(Math.abs(anchoredAfterZoom.x - anchored.x) < 1e-10);
  assert.ok(Math.abs(anchoredAfterZoom.y - anchored.y) < 1e-10);
  assert.deepEqual(
    viewport.panContextCanvasFromPointer(view, { x: 10, y: 20 }, { x: 25, y: 8 }),
    { x: 135, y: -47, zoom: 1.75 },
  );
  assert.deepEqual(viewport.sanitizeContextCanvasViewport({ x: Number.NaN, y: Infinity, zoom: -Infinity }), {
    x: 0,
    y: 0,
    zoom: 1,
  });
});

const initializingState = stateModule.createInitializingContextCanvasState(dataset);
const readyDescriptiveState = reducerModule.contextCanvasReducer(initializingState, {
  type: "INITIALIZE",
  composition: descriptiveComposition,
  viewport: { x: 11, y: -17, zoom: 1.2 },
});
const addedState = reducerModule.contextCanvasReducer(readyDescriptiveState, {
  type: "ADD_ENTITY",
  entityId: pathwayEntityId,
  position: { x: 913, y: 407 },
});
const duplicateState = reducerModule.contextCanvasReducer(addedState, {
  type: "ADD_ENTITY",
  entityId: pathwayEntityId,
  position: { x: -999, y: -999 },
});
const hiddenState = reducerModule.contextCanvasReducer(addedState, {
  type: "HIDE_ENTITY",
  entityId: pathwayEntityId,
});
const rootHideState = reducerModule.contextCanvasReducer(addedState, {
  type: "HIDE_ENTITY",
  entityId: rootEntityId,
});
const dragStartedState = reducerModule.contextCanvasReducer(addedState, {
  type: "BEGIN_NODE_DRAG",
  nodeId: pathwayEntityId,
  pointerId: 7,
  startClient: { x: 100, y: 80 },
});
const dragPreviewState = reducerModule.contextCanvasReducer(dragStartedState, {
  type: "PREVIEW_NODE_DRAG",
  position: { x: 777, y: 333 },
});
const dragCommittedState = reducerModule.contextCanvasReducer(dragPreviewState, {
  type: "END_NODE_DRAG",
});
const customViewportState = reducerModule.contextCanvasReducer(dragCommittedState, {
  type: "SET_VIEWPORT",
  viewport: { x: 123, y: -45, zoom: 1.4 },
});
const autoPositions = layout.autoArrangeContextCanvas(
  dataset,
  customViewportState.history.present.visibleEntityIds,
);
const autoArrangedState = reducerModule.contextCanvasReducer(customViewportState, {
  type: "AUTO_ARRANGE",
  positions: autoPositions,
});
const undoneState = reducerModule.contextCanvasReducer(autoArrangedState, { type: "UNDO" });
const redoneState = reducerModule.contextCanvasReducer(undoneState, { type: "REDO" });

check("CONTEXT-CANVAS-REDUCER-001 add, duplicate, hide, root, drag, auto, undo, redo", () => {
  assert.equal(readyDescriptiveState.phase, "READY");
  assert.equal(readyDescriptiveState.history.present.visibleEntityIds.includes(pathwayEntityId), false);
  assert.equal(addedState.history.present.visibleEntityIds.includes(pathwayEntityId), true);
  assert.deepEqual(addedState.history.present.positions[pathwayEntityId], { x: 913, y: 407 });
  assert.deepEqual(addedState.selection, { kind: "node", id: pathwayEntityId });
  assert.equal(addedState.history.past.length, readyDescriptiveState.history.past.length + 1);

  assert.deepEqual(duplicateState.history.present, addedState.history.present);
  assert.equal(duplicateState.history.present.visibleEntityIds.filter((id) => id === pathwayEntityId).length, 1);
  assert.equal(duplicateState.history.past.length, addedState.history.past.length);
  assert.deepEqual(duplicateState.selection, { kind: "node", id: pathwayEntityId });

  assert.equal(hiddenState.history.present.visibleEntityIds.includes(pathwayEntityId), false);
  assert.equal(pathwayEntityId in hiddenState.history.present.positions, false);
  assert.deepEqual(rootHideState.history.present, addedState.history.present);
  assert.equal(rootHideState.history.present.visibleEntityIds.includes(rootEntityId), true);
  assert.match(rootHideState.statusMessage, /cannot be removed/i);

  assert.equal(dragStartedState.interaction.mode, "NODE_DRAGGING");
  assert.deepEqual(dragPreviewState.history.present.positions[pathwayEntityId], { x: 777, y: 333 });
  assert.equal(dragPreviewState.history.past.length, addedState.history.past.length);
  assert.equal(dragCommittedState.interaction.mode, "READY");
  assert.equal(dragCommittedState.history.past.length, addedState.history.past.length + 1);
  assert.deepEqual(dragCommittedState.selection, { kind: "node", id: pathwayEntityId });

  assert.deepEqual(autoArrangedState.history.present.positions, autoPositions);
  assert.deepEqual(undoneState.history.present, customViewportState.history.present);
  assert.deepEqual(redoneState.history.present, autoArrangedState.history.present);
  assert.deepEqual(undoneState.viewport, customViewportState.viewport);
  assert.deepEqual(redoneState.viewport, customViewportState.viewport);
});

check("CONTEXT-CANVAS-REDUCER-002 template switch and reset", () => {
  const switched = reducerModule.contextCanvasReducer(readyDescriptiveState, {
    type: "APPLY_TEMPLATE",
    composition: fullComposition,
  });
  assert.deepEqual(switched.history.present, fullComposition);
  assert.equal(switched.history.past.length, 1);
  assert.deepEqual(
    reducerModule.contextCanvasReducer(switched, { type: "UNDO" }).history.present,
    descriptiveComposition,
  );

  const reset = reducerModule.contextCanvasReducer(switched, {
    type: "RESET_CANVAS",
    composition: descriptiveComposition,
  });
  assert.deepEqual(reset.history.present, descriptiveComposition);
  assert.equal(reset.history.past.length, 0);
  assert.equal(reset.history.future.length, 0);
});

check("CONTEXT-CANVAS-REDUCER-003 export cancellation restores ready state", () => {
  const exporting = reducerModule.contextCanvasReducer(redoneState, { type: "EXPORT_START" });
  assert.equal(exporting.phase, "EXPORTING");
  assert.equal(exporting.interaction.mode, "READY");
  const recovered = reducerModule.contextCanvasReducer(exporting, { type: "EXPORT_CANCEL" });
  assert.equal(recovered.phase, "READY");
  assert.equal(recovered.exportError, null);
  assert.equal(recovered.interaction.mode, "READY");
  assert.deepEqual(recovered.history, exporting.history);
  assert.deepEqual(recovered.viewport, exporting.viewport);
  assert.deepEqual(recovered.selection, exporting.selection);
  assert.match(recovered.statusMessage, /export cancelled/i);
  assert.strictEqual(
    reducerModule.contextCanvasReducer(recovered, { type: "EXPORT_CANCEL" }),
    recovered,
  );
});

let boundedHistoryState = readyDescriptiveState;
for (let index = 0; index < 55; index += 1) {
  boundedHistoryState = reducerModule.contextCanvasReducer(boundedHistoryState, {
    type: "MOVE_NODE_BY",
    entityId: rootEntityId,
    delta: { x: 1, y: 0 },
  });
}

check("CONTEXT-CANVAS-HISTORY-001 bounded fifty-state undo and redo", () => {
  assert.equal(types.CONTEXT_CANVAS_HISTORY_LIMIT, 50);
  assert.equal(boundedHistoryState.history.past.length, 50);
  assert.equal(boundedHistoryState.history.future.length, 0);

  let state = boundedHistoryState;
  let undoCount = 0;
  while (state.history.past.length > 0) {
    state = reducerModule.contextCanvasReducer(state, { type: "UNDO" });
    undoCount += 1;
  }
  assert.equal(undoCount, 50);
  assert.equal(state.history.future.length, 50);

  let redoCount = 0;
  while (state.history.future.length > 0) {
    state = reducerModule.contextCanvasReducer(state, { type: "REDO" });
    redoCount += 1;
  }
  assert.equal(redoCount, 50);
  assert.equal(state.history.past.length, 50);
  assert.deepEqual(state.history.present, boundedHistoryState.history.present);
});

const persistedState = reducerModule.contextCanvasReducer(redoneState, {
  type: "SET_VIEWPORT",
  viewport: { x: 19, y: -23, zoom: 1.25 },
});
const serializedWorkspace = persistence.serializeContextCanvasWorkspace(persistedState);
const serializedPayload = JSON.parse(serializedWorkspace);
const restoredWorkspace = persistence.deserializeContextCanvasWorkspace(serializedWorkspace, dataset);

check("CONTEXT-CANVAS-PERSISTENCE-001 roundtrip, storage helpers, and version reset", () => {
  assert.ok(restoredWorkspace);
  assert.deepEqual(restoredWorkspace.composition, persistedState.history.present);
  assert.deepEqual(restoredWorkspace.viewport, persistedState.viewport);
  assert.equal(persistence.serializeContextCanvasWorkspace(persistedState), serializedWorkspace);

  const schemaMismatch = JSON.stringify({
    ...serializedPayload,
    schemaVersion: serializedPayload.schemaVersion + 1,
  });
  const catalogMismatch = JSON.stringify({
    ...serializedPayload,
    templateCatalogVersion: serializedPayload.templateCatalogVersion + 1,
  });
  const templateMismatch = JSON.stringify({
    ...serializedPayload,
    templateVersion: serializedPayload.templateVersion + 1,
  });
  assert.equal(persistence.deserializeContextCanvasWorkspace(schemaMismatch, dataset), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace(catalogMismatch, dataset), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace(templateMismatch, dataset), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace("not-json", dataset), null);

  const resetAfterMismatch = reducerModule.contextCanvasReducer(
    stateModule.createInitializingContextCanvasState(dataset),
    { type: "INITIALIZE" },
  );
  assert.deepEqual(
    resetAfterMismatch.history.present,
    templates.initializeContextCanvasTemplate(dataset, "context-overview"),
  );

  const memory = new Map();
  const storage = {
    getItem: (key) => memory.get(key) ?? null,
    setItem: (key, value) => memory.set(key, value),
    removeItem: (key) => memory.delete(key),
  };
  assert.equal(persistence.saveContextCanvasWorkspace(dataset, persistedState, storage), true);
  assert.deepEqual(persistence.loadContextCanvasWorkspace(dataset, storage), restoredWorkspace);
  assert.equal(persistence.clearContextCanvasWorkspace(dataset, storage), true);
  assert.equal(persistence.loadContextCanvasWorkspace(dataset, storage), null);
});

const visibleConnections = connections.deriveVisibleContextCanvasConnections(
  dataset,
  redoneState.history.present.visibleEntityIds,
);
const selectedNodeState = reducerModule.contextCanvasReducer(redoneState, {
  type: "SELECT",
  selection: { kind: "node", id: mediumEntityId },
});
const selectedConnectionState = reducerModule.contextCanvasReducer(selectedNodeState, {
  type: "SELECT",
  selection: { kind: "connection", id: visibleConnections[0].id },
});
const clearedSelectionState = reducerModule.contextCanvasReducer(selectedConnectionState, {
  type: "SELECT",
  selection: null,
});

check("CONTEXT-CANVAS-SELECTION-001 zero-or-one primary selection", () => {
  assert.deepEqual(selectedNodeState.selection, { kind: "node", id: mediumEntityId });
  assert.equal(stateModule.contextCanvasFunctionalState(selectedNodeState), "NODE_SELECTED");
  assert.deepEqual(selectedConnectionState.selection, {
    kind: "connection",
    id: visibleConnections[0].id,
  });
  assert.equal(stateModule.contextCanvasFunctionalState(selectedConnectionState), "CONNECTION_SELECTED");
  assert.equal(clearedSelectionState.selection, null);
  assert.equal(stateModule.contextCanvasFunctionalState(clearedSelectionState), "READY");
});

const exportSnapshot = exportPng.prepareContextCanvasExportSvg(dataset, fullComposition);
const exportSnapshotAgain = exportPng.prepareContextCanvasExportSvg(dataset, fullComposition);
const fixedInstant = new Date("2026-08-23T08:30:45.123Z");
const safeFilename = exportPng.buildContextCanvasPngFilename("../../Object A / unsafe?", fixedInstant);
const uuid = "123e4567-e89b-12d3-a456-426614174000";
const uuidFilename = exportPng.buildContextCanvasPngFilename(uuid, fixedInstant);

check("CONTEXT-CANVAS-EXPORT-001 deterministic canvas-only SVG and safe PNG filename", () => {
  assert.deepEqual(exportSnapshotAgain, exportSnapshot);
  assert.equal(types.CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE, 2);
  assert.match(exportSnapshot.svg, /^<svg /);
  assert.match(exportSnapshot.svg, /Object A/);
  assert.match(exportSnapshot.svg, /data-connection-kind="controlled_assignment"/);
  assert.match(exportSnapshot.svg, /data-connection-kind="curated_membership"/);
  assert.match(exportSnapshot.svg, /data-connection-kind="semantic_edge"/);
  assert.equal((exportSnapshot.svg.match(/data-entity-kind=/g) ?? []).length, fullComposition.visibleEntityIds.length);
  assert.equal((exportSnapshot.svg.match(/data-connection-kind=/g) ?? []).length, 9);
  assert.doesNotMatch(exportSnapshot.svg, /<button|toolbar|sidebar|inspector|application chrome|aria-selected|focus-ring|hover/i);
  assert.equal(exportSnapshot.width, Math.ceil(exportSnapshot.contentBounds.width + 96));
  assert.equal(exportSnapshot.height, Math.ceil(exportSnapshot.contentBounds.height + 96 + 44));
  assert.equal(safeFilename, "context-canvas-Object-A-unsafe-20260823T083045Z.png");
  assert.match(safeFilename, /^[a-z0-9_-]+\.png$/i);
  assert.doesNotMatch(safeFilename.slice(0, -4), /[/\\.?]/);
  assert.match(uuidFilename, /context-canvas-public-record-/);
  assert.doesNotMatch(uuidFilename, new RegExp(uuid, "i"));
  assert.equal(
    exportPng.buildContextCanvasPngFilename("safe-id", new Date(Number.NaN)),
    "context-canvas-safe-id-undated.png",
  );
});

const longFooterPublicId = `SURF-${"LONG-PUBLIC-ID-".repeat(12)}END`;
const longFooterReleaseId = `trace-v49-${"long-validation-release-".repeat(10)}end`;
const longFooterText = `Context Canvas · ${longFooterPublicId} · ${longFooterReleaseId}`;
const longFooterDataset = Object.freeze({
  ...dataset,
  release: Object.freeze({ ...dataset.release, releaseId: longFooterReleaseId }),
  selectedRecord: Object.freeze({ ...dataset.selectedRecord, stableId: longFooterPublicId }),
});
const emptyFooterComposition = Object.freeze({
  ...fullComposition,
  visibleEntityIds: Object.freeze([]),
  positions: Object.freeze({}),
});
const longFooterSnapshot = exportPng.prepareContextCanvasExportSvg(
  longFooterDataset,
  emptyFooterComposition,
);

check("CONTEXT-CANVAS-EXPORT-002 long metadata footer fits conservative width", () => {
  const padding = 48;
  const conservativeFooterWidth = Array.from(longFooterText).length * 8 + padding * 2;
  assert.equal(longFooterSnapshot.width, Math.ceil(conservativeFooterWidth));
  assert.ok(padding + Array.from(longFooterText).length * 8 <= longFooterSnapshot.width - padding);
  assert.match(
    longFooterSnapshot.svg,
    new RegExp(escapeRegExp(displayLabel.escapeContextCanvasXml(longFooterText)), "u"),
  );
  assert.match(longFooterSnapshot.svg, new RegExp(`width="${longFooterSnapshot.width}"`, "u"));
  assert.deepEqual(longFooterSnapshot.contentBounds, {
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    empty: true,
  });
});

const hostileFullLabel = "👩🏽‍💻e\u0301漢字 & <tag> \"quoted\" 'apostrophe' \u0096 "
  + "a deliberately long suffix that must be shortened without splitting a grapheme";
const hostileFittedLabel = displayLabel.fitContextCanvasDisplayLabel(hostileFullLabel, 14);
const hostileDefaultFittedLabel = displayLabel.fitContextCanvasDisplayLabel(hostileFullLabel);
const hostileRootRef = Object.freeze({ ...dataset.selectedRecord, label: hostileFullLabel });
const hostileDataset = Object.freeze({
  ...dataset,
  selectedRecord: hostileRootRef,
  items: Object.freeze(dataset.items.map((item) =>
    types.contextCanvasEntityId(item) === rootEntityId ? hostileRootRef : item)),
});
const hostileExportSnapshot = exportPng.prepareContextCanvasExportSvg(
  hostileDataset,
  fullComposition,
);

check("CONTEXT-CANVAS-LABEL-001 hostile grapheme, XML, full-label, and export parity", () => {
  assert.equal(displayLabel.CONTEXT_CANVAS_DISPLAY_LABEL_POLICY_VERSION, 1);
  assert.equal(hostileFittedLabel.fullText, hostileFullLabel);
  assert.equal(hostileFittedLabel.truncated, true);
  assert.match(hostileFittedLabel.displayText, /…$/u);
  assert.doesNotMatch(hostileFittedLabel.displayText, /[\ud800-\udfff]$/u);
  assert.equal(
    displayLabel.fitContextCanvasDisplayLabel(hostileFittedLabel.displayText, 14).truncated,
    false,
  );
  const untitledFallback = displayLabel.fitContextCanvasDisplayLabel("\u0000\t  ");
  assert.equal(untitledFallback.fullText, "\u0000\t  ");
  assert.equal(untitledFallback.displayText, "Untitled");
  assert.equal(untitledFallback.graphemeCount, 8);
  assert.ok(untitledFallback.displayUnitCount >= untitledFallback.graphemeCount);
  assert.equal(untitledFallback.truncated, false);

  const escaped = displayLabel.escapeContextCanvasXml(hostileFullLabel);
  assert.match(escaped, /&amp;/u);
  assert.match(escaped, /&lt;tag&gt;/u);
  assert.match(escaped, /&quot;quoted&quot;/u);
  assert.match(escaped, /&apos;apostrophe&apos;/u);
  assert.match(escaped, /&#x96;/u);
  assert.doesNotMatch(escaped, /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/u);
  assert.equal(hostileFittedLabel.fullText, hostileFullLabel);

  const fullTitle = displayLabel.escapeContextCanvasXml(
    `${hostileFullLabel} (${hostileRootRef.kind})`,
  );
  assert.match(hostileExportSnapshot.svg, new RegExp(`<title>${escapeRegExp(fullTitle)}</title>`, "u"));
  assert.match(
    hostileExportSnapshot.svg,
    new RegExp(escapeRegExp(displayLabel.escapeContextCanvasXml(hostileDefaultFittedLabel.displayText)), "u"),
  );
  assert.doesNotMatch(hostileExportSnapshot.svg, /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/u);
  assert.equal(hostileDataset.selectedRecord.label, hostileFullLabel);
  assert.equal(JSON.stringify(dataset), datasetSnapshot);
});

check("CONTEXT-CANVAS-LABEL-003 lone surrogates are display-safe and source-preserving", () => {
  for (const source of ["before\ud800after", "before\udc00after"]) {
    const fitted = displayLabel.fitContextCanvasDisplayLabel(source);
    assert.equal(fitted.fullText, source);
    assert.equal(fitted.displayText, "before\ufffdafter");
    assert.equal(fitted.truncated, false);
    assert.doesNotMatch(fitted.displayText, /[\ud800-\udfff]/u);
    assert.equal(displayLabel.escapeContextCanvasXml(source), "before&#xFFFD;after");
    assert.equal(displayLabel.escapeContextCanvasXml(fitted.displayText), "before\ufffdafter");
  }
  const validPair = "before\ud83d\ude00after";
  assert.equal(displayLabel.fitContextCanvasDisplayLabel(validPair).fullText, validPair);
  assert.match(displayLabel.fitContextCanvasDisplayLabel(validPair).displayText, /😀/u);
});

check("CONTEXT-CANVAS-A11Y-001 every visible connection has a typed row", () => {
  const rows = new Map(dataset.accessibleRows.map((row) => [row.id, row]));
  const expectedCategory = {
    controlled_assignment: "controlled_assignment",
    curated_membership: "curated_membership",
    semantic_edge: "accepted_semantic_edge",
  };
  assert.equal(geometryForward.length, 9);
  for (const item of geometryForward) {
    const row = rows.get(item.connection.accessibleRowId);
    assert.ok(row, `missing accessible row: ${item.connection.accessibleRowId}`);
    assert.equal(row.category, expectedCategory[item.connection.connectionKind]);
    assert.ok(row.label.trim());
    assert.ok(item.accessibleLabel.includes(row.label));
  }
  assert.ok(dataset.accessibleRows.some((row) => row.category === "selected_record"));
});

const codeFiles = [
  ...await walkCodeFiles(canvasRoot),
  ...await walkCodeFiles(routeRoot),
];
const sourceEntries = await Promise.all(codeFiles.map(async (path) => [path, await readFile(path, "utf8")]));
const importRecords = sourceEntries.flatMap(([path, source]) =>
  importSpecifiers(source).map((specifier) => ({ path, specifier }))
);
const reducerSource = sourceEntries.find(([path]) => path === join(canvasRoot, "reducer.ts"))?.[1] ?? "";
const canvasSource = sourceEntries.map(([, source]) => source).join("\n");

check("CONTEXT-CANVAS-LABEL-002 renderer and export share the display-label policy", () => {
  const nodeSource = sourceEntries.find(([path]) => path === join(canvasRoot, "ContextCanvasNode.tsx"))?.[1] ?? "";
  const connectionSource = sourceEntries.find(([path]) => path === join(canvasRoot, "ContextCanvasConnections.tsx"))?.[1] ?? "";
  const exportSource = sourceEntries.find(([path]) => path === join(canvasRoot, "export-png.ts"))?.[1] ?? "";
  for (const source of [nodeSource, connectionSource, exportSource]) {
    assert.match(source, /fitContextCanvasDisplayLabel/u);
    assert.match(source, /\.\/display-label/u);
  }
  assert.match(nodeSource, /contextCanvasFullLabel/u);
  assert.match(exportSource, /contextCanvasFullLabel/u);
  assert.match(nodeSource, /<title>/u);
  assert.match(connectionSource, /<title>/u);
  assert.match(exportSource, /<title>/u);
});

check("CTX-CANVAS-INV-001 composition never mutates TraceContextDataset", () => {
  assert.equal(JSON.stringify(dataset), datasetSnapshot);
  assert.equal(initializingState.rootEntityId, rootEntityId);
  assert.equal(initializingState.history.present === dataset, false);
  assert.equal("dataset" in initializingState, false);
});

check("CTX-CANVAS-INV-002 adding an entity never creates semantic data", () => {
  assert.equal(dataset.semanticEdges.length, 1);
  assert.equal(JSON.stringify(dataset), datasetSnapshot);
  assert.deepEqual(
    Object.keys(addedState.history.present).sort(),
    ["positions", "templateId", "templateVersion", "visibleEntityIds"],
  );
  assert.doesNotMatch(JSON.stringify(addedState.history.present), /semanticEdges|controlledAssignments|curatedMemberships|evidenceRefs/);
});

check("CTX-CANVAS-INV-003 connections require underlying dataset records", () => {
  const sourceConnectionIds = sorted([
    ...dataset.controlledAssignments.map((item) => `connection:controlled_assignment:${item.id}`),
    ...dataset.curatedMemberships.map((item) => `connection:curated_membership:${item.id}`),
    ...dataset.semanticEdges.map((item) => `connection:semantic_edge:${item.id}`),
  ]);
  assert.deepEqual(geometryForward.map((item) => item.connection.id), sourceConnectionIds);
  assert.deepEqual(
    connections.deriveVisibleContextCanvasConnections(dataset, [mediumEntityId, pathwayEntityId]),
    [],
  );
  assert.equal(
    connections.deriveVisibleContextCanvasConnections(
      dataset,
      [rootEntityId, semanticPeerEntityId],
    ).every((item) => item.connectionKind === "semantic_edge"),
    true,
  );
});

check("CTX-CANVAS-INV-004 no manual semantic-edge authoring action", () => {
  const actionNames = [...reducerSource.matchAll(/\btype:\s*"([A-Z_]+)"/g)].map((match) => match[1]);
  assert.ok(actionNames.includes("ADD_ENTITY"));
  assert.equal(actionNames.some((name) => /(?:CREATE|ADD|DRAW|EDIT|UPDATE)_(?:EDGE|RELATION|RELATIONSHIP|CONNECTION)/.test(name)), false);
  assert.doesNotMatch(canvasSource, /Add Relationship|Create Relationship|Draw (?:an? )?Edge/i);
});

check("CTX-CANVAS-INV-005 ControlledAssignment remains distinct from CuratedMembership", () => {
  const assignment = visibleConnections.find((item) => item.connectionKind === "controlled_assignment");
  const membership = visibleConnections.find((item) => item.connectionKind === "curated_membership");
  assert.ok(assignment);
  assert.ok(membership);
  assert.ok("assignment" in assignment);
  assert.equal("membership" in assignment, false);
  assert.ok("membership" in membership);
  assert.equal("assignment" in membership, false);
  assert.notEqual(assignment.accessibleRowId.split(":")[0], membership.accessibleRowId.split(":")[0]);
});

check("CTX-CANVAS-INV-006 SemanticEdge remains a distinct connection class", () => {
  const semantic = geometryForward.find((item) => item.connection.connectionKind === "semantic_edge")?.connection;
  assert.ok(semantic);
  assert.ok("semanticEdge" in semantic);
  assert.equal("assignment" in semantic, false);
  assert.equal("membership" in semantic, false);
  assert.equal(semantic.semanticEdge.semantic, true);
  assert.equal(semantic.semanticEdge.status, "accepted");
});

check("CTX-CANVAS-INV-007 hiding preserves source entities and relations", () => {
  assert.equal(hiddenState.history.present.visibleEntityIds.includes(pathwayEntityId), false);
  assert.equal(dataset.items.some((item) => types.contextCanvasEntityId(item) === pathwayEntityId), true);
  assert.equal(dataset.curatedMemberships.some((item) =>
    types.contextCanvasEntityId(item.container) === pathwayEntityId), true);
  assert.equal(connections.deriveVisibleContextCanvasConnections(
    dataset,
    hiddenState.history.present.visibleEntityIds,
  ).some((item) => item.targetEntityId === pathwayEntityId), false);
  assert.equal(JSON.stringify(dataset), datasetSnapshot);
});

check("CTX-CANVAS-INV-008 duplicate palette drop focuses one existing node", () => {
  assert.deepEqual(duplicateState.history.present, addedState.history.present);
  assert.equal(duplicateState.history.present.visibleEntityIds.filter((id) => id === pathwayEntityId).length, 1);
  assert.deepEqual(duplicateState.selection, { kind: "node", id: pathwayEntityId });
});

check("CTX-CANVAS-INV-009 template initialization is deterministic", () => {
  for (const templateId of templateIds) {
    assert.deepEqual(
      templates.initializeContextCanvasTemplate(dataset, templateId),
      initializedTemplates.get(templateId),
    );
  }
});

check("CTX-CANVAS-INV-010 Auto Arrange is deterministic", () => {
  assert.deepEqual(
    layout.autoArrangeContextCanvas(dataset, fullComposition.visibleEntityIds),
    arrangedForward,
  );
  assert.deepEqual(arrangedReverse, arrangedForward);
});

check("CTX-CANVAS-INV-011 positions produce deterministic SVG geometry", () => {
  assert.deepEqual(
    connections.buildContextCanvasConnectionGeometry(dataset, fullComposition),
    geometryForward,
  );
  assert.deepEqual(exportPng.prepareContextCanvasExportSvg(dataset, fullComposition), exportSnapshot);
});

check("CTX-CANVAS-INV-012 undo and redo affect composition only", () => {
  assert.deepEqual(undoneState.history.present, customViewportState.history.present);
  assert.deepEqual(redoneState.history.present, autoArrangedState.history.present);
  assert.deepEqual(undoneState.viewport, customViewportState.viewport);
  assert.deepEqual(redoneState.viewport, customViewportState.viewport);
  assert.equal(undoneState.rootEntityId, customViewportState.rootEntityId);
  assert.deepEqual(undoneState.allowedEntityIds, customViewportState.allowedEntityIds);
  assert.equal(JSON.stringify(dataset), datasetSnapshot);
});

check("CTX-CANVAS-INV-013 persistence contains public IDs and positions, not canonical objects", () => {
  assert.deepEqual(Object.keys(serializedPayload).sort(), [
    "positions",
    "schemaVersion",
    "templateCatalogVersion",
    "templateId",
    "templateVersion",
    "viewport",
    "visibleEntityIds",
  ]);
  assert.deepEqual(sorted(Object.keys(serializedPayload.positions)), sorted(serializedPayload.visibleEntityIds));
  assert.ok(serializedPayload.visibleEntityIds.every((id) =>
    typeof id === "string" && id.startsWith("entity:")));
  for (const position of Object.values(serializedPayload.positions)) {
    assert.deepEqual(Object.keys(position).sort(), ["x", "y"]);
    assertFinitePosition(position);
  }
  const forbiddenPayloadKeys = new Set([
    "assignment",
    "assignmentType",
    "availability",
    "container",
    "controlledAssignments",
    "curatedMemberships",
    "evidenceRefs",
    "label",
    "member",
    "membership",
    "membershipType",
    "semanticEdge",
    "semanticEdges",
    "subject",
    "value",
    "warnings",
  ]);
  assert.deepEqual(
    [...collectKeys(serializedPayload)].filter((key) => forbiddenPayloadKeys.has(key)),
    [],
  );
});

check("CTX-CANVAS-INV-014 fixture and export contain no held/private/internal identifiers", () => {
  const fixtureText = JSON.stringify({
    metadata: fixture.CONTEXT_CANVAS_FIXTURE_METADATA,
    input: fixture.CONTEXT_CANVAS_SYNTHETIC_INPUT,
    dataset,
  });
  const uuidPattern = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/i;
  assert.deepEqual(fixture.CONTEXT_CANVAS_FIXTURE_METADATA, {
    dataLabel: "synthetic contract fixture",
    mappingVersion: "synthetic-context-contract-v1",
    candidateState: "synthetic_contract",
    historicalEvidence: false,
    governedPublicRelease: false,
    publicReleaseData: false,
    publicObjectCohortCount: 2,
  });
  assert.doesNotMatch(fixtureText, uuidPattern);
  assert.doesNotMatch(fixtureText, /"(?:held|private|internalUuid|internalId)"\s*:/i);
  assert.doesNotMatch(exportSnapshot.svg, uuidPattern);
  assert.doesNotMatch(exportSnapshot.svg, /held state|private source|raw payload|internal uuid/i);
  assert.doesNotMatch(uuidFilename, uuidPattern);
});

check("CTX-CANVAS-INV-015 PNG snapshot contains canvas content, not application chrome", () => {
  assert.equal(types.CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE, 2);
  assert.equal((exportSnapshot.svg.match(/<path d=/g) ?? []).length >= geometryForward.length, true);
  assert.equal((exportSnapshot.svg.match(/data-entity-kind=/g) ?? []).length, fullComposition.visibleEntityIds.length);
  assert.doesNotMatch(exportSnapshot.svg, /toolbar|sidebar|inspector|palette|undo|redo|export png/i);
});

check("CTX-CANVAS-INV-016 visible connections have accessible-row equivalents", () => {
  const rowIds = new Set(dataset.accessibleRows.map((row) => row.id));
  assert.equal(geometryForward.every((item) => rowIds.has(item.connection.accessibleRowId)), true);
  assert.equal(new Set(geometryForward.map((item) => item.connection.accessibleRowId)).size,
    geometryForward.length);
});

check("CTX-CANVAS-INV-017 no v48 TRACE import", () => {
  const forbidden = importRecords.filter(({ specifier }) => /trace[-_/]?v48|public\/data\/trace-v48/i.test(specifier));
  assert.deepEqual(forbidden, []);
});

check("CTX-CANVAS-INV-018 no Search, AI, embedding, map, Spacetime, or Exploration import", () => {
  const forbiddenImport = /(?:^|[/@._-])(?:search(?:-v\d+)?|ai|llm|openai|embeddings?|vectors?|spacetime|maps?|mapping|geography|d3-geo|topojson|exploration(?:-field)?)(?=$|[/@._-])/i;
  const forbidden = importRecords.filter(({ specifier }) => forbiddenImport.test(specifier));
  assert.deepEqual(forbidden, []);
});

assert.equal(
  dataset.controlledAssignments.length
    + dataset.curatedMemberships.length
    + dataset.semanticEdges.length,
  9,
  "benchmark fixture must retain the synthetic nine-association maximum workload",
);

const benchmarkBaseState = reducerModule.contextCanvasReducer(
  stateModule.createInitializingContextCanvasState(dataset),
  { type: "INITIALIZE", composition: fullComposition },
);
let benchmarkSink = 0;

function runSyntheticMaxWorkload() {
  const composition = templates.initializeContextCanvasTemplate(dataset, "full-context");
  const positions = layout.autoArrangeContextCanvas(dataset, composition.visibleEntityIds);
  const visible = connections.deriveVisibleContextCanvasConnections(
    dataset,
    composition.visibleEntityIds,
  );
  const bounds = layout.computeContextCanvasBounds(composition.visibleEntityIds, positions);
  const fitted = layout.fitContextCanvasViewport(bounds, { width: 1_280, height: 760 });
  const reduced = reducerModule.contextCanvasReducer(benchmarkBaseState, {
    type: "MOVE_NODE_BY",
    entityId: rootEntityId,
    delta: { x: 1, y: 1 },
  });
  benchmarkSink += visible.length + fitted.zoom + reduced.history.past.length;
}

for (let index = 0; index < 250; index += 1) runSyntheticMaxWorkload();
const timings = [];
for (let index = 0; index < 1_000; index += 1) {
  const started = performance.now();
  runSyntheticMaxWorkload();
  timings.push(performance.now() - started);
}
timings.sort((left, right) => left - right);
const p95Ms = timings[Math.ceil(timings.length * 0.95) - 1];

check("CONTEXT-CANVAS-BENCHMARK-001 synthetic max pure-operation P95", () => {
  assert.equal(Number.isFinite(benchmarkSink), true);
  assert.equal(Number.isFinite(p95Ms), true);
  assert.ok(p95Ms < 5, `pure Context Canvas operation P95 ${p95Ms.toFixed(3)} ms exceeded 5 ms`);
});

const invariantChecks = checks.filter((id) => id.startsWith("CTX-CANVAS-INV-"));
assert.equal(invariantChecks.length, 18);
assert.deepEqual(
  invariantChecks.map((id) => id.match(/INV-(\d{3})/)?.[1]),
  Array.from({ length: 18 }, (_, index) => String(index + 1).padStart(3, "0")),
);
assert.equal(JSON.stringify(dataset), datasetSnapshot);

const formattedP95 = p95Ms.toFixed(3);
console.log(`CONTEXT_CANVAS_V49_TESTS=PASS CHECKS=${checks.length} INVARIANTS=18 TEMPLATES=4 ASSOCIATIONS=9 P95_MS=${formattedP95}`);
console.log(`CONTEXT_CANVAS_P95_FUNCTION_MS=${formattedP95}`);

async function walkCodeFiles(root) {
  let entries;
  try {
    entries = await readdir(root, { withFileTypes: true });
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") return [];
    throw error;
  }
  const files = [];
  for (const entry of entries) {
    const child = join(root, entry.name);
    if (entry.isDirectory()) files.push(...await walkCodeFiles(child));
    else if ([".js", ".mjs", ".ts", ".tsx"].includes(extname(entry.name))) files.push(child);
  }
  return files.sort();
}

function importSpecifiers(source) {
  const values = [];
  const patterns = [
    /\bfrom\s*["']([^"']+)["']/g,
    /\bimport\s*["']([^"']+)["']/g,
    /\b(?:import|require)\s*\(\s*["']([^"']+)["']\s*\)/g,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) values.push(match[1]);
  }
  return values;
}

function collectKeys(value, found = new Set()) {
  if (!value || typeof value !== "object") return found;
  for (const [key, child] of Object.entries(value)) {
    found.add(key);
    collectKeys(child, found);
  }
  return found;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

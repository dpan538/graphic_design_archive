"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { ApprovedSuggestion, TraceSuggestionContext } from "@/features/system-suggestions/types";
import type { TraceContextDataset } from "../types";
import { deriveVisibleContextCanvasConnections } from "./connections";
import { ContextCanvasInspector } from "./ContextCanvasInspector";
import { ContextCanvasToolbar } from "./ContextCanvasToolbar";
import { ContextCanvasViewport } from "./ContextCanvasViewport";
import { ContextEntityPalette } from "./ContextEntityPalette";
import {
  buildContextCanvasPngFilename,
  downloadContextCanvasPng,
  prepareContextCanvasExportSvg,
} from "./export-png";
import {
  autoArrangeContextCanvas,
  computeContextCanvasBounds,
  fitContextCanvasViewport,
} from "./layout";
import {
  contextCanvasAccessibleRowsForMode,
  contextCanvasEntityRefsForMode,
  contextCanvasRepresentationByEntityId,
  contextCanvasSessionKey,
  getGovernedContextMetadata,
} from "./model";
import {
  clearContextCanvasWorkspace,
  loadContextCanvasWorkspace,
  saveContextCanvasWorkspace,
} from "./persistence";
import { contextCanvasReducer } from "./reducer";
import {
  contextCanvasFunctionalState,
  createInitializingContextCanvasState,
} from "./state";
import {
  getContextCanvasTemplatesForMode,
  initializeContextCanvasTemplate,
} from "./templates";
import {
  CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
  CONTEXT_CANVAS_MAX_ZOOM,
  CONTEXT_CANVAS_MIN_ZOOM,
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  contextCanvasEntityId,
  contextCanvasNodeDomId,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasState,
  type ContextCanvasViewportSize,
} from "./types";
import { contextCanvasScreenToWorld, zoomContextCanvasAtPoint } from "./viewport";
import styles from "./ContextCanvas.module.css";

const DEFAULT_VIEWPORT_SIZE = Object.freeze({ width: 1_000, height: 640 });

export interface ContextCanvasProps {
  readonly dataset: TraceContextDataset;
  readonly dataMode: ContextCanvasDataMode;
  readonly metadata: ContextCanvasDataMetadata;
}

function stateForPersistenceTeardown(state: ContextCanvasState): ContextCanvasState {
  if (state.interaction.mode !== "NODE_DRAGGING") return state;
  return {
    ...state,
    history: {
      ...state.history,
      present: state.interaction.baseline,
    },
  };
}

function persistContextCanvasSession(
  dataset: TraceContextDataset,
  state: ContextCanvasState,
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): boolean {
  try {
    return saveContextCanvasWorkspace(
      dataset,
      state,
      window.localStorage,
      dataMode,
      metadata,
    );
  } catch {
    return false;
  }
}

export default function ContextCanvas(props: ContextCanvasProps) {
  const sessionKey = contextCanvasSessionKey(props.dataset, props.dataMode, props.metadata);

  return <ContextCanvasSession key={sessionKey} {...props} />;
}

function ContextCanvasSession({ dataset, dataMode, metadata }: ContextCanvasProps) {
  const [state, dispatch] = useReducer(
    contextCanvasReducer,
    undefined,
    () => createInitializingContextCanvasState(dataset, dataMode, metadata),
  );
  const [viewportSize, setViewportSize] = useState<ContextCanvasViewportSize>(DEFAULT_VIEWPORT_SIZE);
  const [paletteCollapsed, setPaletteCollapsed] = useState(false);
  const [inspectorCollapsed, setInspectorCollapsed] = useState(false);
  const [paletteGhost, setPaletteGhost] = useState<Readonly<{ x: number; y: number; label: string }> | null>(null);
  const [pendingFocusTarget, setPendingFocusTarget] = useState<string | null>(null);
  const viewportContainerRef = useRef<HTMLDivElement>(null);
  const initialViewportFitPending = useRef(true);
  const latestStateRef = useRef(state);
  const exportAbortControllerRef = useRef<AbortController | null>(null);

  const composition = state.history.present;
  const templates = useMemo(() => getContextCanvasTemplatesForMode(dataMode), [dataMode]);
  const visibleIds = useMemo(() => new Set(composition.visibleEntityIds), [composition.visibleEntityIds]);
  const canvasEntities = useMemo(
    () => contextCanvasEntityRefsForMode(dataset, dataMode, metadata),
    [dataMode, dataset, metadata],
  );
  const representationByEntityId = useMemo(
    () => contextCanvasRepresentationByEntityId(dataMode, metadata),
    [dataMode, metadata],
  );
  const allAccessibleRows = useMemo(
    () => contextCanvasAccessibleRowsForMode(dataset, dataMode, metadata),
    [dataMode, dataset, metadata],
  );
  const governed = getGovernedContextMetadata(dataMode, metadata);
  const availableEntities = useMemo(
    () => canvasEntities.filter((item) => !visibleIds.has(contextCanvasEntityId(item))),
    [canvasEntities, visibleIds],
  );
  const visibleConnections = useMemo(
    () => deriveVisibleContextCanvasConnections(
      dataset,
      composition.visibleEntityIds,
      dataMode,
      metadata,
    ),
    [composition.visibleEntityIds, dataMode, dataset, metadata],
  );
  const visibleAccessibleRows = useMemo(() => {
    const rowIds = new Set([
      `selected:${dataset.selectedRecord.stableId}`,
      ...visibleConnections.map((connection) => connection.accessibleRowId),
    ]);
    return allAccessibleRows.filter((row) => rowIds.has(row.id));
  }, [allAccessibleRows, dataset.selectedRecord.stableId, visibleConnections]);
  const interactionLocked = state.phase === "INITIALIZING"
    || state.phase === "EXPORTING"
    || state.interaction.mode !== "READY";
  const suggestionContext = useMemo<TraceSuggestionContext>(() => {
    const availableKinds = new Set(availableEntities.flatMap((entity) => {
      const representation = representationByEntityId.get(contextCanvasEntityId(entity));
      return representation ? [representation.kind] : [];
    }));
    return {
      stateType: `CONTEXT_CANVAS_${composition.templateId.toUpperCase().replaceAll("-", "_")}`,
      labels: [
        dataset.selectedRecord.label ?? dataset.selectedRecord.stableId,
        ...(governed?.representations.map((representation) => representation.label) ?? []),
      ].slice(0, 12),
      counts: {
        publicContextRepresentations: governed?.representations.length ?? 0,
        visibleRepresentations: visibleConnections.length,
        availableRepresentations: availableEntities.length,
      },
      validActionIds: [
        ...(availableKinds.has("medium") ? ["EXPAND_MEDIUM"] : []),
        ...(availableKinds.has("theme") ? ["EXPAND_THEME"] : []),
        ...(availableKinds.has("movement_context") ? ["EXPAND_MOVEMENT"] : []),
      ],
      evidenceClass: "PUBLIC_CONTEXT",
    };
  }, [availableEntities, composition.templateId, dataset.selectedRecord.label, dataset.selectedRecord.stableId, governed?.representations, representationByEntityId, visibleConnections.length]);

  const handleViewportSizeChange = useCallback((size: ContextCanvasViewportSize) => {
    setViewportSize((current) =>
      Math.abs(current.width - size.width) < 0.5 && Math.abs(current.height - size.height) < 0.5
        ? current
        : size);
    if (initialViewportFitPending.current && size.width > 0 && size.height > 0) {
      initialViewportFitPending.current = false;
      const initial = initializeContextCanvasTemplate(
        dataset,
        "context-overview",
        dataMode,
        metadata,
      );
      dispatch({
        type: "SET_VIEWPORT",
        viewport: fitContextCanvasViewport(
          computeContextCanvasBounds(initial.visibleEntityIds, initial.positions),
          size,
        ),
      });
    }
  }, [dataMode, dataset, metadata]);

  useEffect(() => {
    const restored = loadContextCanvasWorkspace(
      dataset,
      window.localStorage,
      dataMode,
      metadata,
    );
    if (restored) {
      initialViewportFitPending.current = false;
      dispatch({ type: "INITIALIZE", ...restored });
      return;
    }
    const initial = initializeContextCanvasTemplate(
      dataset,
      "context-overview",
      dataMode,
      metadata,
    );
    dispatch({ type: "INITIALIZE", composition: initial });
  }, [dataMode, dataset, metadata]);

  useLayoutEffect(() => {
    latestStateRef.current = state;
  }, [state]);

  useEffect(() => {
    if (state.phase === "INITIALIZING" || state.interaction.mode === "NODE_DRAGGING") return;
    const timer = window.setTimeout(() => {
      persistContextCanvasSession(dataset, state, dataMode, metadata);
    }, 160);
    return () => window.clearTimeout(timer);
  }, [dataMode, dataset, metadata, composition, state.viewport, state.phase, state.interaction.mode]);

  useEffect(() => {
    const flushLatestSession = () => {
      exportAbortControllerRef.current?.abort();
      exportAbortControllerRef.current = null;

      const latestState = latestStateRef.current;
      if (latestState.phase === "INITIALIZING") return;
      persistContextCanvasSession(
        dataset,
        stateForPersistenceTeardown(latestState),
        dataMode,
        metadata,
      );
    };
    const restoreAfterPageCache = (event: PageTransitionEvent) => {
      if (event.persisted && latestStateRef.current.phase === "EXPORTING") {
        dispatch({ type: "EXPORT_CANCEL" });
      }
    };
    window.addEventListener("pagehide", flushLatestSession);
    window.addEventListener("pageshow", restoreAfterPageCache);
    return () => {
      window.removeEventListener("pagehide", flushLatestSession);
      window.removeEventListener("pageshow", restoreAfterPageCache);
      flushLatestSession();
    };
  }, [dataMode, dataset, metadata]);

  useEffect(() => {
    if (!pendingFocusTarget) return;
    const target = document.getElementById(pendingFocusTarget);
    if (!target) return;
    target.focus();
    setPendingFocusTarget(null);
  }, [pendingFocusTarget, composition.visibleEntityIds]);

  function fitComposition(nextComposition = composition) {
    dispatch({
      type: "SET_VIEWPORT",
      viewport: fitContextCanvasViewport(
        computeContextCanvasBounds(nextComposition.visibleEntityIds, nextComposition.positions),
        viewportSize,
      ),
    });
  }

  function applyTemplate(templateId: typeof composition.templateId) {
    const next = initializeContextCanvasTemplate(dataset, templateId, dataMode, metadata);
    dispatch({ type: "APPLY_TEMPLATE", composition: next });
    fitComposition(next);
  }

  function defaultAddPosition() {
    const center = contextCanvasScreenToWorld(
      { x: viewportSize.width / 2, y: viewportSize.height / 2 },
      state.viewport,
    );
    const occupied = new Set(
      Object.values(composition.positions).map((position) => `${Math.round(position.x)}:${Math.round(position.y)}`),
    );
    let position = {
      x: center.x - CONTEXT_CANVAS_NODE_WIDTH / 2,
      y: center.y - CONTEXT_CANVAS_NODE_HEIGHT / 2,
    };
    let attempt = 0;
    while (occupied.has(`${Math.round(position.x)}:${Math.round(position.y)}`) && attempt < 12) {
      attempt += 1;
      position = { x: position.x + 28, y: position.y + 28 };
    }
    return position;
  }

  function addEntity(entityId: string) {
    setPendingFocusTarget(contextCanvasNodeDomId(entityId));
    dispatch({ type: "ADD_ENTITY", entityId, position: defaultAddPosition() });
  }

  function applySuggestion(suggestion: ApprovedSuggestion) {
    const actionId = suggestion.action.parameters.actionId;
    const kind = actionId === "EXPAND_MEDIUM" ? "medium"
      : actionId === "EXPAND_THEME" ? "theme"
      : actionId === "EXPAND_MOVEMENT" ? "movement_context"
      : null;
    if (!kind) return;
    const entity = availableEntities.find((candidate) => representationByEntityId.get(contextCanvasEntityId(candidate))?.kind === kind);
    if (entity) addEntity(contextCanvasEntityId(entity));
  }

  function endPaletteDrag(
    entityId: string,
    _pointerId: number,
    clientX: number,
    clientY: number,
  ) {
    dispatch({ type: "END_PALETTE_DRAG" });
    setPaletteGhost(null);
    const rect = viewportContainerRef.current?.getBoundingClientRect();
    if (!rect || clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) return;
    const position = contextCanvasScreenToWorld(
      { x: clientX - rect.left, y: clientY - rect.top },
      state.viewport,
    );
    setPendingFocusTarget(contextCanvasNodeDomId(entityId));
    dispatch({ type: "ADD_ENTITY", entityId, position });
  }

  function hideEntity(entityId: string) {
    setPendingFocusTarget("context-canvas-workspace");
    dispatch({ type: "HIDE_ENTITY", entityId });
  }

  function zoomBy(factor: number) {
    dispatch({
      type: "SET_VIEWPORT",
      viewport: zoomContextCanvasAtPoint(
        state.viewport,
        { x: viewportSize.width / 2, y: viewportSize.height / 2 },
        state.viewport.zoom * factor,
      ),
    });
  }

  function resetCanvas() {
    const initial = initializeContextCanvasTemplate(
      dataset,
      composition.templateId,
      dataMode,
      metadata,
    );
    clearContextCanvasWorkspace(dataset, window.localStorage, dataMode, metadata);
    dispatch({ type: "RESET_CANVAS", composition: initial });
    fitComposition(initial);
  }

  async function exportPng() {
    exportAbortControllerRef.current?.abort();
    const controller = new AbortController();
    exportAbortControllerRef.current = controller;
    dispatch({ type: "EXPORT_START" });
    try {
      const stableSnapshot = prepareContextCanvasExportSvg(
        dataset,
        composition,
        true,
        dataMode,
        metadata,
      );
      const filename = buildContextCanvasPngFilename(dataset.selectedRecord.stableId);
      await downloadContextCanvasPng(
        stableSnapshot,
        filename,
        CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
        controller.signal,
      );
      if (controller.signal.aborted) return;
      dispatch({ type: "EXPORT_SUCCESS" });
    } catch (error) {
      if (controller.signal.aborted) return;
      dispatch({
        type: "EXPORT_FAILURE",
        message: error instanceof Error ? error.message : "Unknown PNG export error.",
      });
    } finally {
      if (exportAbortControllerRef.current === controller) {
        exportAbortControllerRef.current = null;
      }
    }
  }

  return (
    <main className={styles.prototype}>
      <header className={styles.prototypeHeader}>
        <div>
          <p className={styles.eyebrow}>
            TRACE v49 · {dataMode === "governed_context_v1"
              ? "governed Context v1 workspace"
              : dataMode === "real_v49_validation"
                ? "real-data validation workspace"
                : "synthetic contract workspace"}
          </p>
          <h1>Context Canvas</h1>
          <p>
            {dataMode === "governed_context_v1"
              ? "Explore the archive's governed project-curated classifications. They are research-navigation context, not historical relations."
              : "Compose a view over a read-only context dataset. Moving or hiding items changes only this local canvas."}
          </p>
        </div>
        <dl className={styles.dataNotice}>
          <div><dt>Data mode</dt><dd>{dataMode}</dd></div>
          <div><dt>Dataset</dt><dd>{metadata.dataLabel}</dd></div>
          <div><dt>Mapping</dt><dd>{metadata.mappingVersion}</dd></div>
          <div><dt>Selected public ID</dt><dd>{dataset.selectedRecord.stableId}</dd></div>
          {governed ? (
            <>
              <div><dt>Context projection</dt><dd>{governed.projectionId}</dd></div>
              <div><dt>Governance policy</dt><dd>{governed.policyVersion}</dd></div>
              <div><dt>Explanation registry</dt><dd>{governed.explanationRegistryVersion}</dd></div>
              <div><dt>Context publication</dt><dd>published as project-curated context</dd></div>
              <div><dt>Frozen source state</dt><dd>proposed</dd></div>
              <div><dt>Historical relations</dt><dd>none asserted by Context</dd></div>
            </>
          ) : (
            <div><dt>Candidate state</dt><dd>{metadata.candidateState}</dd></div>
          )}
          <div><dt>Availability</dt><dd>{dataset.availability.state}</dd></div>
          <div><dt>Governed release</dt><dd>{String(metadata.governedPublicRelease)}</dd></div>
        </dl>
      </header>

      <ContextCanvasToolbar
        templateId={composition.templateId}
        templates={templates}
        canUndo={state.history.past.length > 0}
        canRedo={state.history.future.length > 0}
        canZoomIn={state.viewport.zoom < CONTEXT_CANVAS_MAX_ZOOM}
        canZoomOut={state.viewport.zoom > CONTEXT_CANVAS_MIN_ZOOM}
        exporting={state.phase === "EXPORTING"}
        interactionLocked={interactionLocked}
        onTemplateChange={applyTemplate}
        onUndo={() => dispatch({ type: "UNDO" })}
        onRedo={() => dispatch({ type: "REDO" })}
        onAutoArrange={() => dispatch({
          type: "AUTO_ARRANGE",
          positions: autoArrangeContextCanvas(
            dataset,
            composition.visibleEntityIds,
            dataMode,
            metadata,
          ),
        })}
        onFit={() => fitComposition()}
        onZoomIn={() => zoomBy(1.2)}
        onZoomOut={() => zoomBy(1 / 1.2)}
        onResetView={() => fitComposition()}
        onResetCanvas={resetCanvas}
        onExportPng={exportPng}
      />

      {dataMode === "governed_context_v1" && governed ? (
        <SystemSuggestionsPanel surface="TRACE_CONTEXT" context={suggestionContext} onAction={applySuggestion} />
      ) : null}

      <div className={styles.workspace}>
        <ContextEntityPalette
          entities={availableEntities}
          representationByEntityId={representationByEntityId}
          collapsed={paletteCollapsed}
          disabled={interactionLocked}
          onToggleCollapsed={() => setPaletteCollapsed((value) => !value)}
          onAdd={addEntity}
          onDragStart={(entityId, pointerId, clientX, clientY) => {
            const ref = canvasEntities.find((item) => contextCanvasEntityId(item) === entityId);
            setPaletteGhost({ x: clientX, y: clientY, label: ref?.label || ref?.stableId || "Entity" });
            dispatch({ type: "BEGIN_PALETTE_DRAG", entityId, pointerId });
          }}
          onDragMove={(x, y) => setPaletteGhost((value) => value ? { ...value, x, y } : null)}
          onDragEnd={endPaletteDrag}
          onDragCancel={() => {
            setPaletteGhost(null);
            dispatch({ type: "CANCEL_INTERACTION" });
          }}
        />

        <div className={styles.canvasColumn}>
          <ContextCanvasViewport
            dataset={dataset}
            dataMode={dataMode}
            metadata={metadata}
            state={state}
            dispatch={dispatch}
            containerRef={viewportContainerRef}
            onViewportSizeChange={handleViewportSizeChange}
          />

          <details
            id="context-canvas-accessible-reference"
            className={styles.accessibleReference}
          >
            <summary className={styles.accessibleSummary}>
              Accessible context reference ({visibleAccessibleRows.length} rows)
            </summary>
            <div className={styles.accessibleReferenceContent}>
              <p>
                {dataMode === "governed_context_v1"
                  ? "This table is the non-graphic equivalent for the selected record and every visible governed Context representation, including its explanation and provenance summary."
                  : "This table is the non-graphic equivalent for the selected record and every currently visible typed connection."}
              </p>
              <div className={styles.tableScroll}>
                <table>
                  <caption>Visible Context Canvas reference rows</caption>
                  <thead><tr><th scope="col">Category</th><th scope="col">Connection or record</th><th scope="col">Verified fields</th></tr></thead>
                  <tbody>
                    {visibleAccessibleRows.map((row) => (
                      <tr key={row.id}>
                        <td>{row.category}</td>
                        <th scope="row">{row.label}</th>
                        <td>{row.values.map((value) => `${value.label}: ${value.value}`).join("; ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </details>
        </div>

        <ContextCanvasInspector
          dataset={dataset}
          dataMode={dataMode}
          metadata={metadata}
          selection={state.selection}
          connections={visibleConnections}
          collapsed={inspectorCollapsed}
          onToggleCollapsed={() => setInspectorCollapsed((value) => !value)}
          onClose={() => dispatch({ type: "SELECT", selection: null })}
          onHideEntity={hideEntity}
        />
      </div>

      {paletteGhost ? (
        <div
          className={styles.paletteGhost}
          style={{ transform: `translate(${paletteGhost.x + 12}px, ${paletteGhost.y + 12}px)` }}
          aria-hidden="true"
        >
          {paletteGhost.label}
        </div>
      ) : null}

      <div className={styles.statusBar}>
        <span>State: {contextCanvasFunctionalState(state)}</span>
        <span role="status" aria-live="polite" aria-atomic="true">{state.statusMessage}</span>
        {state.exportError ? <span role="alert">{state.exportError}</span> : null}
      </div>

    </main>
  );
}

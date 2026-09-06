"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type PointerEvent,
} from "react";
import SiteNav from "@/components/site/SiteNav";
import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { ApprovedSuggestion, ContextReference } from "@/features/system-suggestions/types";
import type { TraceContextDataset } from "@/features/trace-v49/context/types";
import {
  deriveVisibleContextCanvasConnections,
  visibleContextCanvasNodes,
} from "@/features/trace-v49/context/canvas/connections";
import {
  buildContextCanvasPngFilename,
  downloadContextCanvasPng,
} from "@/features/trace-v49/context/canvas/export-png";
import {
  contextCanvasAccessibleRowsForMode,
  contextCanvasRepresentationByEntityId,
  contextCanvasSessionKey,
  getGovernedContextMetadata,
} from "@/features/trace-v49/context/canvas/model";
import {
  clearContextCanvasWorkspace,
  loadContextCanvasWorkspace,
  saveContextCanvasWorkspace,
} from "@/features/trace-v49/context/canvas/persistence";
import { contextCanvasReducer } from "@/features/trace-v49/context/canvas/reducer";
import { createInitializingContextCanvasState } from "@/features/trace-v49/context/canvas/state";
import { initializeContextCanvasTemplate } from "@/features/trace-v49/context/canvas/templates";
import {
  CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
  CONTEXT_CANVAS_MAX_ZOOM,
  CONTEXT_CANVAS_MIN_ZOOM,
  contextCanvasEntityId,
  contextCanvasNodeDomId,
  type ContextCanvasComposition,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasPosition,
  type ContextCanvasState,
  type ContextCanvasViewportSize,
} from "@/features/trace-v49/context/canvas/types";
import {
  contextCanvasScreenToWorld,
  zoomContextCanvasAtPoint,
} from "@/features/trace-v49/context/canvas/viewport";
import type { GovernedContextExampleOption, GovernedContextSampleOption } from "@/features/trace-v49/context/governed/types";
import {
  arrangeWith,
  boundsOf,
  boxOf,
  connectorsOf,
  fieldsOf,
  fitBounds,
  slotFor,
  type ArrangedNode,
  type LayoutInput,
  KIND_ORDER,
  dropOutcome,
} from "../lib/arrange";
import { prepareContextCardSvg } from "../lib/export-card";
import {
  ARCHIVE_NAME,
  BOUNDARY,
  CANVAS_CLAIM,
  CARD_KICKER,
  CARD_RECORD,
  CARD_SITE,
  CARD_WORDMARK,
  COPIED,
  COPIED_HASH,
  COPIED_TECHNICAL,
  COPY_UNAVAILABLE,
  FIELD_SET_ASIDE,
  LAYOUTS,
  LOADING,
  NAME,
  NOT_RECORDED,
  RAIL_COLLAPSE,
  STRESS_BANNER,
  kindWord,
  type ContextKind,
  type LayoutPreset,
  DROP_OBJECT,
  DROP_OUTSIDE,
  DROP_SWAPPED,
} from "../lib/content";
import {
  buildPresentation,
  presentationAsHtml,
  presentationAsMarkdown,
  termEntityId,
} from "../lib/presentation";
import AddContextPanel from "./AddContextPanel";
import CanvasToolbar from "./CanvasToolbar";
import CompactRail from "./CompactRail";
import ContextControls from "./ContextControls";
import ContextRows from "./ContextRows";
import Dock from "./Dock";
import Inspector, { type InspectorSelection } from "./Inspector";
import PageHeader from "./PageHeader";
import Stage from "./Stage";
import styles from "./ContextDesktop.module.css";

/* Context Canvas, desktop (FRONTEND_DESIGN_DECISION.md §7g).

   The existing function, re-set: the composition state, its reducer,
   the entity and row derivations, persistence and the PNG export are the
   reference implementation's (features/trace-v49/context/canvas) and are
   used unchanged; this tree owns only what is seen — four layout
   presets over the same governed contexts (lib/arrange: Overview, Focus,
   Columns, Dense), the items, the fields, the columns, the copy; and one
   presentation model (lib/presentation) that the canvas, the rows and
   the clipboard all read.

   The rail at the left (01 the head, 02 the controls, 06 System suggests
   when there is something to suggest), or compact — the title and three
   indicators — for canvas-focus work; the canvas as the body (03, with
   its toolbar and 05 the rows folded beneath); 04 the inspector at the
   right, closed until a context is selected and closable from the
   dock's toggle; the dock past it. When a column opens or closes, or the
   template changes, the canvas is fitted again. Changing the template
   keeps the selected object, the contexts on the canvas, the selected
   context and the inspector; only positions change. */

const DEFAULT_SIZE = Object.freeze({ width: 1100, height: 700 });
const FIT_PAD = 48;
const FIT_MAX_ZOOM = 1;
const RAIL_KEY = "mgda:context-canvas:rail";
const LAST_RECORD_COOKIE = "mgda-context-last";
const LAST_RECORD_SECONDS = 30 * 60;
const LAYOUT_KEY = "mgda:context-canvas:layout";
/* a stable empty default — a fresh [] each render would re-run the
   initialising effect without end */
const NO_TERMS: readonly string[] = Object.freeze([]);

export type ContextPreview = "loading" | "empty" | "stress" | null;

export interface ContextDesktopProps {
  readonly dataset: TraceContextDataset;
  readonly dataMode: ContextCanvasDataMode;
  readonly metadata: ContextCanvasDataMetadata;
  readonly examples: readonly GovernedContextExampleOption[];
  readonly qaSamples: readonly GovernedContextSampleOption[] | null;
  readonly coverage: Readonly<Record<string, number>>;
  readonly cohort: number;
  readonly preview?: ContextPreview;
  /* the stress fixture's opening state: terms set aside, the term selected */
  readonly initialSetAsideTermIds?: readonly string[];
  readonly initialSelectTermId?: string | null;
}

function stateForPersistenceTeardown(state: ContextCanvasState): ContextCanvasState {
  if (state.interaction.mode !== "NODE_DRAGGING") return state;
  return { ...state, history: { ...state.history, present: state.interaction.baseline } };
}

function persist(
  dataset: TraceContextDataset,
  state: ContextCanvasState,
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): boolean {
  try {
    return saveContextCanvasWorkspace(dataset, state, window.localStorage, dataMode, metadata);
  } catch {
    return false;
  }
}

function readStored(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* no storage: the choice lasts for the page */
  }
}

const isLayout = (value: string | null): value is LayoutPreset => LAYOUTS.some((item) => item.id === value);

export default function ContextDesktop(props: ContextDesktopProps) {
  const sessionKey = contextCanvasSessionKey(props.dataset, props.dataMode, props.metadata);
  return <Session key={sessionKey} {...props} />;
}

function Session({
  dataset,
  dataMode,
  metadata,
  examples,
  qaSamples,
  coverage,
  cohort,
  preview = null,
  initialSetAsideTermIds = NO_TERMS,
  initialSelectTermId = null,
}: ContextDesktopProps) {
  const cohortText = cohort.toLocaleString("en-US");
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const governed = getGovernedContextMetadata(dataMode, metadata);
  const representationById = useMemo(
    () => contextCanvasRepresentationByEntityId(dataMode, metadata),
    [dataMode, metadata],
  );
  const representations = useMemo(() => governed?.representations ?? [], [governed]);
  const kindOf = useCallback(
    (entityId: string): ContextKind | null => representationById.get(entityId)?.kind ?? null,
    [representationById],
  );
  const totals = useMemo(() => ({
    medium: representations.filter((r) => r.kind === "medium").length,
    theme: representations.filter((r) => r.kind === "theme").length,
    movement_context: representations.filter((r) => r.kind === "movement_context").length,
  }), [representations]);

  const [state, dispatch] = useReducer(
    contextCanvasReducer,
    undefined,
    () => createInitializingContextCanvasState(dataset, dataMode, metadata),
  );
  const [size, setSize] = useState<ContextCanvasViewportSize>(DEFAULT_SIZE);
  const [note, setNote] = useState<string | null>(null);
  const [ghost, setGhost] = useState<Readonly<{ x: number; y: number; label: string }> | null>(null);
  const [pendingFocus, setPendingFocus] = useState<string | null>(null);
  const [rowsOpen, setRowsOpen] = useState(preview === "stress");
  /* the workspace states: the inspector opens itself on a selection and
     can be closed; the rail can be compact; the template is a layout
     preset (both kept per browser) */
  const [inspectorOpen, setInspectorOpen] = useState(preview === "stress");
  /* the right panel's mode: the inspector, or ADD CONTEXT from the dock's "+" */
  const [panel, setPanel] = useState<"inspector" | "add">("inspector");
  const [railCompact, setRailCompact] = useState(false);
  const [layout, setLayout] = useState<LayoutPreset>("overview");
  const [focusKind, setFocusKind] = useState<ContextKind>("medium");
  const refitPending = useRef(false);
  const stageRef = useRef<HTMLDivElement>(null);
  const initialised = useRef(false);
  const latest = useRef(state);
  const exportAbort = useRef<AbortController | null>(null);

  const layoutInput = useMemo<LayoutInput>(() => ({ preset: layout, focusKind }), [focusKind, layout]);

  /* the arrangement for a layout: the given composition with its positions
     replaced, the contexts in the projection's order */
  const arrangeFor = useCallback((composition: ContextCanvasComposition, input: LayoutInput): ContextCanvasComposition => {
    const visible = new Set(composition.visibleEntityIds);
    const items = representations
      .map((r) => ({ id: termEntityId(r.termId), kind: r.kind }))
      .filter((item) => visible.has(item.id));
    const known = new Set(items.map((item) => item.id));
    const rest = composition.visibleEntityIds
      .filter((id) => id !== rootId && !known.has(id))
      .map((id) => ({ id, kind: kindOf(id) }));
    return Object.freeze({ ...composition, positions: arrangeWith(rootId, [...items, ...rest], input) });
  }, [kindOf, representations, rootId]);
  const arrange = useCallback(
    (composition: ContextCanvasComposition) => arrangeFor(composition, layoutInput),
    [arrangeFor, layoutInput],
  );

  const composition = state.history.present;
  const nodes = useMemo(
    () => visibleContextCanvasNodes(dataset, composition, dataMode, metadata),
    [composition, dataMode, dataset, metadata],
  );
  const arranged = useMemo<readonly ArrangedNode[]>(
    () => nodes.map((n) => ({ id: n.id, isRoot: n.isRoot, kind: n.representation?.kind ?? null, position: n.position })),
    [nodes],
  );
  const fields = useMemo(() => fieldsOf(arranged, totals, layoutInput), [arranged, layoutInput, totals]);
  /* the governed wording of each connection: the registry's, per kind */
  const wording = useMemo(() => {
    const out: Record<string, string> = {};
    for (const r of representations) {
      out[termEntityId(r.termId)] = r.connectionLabel;
      out[r.kind] = r.connectionLabel;
    }
    return Object.freeze(out);
  }, [representations]);
  const connectors = useMemo(() => connectorsOf(arranged, fields, layoutInput, wording), [arranged, fields, layoutInput, wording]);
  const visibleIds = useMemo(() => new Set(composition.visibleEntityIds), [composition.visibleEntityIds]);
  const connections = useMemo(
    () => deriveVisibleContextCanvasConnections(dataset, composition.visibleEntityIds, dataMode, metadata),
    [composition.visibleEntityIds, dataMode, dataset, metadata],
  );
  const allRows = useMemo(
    () => contextCanvasAccessibleRowsForMode(dataset, dataMode, metadata),
    [dataMode, dataset, metadata],
  );
  const visibleRows = useMemo(() => {
    const ids = new Set([`selected:${dataset.selectedRecord.stableId}`, ...connections.map((c) => c.accessibleRowId)]);
    return allRows.filter((row) => ids.has(row.id));
  }, [allRows, connections, dataset.selectedRecord.stableId]);
  const loading = state.phase === "INITIALIZING";
  const locked = loading || state.phase === "EXPORTING" || state.interaction.mode !== "READY";
  const empty = representations.length === 0;
  const rootMeta = governed?.rootMetadata;
  const title = dataset.selectedRecord.label?.trim() || dataset.selectedRecord.stableId;
  /* the one presentation the canvas, the rows and the clipboard read */
  const presentation = useMemo(() => buildPresentation({
    object: {
      title,
      stableId: dataset.selectedRecord.stableId,
      dateDisplay: rootMeta?.dateDisplay,
      creatorAttribution: rootMeta?.creatorAttribution,
      objectType: rootMeta?.objectType,
      sourceName: rootMeta?.sourceName,
    },
    representations,
    visibleIds,
    boundary: BOUNDARY,
    releaseId: dataset.release.releaseId,
    canvasName: NAME,
  }), [dataset.release.releaseId, dataset.selectedRecord.stableId, representations, rootMeta, title, visibleIds]);
  const groups = presentation.dimensions;
  const available = useMemo(() => groups.flatMap((g) => g.items.filter((i) => !i.visible)), [groups]);
  const selectedEntityId = state.selection?.kind === "node" ? state.selection.id : null;

  const nodesOf = useCallback((c: ContextCanvasComposition): readonly ArrangedNode[] =>
    c.visibleEntityIds.flatMap((id) => {
      const position = c.positions[id];
      return position ? [{ id, isRoot: id === rootId, kind: kindOf(id), position }] : [];
    }), [kindOf, rootId]);
  const viewportFor = useCallback(
    (list: readonly ArrangedNode[], at: ContextCanvasViewportSize = size, input: LayoutInput = layoutInput) =>
      fitBounds(boundsOf(list, fieldsOf(list, totals, input)), at, FIT_PAD, FIT_MAX_ZOOM),
    [layoutInput, size, totals],
  );

  /* ---- lifecycle: restore or initialise, persist, tear down ---- */

  const handleSizeChange = useCallback((next: ContextCanvasViewportSize) => {
    setSize((current) =>
      Math.abs(current.width - next.width) < 0.5 && Math.abs(current.height - next.height) < 0.5 ? current : next);
  }, []);

  /* once, on arrival: the per-browser choices, then the composition —
     restored, or the template arranged under the stored layout; the
     first fit follows in the layout effect below */
  useEffect(() => {
    if (initialised.current) return;
    initialised.current = true;
    let preset: LayoutPreset = "overview";
    if (!preview) {
      setRailCompact(readStored(RAIL_KEY) === "compact");
      const stored = readStored(LAYOUT_KEY);
      if (isLayout(stored)) {
        preset = stored;
        setLayout(stored);
      }
    }
    /* Focus reads the first dimension the object carries */
    const focus = KIND_ORDER.find((kind) => totals[kind] > 0) ?? "medium";
    setFocusKind(focus);
    const input: LayoutInput = { preset, focusKind: focus };
    /* the loading preview keeps the canvas in its initialising state */
    if (preview === "loading") return;
    const restored = preview ? null : loadContextCanvasWorkspace(dataset, window.localStorage, dataMode, metadata);
    if (restored) {
      /* the composition is the reader's — its membership, what was set
         aside and what is selected; its positions are laid out again
         under the layout as it is now, since positions kept from another
         layout (or an earlier arrangement) would draw the fields around
         the wrong places; the viewport is fitted to the stage as it is */
      refitPending.current = true;
      dispatch({ type: "INITIALIZE", composition: arrangeFor(restored.composition, input) });
      return;
    }
    /* the template, minus what is left to add */
    const setAside = new Set(initialSetAsideTermIds.map(termEntityId));
    const base = initializeContextCanvasTemplate(dataset, "context-overview", dataMode, metadata);
    const composition = arrangeFor(setAside.size === 0 ? base : Object.freeze({
      ...base,
      visibleEntityIds: base.visibleEntityIds.filter((id) => !setAside.has(id)),
    }), input);
    refitPending.current = true;
    dispatch({ type: "INITIALIZE", composition });
    if (initialSelectTermId) dispatch({ type: "SELECT", selection: { kind: "node", id: termEntityId(initialSelectTermId) } });
  }, [arrangeFor, dataMode, dataset, initialSelectTermId, initialSetAsideTermIds, metadata, preview, totals]);

  /* the object opened, remembered for thirty minutes in this browser (a
     first-party cookie holding the public stable ID) so that entering
     Context Canvas again returns here rather than to the landing record */
  useEffect(() => {
    if (preview) return;
    try {
      document.cookie = `${LAST_RECORD_COOKIE}=${encodeURIComponent(dataset.selectedRecord.stableId)}; Max-Age=${LAST_RECORD_SECONDS}; Path=/trace/context-canvas; SameSite=Lax`;
    } catch {
      /* no cookie: the landing record next time */
    }
  }, [dataset.selectedRecord.stableId, preview]);

  useLayoutEffect(() => {
    latest.current = state;
  }, [state]);

  /* on arrival, when a column opened or closed, or when the template
     changed: the stage has its width and the canvas its positions — fit */
  useLayoutEffect(() => {
    if (!refitPending.current) return;
    const element = stageRef.current;
    if (!element) return;
    refitPending.current = false;
    const rect = element.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    const next = { width: rect.width, height: rect.height };
    setSize(next);
    dispatch({ type: "SET_VIEWPORT", viewport: viewportFor(nodesOf(latest.current.history.present), next) });
  }, [inspectorOpen, railCompact, layout, focusKind, nodesOf, viewportFor, composition]);

  useEffect(() => {
    if (preview || state.phase === "INITIALIZING" || state.interaction.mode === "NODE_DRAGGING") return;
    const timer = window.setTimeout(() => persist(dataset, state, dataMode, metadata), 160);
    return () => window.clearTimeout(timer);
  }, [dataMode, dataset, metadata, preview, state]);

  useEffect(() => {
    const flush = () => {
      exportAbort.current?.abort();
      exportAbort.current = null;
      const current = latest.current;
      if (preview || current.phase === "INITIALIZING") return;
      persist(dataset, stateForPersistenceTeardown(current), dataMode, metadata);
    };
    const restoreAfterPageCache = (event: PageTransitionEvent) => {
      if (event.persisted && latest.current.phase === "EXPORTING") dispatch({ type: "EXPORT_CANCEL" });
    };
    window.addEventListener("pagehide", flush);
    window.addEventListener("pageshow", restoreAfterPageCache);
    return () => {
      window.removeEventListener("pagehide", flush);
      window.removeEventListener("pageshow", restoreAfterPageCache);
      flush();
    };
  }, [dataMode, dataset, metadata, preview]);

  useEffect(() => {
    if (!pendingFocus) return;
    const target = document.getElementById(pendingFocus);
    if (!target) return;
    target.focus({ preventScroll: true });
    setPendingFocus(null);
  }, [pendingFocus, composition.visibleEntityIds, rowsOpen]);

  /* a UI note (copy, focus) shows in the status line until the reducer
     speaks again — unless a note was queued for that very message (a
     drag's determination), which then takes the line */
  const queuedNote = useRef<string | null>(null);
  useEffect(() => {
    setNote(queuedNote.current);
    queuedNote.current = null;
  }, [state.statusMessage]);
  /* the click that trails a drag must not speak over the determination */
  const clickGuardUntil = useRef(0);

  /* ---- the view ---- */

  function setViewport(viewport: ContextCanvasState["viewport"]) {
    dispatch({ type: "SET_VIEWPORT", viewport });
  }

  function fitAll() {
    setViewport(viewportFor(arranged));
  }

  function zoomBy(factor: number) {
    setViewport(zoomContextCanvasAtPoint(
      state.viewport,
      { x: size.width / 2, y: size.height / 2 },
      state.viewport.zoom * factor,
    ));
  }

  const handleWheel = useCallback((deltaY: number, point: ContextCanvasPosition) => {
    const current = latest.current;
    if (current.phase === "EXPORTING" || current.interaction.mode !== "READY") return;
    const factor = Math.exp(-deltaY * 0.0015);
    dispatch({
      type: "SET_VIEWPORT",
      viewport: zoomContextCanvasAtPoint(current.viewport, point, current.viewport.zoom * factor),
    });
  }, []);

  /* bring one item fully into the stage, keeping the zoom */
  function bringIntoView(entityId: string) {
    const node = arranged.find((n) => n.id === entityId);
    if (!node) return;
    const box = boxOf(node);
    const { x, y, zoom } = state.viewport;
    const left = box.x * zoom + x;
    const top = box.y * zoom + y;
    const right = left + box.width * zoom;
    const bottom = top + box.height * zoom;
    const margin = 32;
    const inside = left >= margin && top >= margin && right <= size.width - margin && bottom <= size.height - margin;
    if (inside) return;
    setViewport({
      x: size.width / 2 - (box.x + box.width / 2) * zoom,
      y: size.height / 2 - (box.y + box.height / 2) * zoom,
      zoom,
    });
  }

  function select(entityId: string, bring: boolean) {
    /* the click that trails a drag: the drag's determination already
       selected the item and spoke */
    if (Date.now() < clickGuardUntil.current) return;
    dispatch({ type: "SELECT", selection: { kind: "node", id: entityId } });
    if (bring) bringIntoView(entityId);
    setPanel("inspector");
    if (!inspectorOpen) {
      refitPending.current = true;
      setInspectorOpen(true);
    }
  }

  function goToChip(entityId: string) {
    bringIntoView(entityId);
    setPendingFocus(contextCanvasNodeDomId(entityId));
  }

  function bringFieldIntoView(kind: ContextKind) {
    const field = fields.find((f) => f.kind === kind);
    if (!field) return;
    setViewport(fitBounds(field.box, size, FIT_PAD, 1.1));
    setNote(`${kindWord(kind)} field in view.`);
  }

  function openRows() {
    setRowsOpen(true);
    setPendingFocus("context-rows-summary");
  }

  function toggleInspector() {
    refitPending.current = true;
    if (inspectorOpen && panel === "add") {
      /* from the add panel, the inspector's control shows the inspector */
      setPanel("inspector");
      return;
    }
    setPanel("inspector");
    setInspectorOpen((open) => !open);
  }

  function openAddPanel() {
    if (available.length === 0) return;
    if (!inspectorOpen) refitPending.current = true;
    setPanel("add");
    setInspectorOpen(true);
  }

  function toggleRail() {
    refitPending.current = true;
    setRailCompact((compact) => {
      writeStored(RAIL_KEY, compact ? "expanded" : "compact");
      return !compact;
    });
  }

  /* ---- the templates: layout only ---- */

  /* the dimension a focus template opens on: the selected context's, else
     the first with something on the canvas */
  function defaultFocus(): ContextKind {
    const selectedKind = selectedEntityId ? kindOf(selectedEntityId) : null;
    if (selectedKind) return selectedKind;
    return groups.find((g) => g.items.some((i) => i.visible))?.kind
      ?? groups.find((g) => g.items.length > 0)?.kind
      ?? "medium";
  }

  /* re-lay the current composition under a layout; keep the selection */
  function rearrange(input: LayoutInput) {
    const next = arrangeFor(composition, input);
    dispatch({ type: "AUTO_ARRANGE", positions: next.positions });
    if (selectedEntityId && visibleIds.has(selectedEntityId)) {
      dispatch({ type: "SELECT", selection: { kind: "node", id: selectedEntityId } });
    }
    refitPending.current = true;
  }

  function applyLayout(next: LayoutPreset) {
    const focus = next === "focus" ? defaultFocus() : focusKind;
    setLayout(next);
    setFocusKind(focus);
    if (!preview) writeStored(LAYOUT_KEY, next);
    rearrange({ preset: next, focusKind: focus });
  }

  function chooseFocus(kind: ContextKind) {
    setFocusKind(kind);
    if (layout === "focus") rearrange({ preset: "focus", focusKind: kind });
  }

  /* ---- the composition ---- */

  function autoArrange() {
    rearrange(layoutInput);
  }

  function resetCanvas() {
    const initial = arrange(initializeContextCanvasTemplate(dataset, composition.templateId, dataMode, metadata));
    if (!preview) clearContextCanvasWorkspace(dataset, window.localStorage, dataMode, metadata);
    dispatch({ type: "RESET_CANVAS", composition: initial });
    setViewport(viewportFor(nodesOf(initial)));
  }

  /* adding: an already-governed representation onto the canvas, into its
     field, focused, selected (the reducer selects it), the inspector open,
     the canvas fitted again so it is in view */
  function addEntity(entityId: string, position?: ContextCanvasPosition) {
    setPendingFocus(contextCanvasNodeDomId(entityId));
    dispatch({
      type: "ADD_ENTITY",
      entityId,
      position: position ?? slotFor(entityId, kindOf(entityId), rootId, arranged, layoutInput),
    });
    refitPending.current = true;
    setPanel("inspector");
    setInspectorOpen(true);
  }

  function hideEntity(entityId: string) {
    setPendingFocus("context-stage");
    dispatch({ type: "HIDE_ENTITY", entityId });
  }

  function applySuggestion(suggestion: ApprovedSuggestion) {
    const actionId = suggestion.action.parameters.actionId;
    const kind: ContextKind | null = actionId === "EXPAND_MEDIUM" ? "medium"
      : actionId === "EXPAND_THEME" ? "theme"
      : actionId === "EXPAND_MOVEMENT" ? "movement_context"
      : null;
    if (!kind) return;
    const candidate = available.find((item) => item.representation.kind === kind);
    if (candidate) addEntity(candidate.entityId);
  }

  /* ---- pointer interaction on the stage ---- */

  function beginPan(event: PointerEvent<HTMLDivElement>) {
    if (state.phase !== "READY" || event.button !== 0) return;
    event.preventDefault();
    stageRef.current?.setPointerCapture(event.pointerId);
    dispatch({ type: "BEGIN_PAN", pointerId: event.pointerId, startClient: { x: event.clientX, y: event.clientY } });
  }

  function beginNodeDrag(event: PointerEvent<HTMLDivElement>, nodeId: string) {
    if (state.phase !== "READY") return;
    dispatch({
      type: "BEGIN_NODE_DRAG",
      nodeId,
      pointerId: event.pointerId,
      startClient: { x: event.clientX, y: event.clientY },
    });
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const interaction = state.interaction;
    if (interaction.mode === "NODE_DRAGGING" && interaction.pointerId === event.pointerId) {
      dispatch({
        type: "PREVIEW_NODE_DRAG",
        position: {
          x: interaction.originPosition.x + (event.clientX - interaction.startClient.x) / state.viewport.zoom,
          y: interaction.originPosition.y + (event.clientY - interaction.startClient.y) / state.viewport.zoom,
        },
      });
    } else if (interaction.mode === "PANNING" && interaction.pointerId === event.pointerId) {
      setViewport({
        x: interaction.originViewport.x + (event.clientX - interaction.startClient.x),
        y: interaction.originViewport.y + (event.clientY - interaction.startClient.y),
        zoom: interaction.originViewport.zoom,
      });
    }
  }

  /* a drag ends in a determination: the chip snaps to a slot of its own
     field — its own, or another chip's, and then the two change places;
     dropped away from its field, or the object itself moved, it is put
     back — the status line says which */
  function handlePointerEnd(event: PointerEvent<HTMLDivElement>) {
    const interaction = state.interaction;
    if (interaction.mode === "NODE_DRAGGING" && interaction.pointerId === event.pointerId) {
      const outcome = dropOutcome(arranged, interaction.baseline.positions, layoutInput, interaction.nodeId);
      const representation = representationById.get(interaction.nodeId);
      const label = representation?.label ?? interaction.nodeId;
      const word = kindWord(representation?.kind ?? "medium");
      queuedNote.current = outcome.kind === "swap"
        ? DROP_SWAPPED(label, representationById.get(outcome.otherId)?.label ?? outcome.otherId, word)
        : outcome.kind === "put_back"
          ? (outcome.reason === "object_moved" ? DROP_OBJECT : DROP_OUTSIDE(label, word))
          : null;
      clickGuardUntil.current = Date.now() + 400;
      dispatch({ type: "CANCEL_INTERACTION" });
      if (outcome.kind === "swap") dispatch({ type: "AUTO_ARRANGE", positions: outcome.positions });
      /* the dragged item stays selected, as the reference's drag left it */
      dispatch({ type: "SELECT", selection: { kind: "node", id: interaction.nodeId } });
    } else if (interaction.mode === "PANNING" && interaction.pointerId === event.pointerId) {
      dispatch({ type: "END_PAN" });
    }
  }

  function handlePointerCancel(event: PointerEvent<HTMLDivElement>) {
    const interaction = state.interaction;
    if (interaction.mode !== "READY" && interaction.pointerId === event.pointerId) {
      dispatch({ type: "CANCEL_INTERACTION" });
    }
  }

  function handleEscape() {
    if (state.interaction.mode === "READY") dispatch({ type: "SELECT", selection: null });
    else dispatch({ type: "CANCEL_INTERACTION" });
  }

  /* dragging an Add control from the rows onto the stage */
  function endRowDrag(entityId: string, _pointerId: number, clientX: number, clientY: number) {
    dispatch({ type: "END_PALETTE_DRAG" });
    setGhost(null);
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect || clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) return;
    const world = contextCanvasScreenToWorld({ x: clientX - rect.left, y: clientY - rect.top }, state.viewport);
    addEntity(entityId, world);
  }

  /* ---- export and copy ---- */

  /* the export: the research card (lib/export-card) — the canvas's exact
     membership under the current layout, the selected term marked */
  const exportCard = useCallback(() => prepareContextCardSvg({
    presentation,
    terms: presentation.dimensions.flatMap((d) => d.items.filter((i) => i.visible).map((i) => ({
      entityId: i.entityId,
      label: i.label,
      kind: i.kind,
      wording: i.representation.connectionLabel,
      selected: i.entityId === selectedEntityId,
    }))),
    layout: layoutInput,
    identity: {
      releaseId: dataset.release.releaseId,
      manifestSha256: dataset.release.manifestSha256,
      projectionId: governed?.projectionId ?? "",
      projectionSha256: governed?.projectionSha256 ?? "",
    },
    kicker: CARD_KICKER,
    canvasName: NAME,
    record: CARD_RECORD,
    wordmark: CARD_WORDMARK,
    site: CARD_SITE,
    notRecorded: NOT_RECORDED,
  }), [dataset.release.manifestSha256, dataset.release.releaseId, governed?.projectionId, governed?.projectionSha256, layoutInput, presentation, selectedEntityId]);

  /* development only: the export SVG and the copy text, for in-browser
     checks (rendered inline and measured, rather than eyeballed) */
  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;
    const hook = {
      exportSvg: () => exportCard(),
      text: () => copyMarkdown(),
      html: () => copyHtml(),
    };
    (window as unknown as { __mgdaContextCanvas?: typeof hook }).__mgdaContextCanvas = hook;
    return () => {
      delete (window as unknown as { __mgdaContextCanvas?: typeof hook }).__mgdaContextCanvas;
    };
  });

  async function exportPng() {
    exportAbort.current?.abort();
    const controller = new AbortController();
    exportAbort.current = controller;
    dispatch({ type: "EXPORT_START" });
    try {
      const snapshot = exportCard();
      const filename = buildContextCanvasPngFilename(dataset.selectedRecord.stableId);
      await downloadContextCanvasPng(snapshot, filename, CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE, controller.signal);
      if (controller.signal.aborted) return;
      dispatch({ type: "EXPORT_SUCCESS" });
    } catch (error) {
      if (controller.signal.aborted) return;
      dispatch({ type: "EXPORT_FAILURE", message: error instanceof Error ? error.message : "Unknown PNG export error." });
    } finally {
      if (exportAbort.current === controller) exportAbort.current = null;
    }
  }

  async function copy(text: string, doneNote: string) {
    try {
      await navigator.clipboard.writeText(text);
      setNote(doneNote);
    } catch {
      setNote(COPY_UNAVAILABLE);
    }
  }

  /* Copy context: the presentation as tables — HTML for rich clipboards
     (notes, documents), a Markdown table as the plain-text fallback
     (chats, editors) — the same sheet either way */
  function copyMarkdown(): string {
    return presentationAsMarkdown(presentation, NOT_RECORDED, FIELD_SET_ASIDE, NAME, ARCHIVE_NAME);
  }

  function copyHtml(): string {
    return presentationAsHtml(presentation, NOT_RECORDED, FIELD_SET_ASIDE, NAME, ARCHIVE_NAME);
  }

  async function copyContext() {
    const markdown = copyMarkdown();
    try {
      if (typeof ClipboardItem !== "undefined" && navigator.clipboard.write) {
        await navigator.clipboard.write([new ClipboardItem({
          "text/html": new Blob([copyHtml()], { type: "text/html" }),
          "text/plain": new Blob([markdown], { type: "text/plain" }),
        })]);
      } else {
        await navigator.clipboard.writeText(markdown);
      }
      setNote(COPIED);
    } catch {
      try {
        await navigator.clipboard.writeText(markdown);
        setNote(COPIED);
      } catch {
        setNote(COPY_UNAVAILABLE);
      }
    }
  }

  /* ---- derived for the columns ---- */

  const inspectorSelection: InspectorSelection = useMemo(() => {
    if (!selectedEntityId) return { kind: "none" };
    if (selectedEntityId === rootId) return { kind: "root" };
    const representation = representationById.get(selectedEntityId);
    if (!representation) return { kind: "none" };
    const count = coverage[representation.termId];
    return {
      kind: "representation",
      representation,
      entityId: selectedEntityId,
      visible: visibleIds.has(selectedEntityId),
      coverage: Number.isSafeInteger(count) ? count : null,
    };
  }, [coverage, representationById, rootId, selectedEntityId, visibleIds]);

  /* 06 — asked only while a context is set aside, so every suggestion
     carries an existing action the reader can take */
  /* the canvas's identity for System suggests (release pass): the object and the governed
     representation ids standing on the canvas; the server reads the object's context itself
     and confirms the counts shown. Only the governed data mode names a public object. */
  const suggestionReference = useMemo<ContextReference | null>(() => {
    if (!governed) return null;
    const onCanvas = [...visibleIds].map((entityId) => representationById.get(entityId)?.termId).filter((id): id is string => typeof id === "string");
    return { objectId: dataset.selectedRecord.stableId, onCanvas };
  }, [governed, visibleIds, representationById, dataset.selectedRecord.stableId]);
  const suggestionShown = useMemo(() => ({ representations: representations.length, onCanvas: connections.length, setAside: available.length }), [representations.length, connections.length, available.length]);

  const status = note ?? state.statusMessage;
  const identity = {
    stableId: dataset.selectedRecord.stableId,
    dateDisplay: rootMeta?.dateDisplay,
    objectType: rootMeta?.objectType,
  };
  const dimensions = groups.map((g) => ({
    kind: g.kind,
    word: g.word,
    visibleCount: g.items.filter((i) => i.visible).length,
    total: g.items.length,
    available: g.items.filter((i) => !i.visible).map((i) => ({ entityId: i.entityId, label: i.label })),
  }));

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNav active="trace" revealTone="light" />
      <Dock
        active="context"
        inspector={{ open: inspectorOpen && panel === "inspector", onToggle: toggleInspector }}
        add={{ available: available.length, open: inspectorOpen && panel === "add", onOpen: openAddPanel }}
      />
      <div className={styles.grain} aria-hidden="true" />

      <main
        id="main"
        className={styles.main}
        data-rail={railCompact ? "compact" : "expanded"}
        data-inspector={inspectorOpen ? "open" : "closed"}
      >
        <div className={styles.rail}>
          {railCompact ? (
            <CompactRail
              title={title}
              stableId={dataset.selectedRecord.stableId}
              dimensions={dimensions}
              onExpand={toggleRail}
              onFocusKind={bringFieldIntoView}
            />
          ) : (
            <>
              <button type="button" className={styles.railToggle} aria-label={RAIL_COLLAPSE} aria-expanded="true" onClick={toggleRail}>‹</button>
              <PageHeader
                selected={{ title, stableId: dataset.selectedRecord.stableId }}
                requestedId={dataset.selectedRecord.stableId}
                examples={examples}
                qaSamples={qaSamples}
                cohort={cohortText}
              />
              <ContextControls
                layout={layout}
                focusKind={focusKind}
                locked={locked}
                dimensions={dimensions}
                onLayoutChange={applyLayout}
                onFocusKind={chooseFocus}
                onDimension={bringFieldIntoView}
                onAdd={(id) => addEntity(id)}
                onOpenRows={openRows}
              />
              {available.length > 0 ? (
                <div className={styles.suggests}>
                  {suggestionReference ? <SystemSuggestionsPanel surface="TRACE_CONTEXT" reference={suggestionReference} shown={suggestionShown} onAction={applySuggestion} tone="canvas" maxActions={1} /> : null}
                </div>
              ) : null}
            </>
          )}
        </div>

        <section className={styles.centre} aria-label="Canvas">
          <Stage
            containerRef={stageRef}
            nodes={nodes}
            fields={fields}
            connectors={connectors}
            preset={layout}
            viewport={state.viewport}
            interaction={state.interaction.mode}
            selection={state.selection}
            identity={identity}
            empty={empty}
            loading={loading}
            loadingText={LOADING(dataset.selectedRecord.stableId)}
            exporting={state.phase === "EXPORTING"}
            claim={CANVAS_CLAIM}
            banner={preview === "stress" ? STRESS_BANNER : null}
            onSizeChange={handleSizeChange}
            onWheel={handleWheel}
            onBackgroundPointerDown={beginPan}
            onNodePointerDown={beginNodeDrag}
            onPointerMove={handlePointerMove}
            onPointerEnd={handlePointerEnd}
            onPointerCancel={handlePointerCancel}
            onEscape={handleEscape}
            onSelect={(id) => select(id, false)}
            onMoveBy={(entityId, delta) => dispatch({ type: "MOVE_NODE_BY", entityId, delta })}
          />
          <CanvasToolbar
            zoom={state.viewport.zoom}
            canUndo={state.history.past.length > 0}
            canRedo={state.history.future.length > 0}
            canZoomIn={state.viewport.zoom < CONTEXT_CANVAS_MAX_ZOOM}
            canZoomOut={state.viewport.zoom > CONTEXT_CANVAS_MIN_ZOOM}
            exporting={state.phase === "EXPORTING"}
            locked={locked}
            status={status}
            exportError={state.exportError}
            actions={{
              zoomIn: () => zoomBy(1.2),
              zoomOut: () => zoomBy(1 / 1.2),
              fit: fitAll,
              arrange: autoArrange,
              undo: () => dispatch({ type: "UNDO" }),
              redo: () => dispatch({ type: "REDO" }),
              resetCanvas,
              exportPng: () => void exportPng(),
            }}
          />
          <ContextRows
            groups={groups}
            open={rowsOpen}
            selectedEntityId={selectedEntityId}
            locked={locked}
            onToggle={setRowsOpen}
            onSelect={(id) => select(id, true)}
            onGoToChip={goToChip}
            onAdd={(id) => addEntity(id)}
            onRemove={hideEntity}
            onCopy={() => void copyContext()}
            onDragStart={(entityId, pointerId, x, y) => {
              const label = representationById.get(entityId)?.label ?? entityId;
              setGhost({ x, y, label });
              dispatch({ type: "BEGIN_PALETTE_DRAG", entityId, pointerId });
            }}
            onDragMove={(x, y) => setGhost((g) => (g ? { ...g, x, y } : null))}
            onDragEnd={endRowDrag}
            onDragCancel={() => {
              setGhost(null);
              dispatch({ type: "CANCEL_INTERACTION" });
            }}
          />
        </section>

        {inspectorOpen && panel === "add" ? (
          <div className={styles.right}>
            <AddContextPanel
              dimensions={groups}
              locked={locked}
              onAdd={(id) => addEntity(id)}
              onBack={() => setPanel("inspector")}
            />
          </div>
        ) : inspectorOpen ? (
          <div className={styles.right}>
            <Inspector
              selection={inspectorSelection}
              root={{
                title,
                stableId: dataset.selectedRecord.stableId,
                creatorAttribution: rootMeta?.creatorAttribution,
                objectType: rootMeta?.objectType,
                dateDisplay: rootMeta?.dateDisplay,
                sourceName: rootMeta?.sourceName,
              }}
              provenance={{
                releaseId: dataset.release.releaseId,
                manifestSha256: dataset.release.manifestSha256,
                projectionId: governed?.projectionId ?? "",
                projectionSha256: governed?.projectionSha256 ?? "",
                policyVersion: governed?.policyVersion ?? "",
                explanationRegistryVersion: governed?.explanationRegistryVersion ?? "",
              }}
              cohort={cohort}
              locked={locked}
              onAdd={(id) => addEntity(id)}
              onRemove={hideEntity}
              onCopy={(text, doneNote) => void copy(text, doneNote)}
              copiedHashNote={COPIED_HASH}
              copiedTechnicalNote={COPIED_TECHNICAL}
            />
          </div>
        ) : null}
      </main>

      {ghost ? (
        <div className={styles.ghost} style={{ transform: `translate(${ghost.x + 12}px, ${ghost.y + 12}px)` }} aria-hidden="true">
          {ghost.label}
        </div>
      ) : null}

      {/* the reference's accessible rows, one per visible representation,
          kept derived so the rows panel and the canvas stay one unit */}
      <span className="sr-only" aria-hidden="true" data-visible-rows={visibleRows.length} />
    </div>
  );
}

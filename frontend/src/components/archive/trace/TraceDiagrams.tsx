"use client";

import dynamic from "next/dynamic";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type FocusEvent,
  type KeyboardEvent,
  type MouseEvent,
} from "react";
import styles from "./TraceExplorer.module.css";
import {
  TRACE_FAMILY_META,
  buildTraceMarks,
  diagramModeForFamily,
  selectionForEdge,
  tracePeerNode,
  traceTypeFor,
  type TraceSelection,
} from "./trace-taxonomy";
import type { RelationFamily, TraceAtlas, TraceEdge, TraceGraph, TraceNode } from "./trace-types";

export type DiagramMode = "medium" | "geography" | "sources";

type DiagramOption = {
  mode: DiagramMode;
  label: string;
  question: string;
};

const DIAGRAM_OPTIONS: DiagramOption[] = [
  { mode: "medium", label: "Medium / context", question: "How is this object situated in media and context?" },
  { mode: "geography", label: "Time / geography", question: "When and where is this object recorded?" },
  { mode: "sources", label: "Sources", question: "Which evidence sources document this object?" },
];

const TimeGeographyMap = dynamic(() => import("./TimeGeographyMap"), {
  ssr: false,
  loading: () => <p className={styles.diagramLoading}>Loading geographic boundary layer…</p>,
});

function nodeMap(graph: TraceGraph) {
  return new Map(graph.nodes.map((node) => [node.id, node]));
}

function externalProps(href: string) {
  return href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {};
}

function stationHref(edge: TraceEdge, peer?: TraceNode) {
  return peer?.href || edge.evidenceUrl;
}

function shortLabel(value: string, limit = 44) {
  if (value.length <= limit) return value;
  return `${value.slice(0, limit - 1).trim()}…`;
}

function familyEdges(graph: TraceGraph, family: RelationFamily) {
  return graph.edges.filter((edge) => edge.family === family);
}

function relationGroups(edges: TraceEdge[]) {
  const groups = new Map<string, TraceEdge[]>();
  for (const edge of edges) {
    const group = groups.get(edge.label) ?? [];
    group.push(edge);
    groups.set(edge.label, group);
  }
  return Array.from(groups, ([label, grouped]) => ({ label, edges: grouped }));
}

function selectOnPlainClick(
  event: MouseEvent<Element>,
  selection: TraceSelection,
  onSelect: (selection: TraceSelection) => void,
) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  onSelect(selection);
}

function useMobileVisualCenter(key: string) {
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !window.matchMedia("(max-width: 760px)").matches) return;
    const frame = window.requestAnimationFrame(() => {
      container.scrollLeft = Math.max(0, (container.scrollWidth - container.clientWidth) / 2);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [key]);
  return containerRef;
}

export default function TraceDiagrams({
  atlas,
  graph,
  selection,
  onSelect,
}: {
  atlas: TraceAtlas;
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const [mode, setMode] = useState<DiagramMode>("medium");
  useEffect(() => setMode("medium"), [graph.object.id]);
  useEffect(() => {
    const selectedEdge = graph.edges.find((edge) => edge.id === selection?.edgeId);
    if (selectedEdge) setMode(diagramModeForFamily(selectedEdge.family));
  }, [graph.edges, selection?.edgeId]);

  return (
    <>
      <DiagramModeControl mode={mode} setMode={setMode} />
      {mode === "medium" ? (
        <MediumContextMetro graph={graph} selection={selection} onSelect={onSelect} />
      ) : null}
      {mode === "geography" ? (
        <TimeGeographyMap atlas={atlas} graph={graph} selection={selection} onSelect={onSelect} />
      ) : null}
      {mode === "sources" ? (
        <SourceRootedTree graph={graph} selection={selection} onSelect={onSelect} />
      ) : null}
    </>
  );
}

function DiagramModeControl({
  mode,
  setMode,
}: {
  mode: DiagramMode;
  setMode: (mode: DiagramMode) => void;
}) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const current = DIAGRAM_OPTIONS.find((option) => option.mode === mode) ?? DIAGRAM_OPTIONS[0];

  function closeWhenFocusLeaves(event: FocusEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      triggerRef.current?.focus();
    }
  }

  return (
    <div
      className={styles.diagramModeControl}
      data-open={open}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onBlur={closeWhenFocusLeaves}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        className={styles.diagramModeTrigger}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
      >
        <DiagramIcon mode={mode} />
        <span>{current.label}</span>
        <span className={styles.modeChevron} aria-hidden="true">⌄</span>
      </button>
      <div id={menuId} className={styles.diagramModeMenu} role="menu" aria-label="Choose TRACE research view">
        {DIAGRAM_OPTIONS.map((option) => (
          <button
            key={option.mode}
            type="button"
            role="menuitemradio"
            aria-checked={mode === option.mode}
            data-selected={mode === option.mode}
            onClick={() => {
              setMode(option.mode);
              setOpen(false);
              triggerRef.current?.focus();
            }}
          >
            <DiagramIcon mode={option.mode} />
            <span><strong>{option.label}</strong><small>{option.question}</small></span>
          </button>
        ))}
      </div>
    </div>
  );
}

function DiagramIcon({ mode }: { mode: DiagramMode }) {
  if (mode === "medium") {
    return (
      <svg className={styles.diagramModeIcon} viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 7h12l4 4v6H8l-4-4" />
        <circle cx="7" cy="7" r="2" /><circle cx="19" cy="11" r="2" /><circle cx="8" cy="17" r="2" />
      </svg>
    );
  }
  if (mode === "geography") {
    return (
      <svg className={styles.diagramModeIcon} viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
      </svg>
    );
  }
  return (
    <svg className={styles.diagramModeIcon} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 12h5m0 0 4-6m-4 6 4 6m0-12h7m-7 12h7" />
      <circle cx="4" cy="12" r="2" /><circle cx="20" cy="6" r="2" /><circle cx="20" cy="18" r="2" />
    </svg>
  );
}

function MobileTraceNodeField({
  graph,
  edges,
  activeEdgeId,
  onActiveEdgeId,
  onSelect,
  family,
}: {
  graph: TraceGraph;
  edges: TraceEdge[];
  activeEdgeId: string;
  onActiveEdgeId: (edgeId: string) => void;
  onSelect: (selection: TraceSelection) => void;
  family: "medium" | "sources";
}) {
  const nodes = nodeMap(graph);
  const marks = buildTraceMarks(graph);
  const visibleEdges = edges.slice(0, 19);
  const activeEdge = visibleEdges.find((edge) => edge.id === activeEdgeId);
  const activePeer = activeEdge
    ? tracePeerNode(activeEdge, graph.object.nodeId, nodes)
    : undefined;
  const activeSelection = activeEdge ? selectionForEdge(graph, activeEdge) : null;
  const activeTitle = activeEdge
    ? activePeer?.label || activeEdge.label
    : graph.object.title;
  const activeMeta = activeEdge
    ? `${traceTypeFor(activeEdge.label).label} · ${activeEdge.direction}`
    : "Selected design object · TRACE origin";
  const activeDescription = activeEdge
    ? activeEdge.evidenceText || "Documented in the object-level source record."
    : family === "medium"
      ? "Choose a numbered point to inspect one documented medium or context relation."
      : "Choose a numbered point to inspect one documented source or provenance relation.";
  const fieldItems: Array<{ edge?: TraceEdge; code: string; title: string }> = [
    { code: "01", title: graph.object.title },
    ...visibleEdges.map((edge, index) => {
      const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
      const edgeSelection = selectionForEdge(graph, edge);
      return {
        edge,
        code: marks.nodeMarks.get(edgeSelection.nodeId) ?? String(index + 2).padStart(2, "0"),
        title: peer?.label || edge.label,
      };
    }),
  ];

  return (
    <div className={styles.mobileTraceField} data-family={family}>
      <div className={styles.mobileTraceFieldStage}>
        <svg viewBox="0 0 390 610" aria-hidden="true">
          <g className={styles.mobileTraceGuideGrid}>
            {Array.from({ length: 9 }, (_, index) => <line key={`gx-${index}`} x1={24 + index * 44} y1="70" x2={24 + index * 44} y2="585" />)}
            {Array.from({ length: 12 }, (_, index) => <line key={`gy-${index}`} x1="18" y1={80 + index * 44} x2="372" y2={80 + index * 44} />)}
          </g>
          <g className={styles.mobileTraceRays}>
            {fieldItems.slice(1).map((item, index) => {
              const col = (index + 1) % 4;
              const row = Math.floor((index + 1) / 4);
              const x = 56 + col * 88;
              const y = 118 + row * 92;
              return <path key={item.edge?.id ?? item.code} d={`M56 118 Q${Math.max(56, x - 36)} ${Math.max(118, y - 28)} ${x} ${y}`} />;
            })}
          </g>
        </svg>
        <p className={styles.mobileTraceFieldLabel}>
          {family === "medium" ? "MEDIUM / CONTEXT" : "SOURCE / PROVENANCE"}
        </p>
        <div className={styles.mobileTraceNodes} aria-label={`${family} TRACE nodes`}>
          {fieldItems.map((item, index) => {
            const col = index % 4;
            const row = Math.floor(index / 4);
            const distance = col + row;
            const selected = item.edge ? item.edge.id === activeEdgeId : activeEdgeId === "";
            const style = {
              "--node-x": `${56 + col * 88}px`,
              "--node-y": `${118 + row * 92}px`,
              "--node-alpha": String(Math.max(0.46, 1 - distance * 0.09)),
              "--node-delay": `${Math.min(index * 34, 480)}ms`,
            } as CSSProperties;
            return (
              <button
                key={item.edge?.id ?? "object-root"}
                type="button"
                className={styles.mobileTraceNode}
                style={style}
                aria-pressed={selected}
                aria-label={`${item.code}: ${item.title}`}
                onClick={() => onActiveEdgeId(item.edge?.id ?? "")}
              >
                {String(index + 1).padStart(2, "0")}
              </button>
            );
          })}
          {Array.from({ length: Math.max(0, 20 - fieldItems.length) }, (_, slotIndex) => {
            const index = fieldItems.length + slotIndex;
            const col = index % 4;
            const row = Math.floor(index / 4);
            return (
              <i
                key={`empty-slot-${index}`}
                className={styles.mobileTraceEmptyNode}
                style={{
                  "--node-x": `${56 + col * 88}px`,
                  "--node-y": `${118 + row * 92}px`,
                } as CSSProperties}
                aria-hidden="true"
              />
            );
          })}
        </div>
      </div>
      <article className={styles.mobileTraceSelection} aria-live="polite">
        <div>
          <span>{activeEdge && activeSelection ? marks.nodeMarks.get(activeSelection.nodeId) : "01"}</span>
          <p>{activeMeta}</p>
        </div>
        <h4>{activeTitle}</h4>
        <p>{activeDescription}</p>
        {activeEdge && activeSelection ? (
          <button type="button" onClick={() => onSelect(activeSelection)}>Open evidence</button>
        ) : null}
      </article>
    </div>
  );
}

function MediumContextMetro({
  graph,
  selection,
  onSelect,
}: {
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const nodes = nodeMap(graph);
  const marks = buildTraceMarks(graph);
  const edges = familyEdges(graph, "medium_context");
  const groups = relationGroups(edges);
  const visualRef = useMobileVisualCenter(`${graph.object.id}-medium`);
  const [focusedEdgeId, setFocusedEdgeId] = useState("");
  useEffect(() => setFocusedEdgeId(""), [graph.object.id]);
  const focusedEdge = edges.find((edge) => edge.id === focusedEdgeId) ?? edges[0];
  const focusedPeer = focusedEdge ? tracePeerNode(focusedEdge, graph.object.nodeId, nodes) : undefined;
  const routeLayouts = [
    { path: "M560 385 L500 325 V145 H118", x1: 150, x2: 476, y: 145, terminalX: 110, terminalY: 145, labelX: 150, labelY: 116 },
    { path: "M560 385 L620 325 V145 H1002", x1: 644, x2: 970, y: 145, terminalX: 1010, terminalY: 145, labelX: 648, labelY: 116 },
    { path: "M560 385 L478 467 H140 L92 515", x1: 170, x2: 448, y: 467, terminalX: 86, terminalY: 521, labelX: 170, labelY: 498 },
    { path: "M560 385 L642 467 H980 L1028 515", x1: 672, x2: 950, y: 467, terminalX: 1034, terminalY: 521, labelX: 676, labelY: 498 },
    { path: "M560 385 V632", x1: 560, x2: 560, y: 0, terminalX: 560, terminalY: 640, labelX: 586, labelY: 596 },
    { path: "M560 385 H882 L938 329", x1: 650, x2: 856, y: 385, terminalX: 944, terminalY: 323, labelX: 690, labelY: 416 },
    { path: "M560 385 H238 L182 329", x1: 264, x2: 470, y: 385, terminalX: 176, terminalY: 323, labelX: 270, labelY: 416 },
  ];

  return (
    <section className={styles.diagram} aria-labelledby="trace-medium-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>MEDIUM / CONTEXT METRO</p>
          <h3 id="trace-medium-title">Media and context routes</h3>
        </div>
        <span>{groups.length} evidence lines · {edges.length} labelled stations · interchange is the selected object</span>
      </div>

      {edges.length ? (
        <div ref={visualRef} className={`${styles.diagramDesktop} ${styles.metroSystem}`}>
          <svg
            className={`${styles.routeMapSvg} ${styles.desktopDiagramSvg}`}
            viewBox="0 0 1120 700"
            role="img"
            aria-labelledby="medium-map-title medium-map-desc"
          >
            <title id="medium-map-title">Medium and context metro map for {graph.object.title}</title>
            <desc id="medium-map-desc">
              Only medium and documented context relations are shown. Parallel lines separate relation types; stations are evidence nodes, not influence claims.
            </desc>
            <g className={styles.metroGrid} aria-hidden="true">
              {Array.from({ length: 29 }, (_, index) => <line key={`v-${index}`} x1={index * 40} y1="0" x2={index * 40} y2="700" />)}
              {Array.from({ length: 18 }, (_, index) => <line key={`h-${index}`} x1="0" y1={index * 40} x2="1120" y2={index * 40} />)}
            </g>
            {groups.slice(0, routeLayouts.length).map((group, routeIndex) => {
              const layout = routeLayouts[routeIndex];
              return (
                <g key={group.label} className={styles.metroRoute} data-route-index={routeIndex} data-muted={Boolean(focusedEdgeId) && !group.edges.some((edge) => edge.id === focusedEdgeId)}>
                  <path
                    className={styles.mediumRouteLine}
                    data-selected={group.edges.some((edge) => edge.id === selection?.edgeId)}
                    d={layout.path}
                  />
                  <circle className={styles.metroTerminal} cx={layout.terminalX} cy={layout.terminalY} r="11" />
                  <text className={styles.routeLabel} x={layout.labelX} y={layout.labelY}>{traceTypeFor(group.label).code} · {group.label.replaceAll("_", " ")}</text>
                  {group.edges.map((edge, stationIndex) => {
                    const vertical = layout.x1 === layout.x2;
                    const progress = (stationIndex + 1) / (group.edges.length + 1);
                    const x = vertical ? layout.x1 : layout.x1 + (layout.x2 - layout.x1) * progress;
                    const y = vertical ? 428 + progress * 178 : layout.y;
                    const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
                    const href = stationHref(edge, peer);
                    const edgeSelection = selectionForEdge(graph, edge);
                    const nodeCode = marks.nodeMarks.get(edgeSelection.nodeId) ?? "N--";
                    const edgeCode = marks.edgeMarks.get(edge.id) ?? "MC-E--";
                    return (
                      <a
                        key={edge.id}
                        href={href}
                        data-selected={selection?.edgeId === edge.id}
                        data-focused={focusedEdgeId === edge.id}
                        aria-label={`${nodeCode}, ${edgeCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                        onMouseEnter={() => setFocusedEdgeId(edge.id)}
                        onFocus={() => setFocusedEdgeId(edge.id)}
                        onClick={(event) => selectOnPlainClick(event, edgeSelection, onSelect)}
                        {...externalProps(href)}
                      >
                        <circle className={styles.mediumRouteStation} cx={x} cy={y} r={focusedEdgeId === edge.id ? 13 : 10} />
                        <text className={styles.stationCode} x={x} y={y + 3.5} textAnchor="middle">{nodeCode}</text>
                        <text className={styles.metroStationLabel} x={vertical ? x + 19 : x} y={vertical ? y + 4 : y + (stationIndex % 2 === 0 ? -19 : 29)} textAnchor={vertical ? "start" : "middle"}>{shortLabel(peer?.label || edge.label, 24)}</text>
                      </a>
                    );
                  })}
                </g>
              );
            })}
            <g className={styles.metroInterchange}>
              <circle className={styles.interchangeOuter} cx="560" cy="385" r="37" />
              <circle className={styles.interchangeInner} cx="560" cy="385" r="17" />
              <rect x="430" y="250" width="260" height="58" />
              <text className={styles.interchangeLabel} x="560" y="272" textAnchor="middle">OBJ · INTERCHANGE</text>
              <text className={styles.objectLabel} x="560" y="293" textAnchor="middle">{shortLabel(graph.object.title, 36)}</text>
            </g>
            <g className={styles.metroLegend} transform="translate(34 646)"><text x="0" y="0">LINES = RECORDED RELATION TYPES</text><text x="360" y="0">STATIONS = EVIDENCE NODES</text><text x="760" y="0">NO LINE = HISTORICAL INFLUENCE</text></g>
          </svg>
          <svg
            className={styles.mobileDiagramSvg}
            viewBox="0 0 390 820"
            role="img"
            aria-labelledby="mobile-medium-map-title mobile-medium-map-desc"
          >
            <title id="mobile-medium-map-title">Mobile medium and context metro for {graph.object.title}</title>
            <desc id="mobile-medium-map-desc">
              The selected object is the interchange. Each saturated route is one documented relation type and each labelled stop is an evidence node. No route claims historical influence.
            </desc>
            <g className={styles.mobileDiagramGrid} aria-hidden="true">
              {Array.from({ length: 14 }, (_, index) => <line key={`mv-${index}`} x1={index * 30} y1="0" x2={index * 30} y2="820" />)}
              {Array.from({ length: 28 }, (_, index) => <line key={`mh-${index}`} x1="0" y1={index * 30} x2="390" y2={index * 30} />)}
            </g>
            <g className={styles.mobileMetroTitle}>
              <text x="24" y="180">MEDIA / CONTEXT</text>
              <text x="24" y="197">DOCUMENTED ROUTES</text>
            </g>
            {groups.slice(0, 4).map((group, routeIndex) => {
              const y = 350 + routeIndex * 115;
              const leftEntry = routeIndex % 2 === 0;
              const entryX = leftEntry ? 92 : 298;
              const terminalX = leftEntry ? 360 : 30;
              const trunkX = 180 + routeIndex * 10;
              return (
                <g key={`mobile-${group.label}`} className={styles.metroRoute} data-route-index={routeIndex} data-muted={Boolean(focusedEdgeId) && !group.edges.some((edge) => edge.id === focusedEdgeId)}>
                  <path className={styles.mediumRouteLine} d={`M195 235 L${trunkX} 252 V${y - 52} H${entryX} V${y} H${terminalX}`} />
                  <circle className={styles.metroTerminal} cx={terminalX} cy={y} r="8" />
                  <text className={styles.mobileRouteLabel} x="24" y={y - 14}>{traceTypeFor(group.label).code} · {group.label.replaceAll("_", " ")}</text>
                  {group.edges.slice(0, 3).map((edge, stationIndex) => {
                    const progress = (stationIndex + 1) / (Math.min(group.edges.length, 3) + 1);
                    const x = entryX + (terminalX - entryX) * progress;
                    const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
                    const href = stationHref(edge, peer);
                    const edgeSelection = selectionForEdge(graph, edge);
                    const nodeCode = marks.nodeMarks.get(edgeSelection.nodeId) ?? "N--";
                    const edgeCode = marks.edgeMarks.get(edge.id) ?? "MC-E--";
                    return (
                      <a
                        key={`mobile-${edge.id}`}
                        href={href}
                        data-selected={selection?.edgeId === edge.id}
                        data-focused={focusedEdgeId === edge.id}
                        aria-label={`${nodeCode}, ${edgeCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                        onFocus={() => setFocusedEdgeId(edge.id)}
                        onClick={(event) => selectOnPlainClick(event, edgeSelection, onSelect)}
                        {...externalProps(href)}
                      >
                        <circle className={styles.mediumRouteStation} cx={x} cy={y} r="9" />
                        <text className={styles.stationCode} x={x} y={y + 3.5} textAnchor="middle">{nodeCode}</text>
                        <text className={styles.mobileMetroLabel} x={x} y={y + 25} textAnchor="middle">{shortLabel(peer?.label || edge.label, 18)}</text>
                      </a>
                    );
                  })}
                </g>
              );
            })}
            <g className={styles.metroInterchange}>
              <rect x="55" y="108" width="280" height="42" />
              <text className={styles.interchangeLabel} x="195" y="125" textAnchor="middle">OBJ · INTERCHANGE</text>
              <text className={styles.objectLabel} x="195" y="141" textAnchor="middle">{shortLabel(graph.object.title, 32)}</text>
              <circle className={styles.interchangeOuter} cx="195" cy="235" r="31" />
              <circle className={styles.interchangeInner} cx="195" cy="235" r="13" />
            </g>
            <g className={styles.mobileDiagramLegend}>
              <text x="24" y="783">TAP A STATION · DOCUMENTED EVIDENCE ONLY</text>
              <text x="24" y="800">NO AUTOMATED INFLUENCE ASSERTION</text>
            </g>
          </svg>
          <MobileTraceNodeField
            graph={graph}
            edges={edges}
            activeEdgeId={focusedEdgeId}
            onActiveEdgeId={setFocusedEdgeId}
            onSelect={onSelect}
            family="medium"
          />
          {focusedEdge ? (
            <aside className={styles.metroReadout} aria-live="polite">
              <span>{marks.nodeMarks.get(selectionForEdge(graph, focusedEdge).nodeId)} · {traceTypeFor(focusedEdge.label).code}</span>
              <h4>{focusedPeer?.label || focusedEdge.label}</h4>
              <p>{focusedEdge.label.replaceAll("_", " ")} · {focusedEdge.direction}</p>
              <p>{focusedEdge.evidenceText || "Documented in the object-level source record."}</p>
            </aside>
          ) : null}
        </div>
      ) : <p className={styles.emptyDiagram}>No medium or context edge is documented for this object.</p>}

      <p className={styles.mobileDiagramNote}>Swipe or tap the visual system; supporting evidence remains available from the information drawer.</p>
      <EvidenceIndex graph={graph} edges={edges} label="Medium / context" selection={selection} onSelect={onSelect} />
    </section>
  );
}

function SourceRootedTree({
  graph,
  selection,
  onSelect,
}: {
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const nodes = nodeMap(graph);
  const marks = buildTraceMarks(graph);
  const edges = familyEdges(graph, "source_provenance");
  const groups = relationGroups(edges);
  const [activeEdgeId, setActiveEdgeId] = useState("");
  useEffect(() => setActiveEdgeId(""), [graph.object.id]);
  const visualRef = useMobileVisualCenter(`${graph.object.id}-sources`);
  let leafCursor = 76;
  const branches = groups.map((group) => {
    const leaves = group.edges.map((edge, index) => ({ edge, y: leafCursor + index * 46 }));
    const first = leaves.at(0)?.y ?? leafCursor;
    const last = leaves.at(-1)?.y ?? first;
    const y = (first + last) / 2;
    leafCursor = last + 90;
    return { ...group, leaves, y };
  });
  const height = Math.max(430, leafCursor + 36);
  const rootY = branches.length ? branches.reduce((sum, branch) => sum + branch.y, 0) / branches.length : height / 2;

  return (
    <section className={styles.diagram} aria-labelledby="trace-source-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>SOURCE ROOTED TREE</p>
          <h3 id="trace-source-title">Source and provenance branches</h3>
        </div>
        <span>{edges.length} source/provenance leaves · line width indicates hierarchy only</span>
      </div>

      {edges.length ? (
        <div ref={visualRef} className={styles.diagramDesktop}>
          <svg
            className={`${styles.treeSvg} ${styles.desktopDiagramSvg}`}
            viewBox={`0 0 1120 ${height}`}
            role="img"
            aria-labelledby="source-tree-title source-tree-desc"
          >
            <title id="source-tree-title">Source and provenance tree for {graph.object.title}</title>
            <desc id="source-tree-desc">
              The object root branches first by documented source relation, then to actual evidence nodes. No medium, place or influence relation is shown.
            </desc>
            {branches.map((branch) => (
              <g key={branch.label}>
                <path
                  className={styles.sourceTrunk}
                  data-selected={branch.edges.some((edge) => edge.id === selection?.edgeId)}
                  d={`M 124 ${rootY} C 230 ${rootY}, 210 ${branch.y}, 342 ${branch.y}`}
                />
                <circle className={styles.sourceHub} cx="342" cy={branch.y} r="12" />
                <text className={styles.treeBranchLabel} x="370" y={branch.y - 15}>
                  {traceTypeFor(branch.label).code} · {branch.label.replaceAll("_", " ")}
                </text>
                {branch.leaves.map(({ edge, y }) => {
                  const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
                  const href = stationHref(edge, peer);
                  const edgeSelection = selectionForEdge(graph, edge);
                  const nodeCode = marks.nodeMarks.get(edgeSelection.nodeId) ?? "N--";
                  const edgeCode = marks.edgeMarks.get(edge.id) ?? "SP-E--";
                  return (
                    <g key={edge.id}>
                      <path
                        className={styles.sourceTwig}
                        data-selected={selection?.edgeId === edge.id}
                        d={`M 342 ${branch.y} C 500 ${branch.y}, 498 ${y}, 650 ${y}`}
                      />
                      <a
                        href={href}
                        data-selected={selection?.edgeId === edge.id}
                        aria-label={`${nodeCode}, ${edgeCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                        onClick={(event) => selectOnPlainClick(event, edgeSelection, onSelect)}
                        {...externalProps(href)}
                      >
                        <circle className={styles.sourceLeaf} cx="650" cy={y} r="7" />
                        <text className={styles.treeLeafLabel} x="672" y={y - 3}>{nodeCode} · {shortLabel(peer?.label || edge.label, 48)}</text>
                        <text className={styles.treeLeafMeta} x="672" y={y + 14}>{edgeCode} · {edge.direction} · {edge.label.replaceAll("_", " ")}</text>
                      </a>
                    </g>
                  );
                })}
              </g>
            ))}
            <circle className={styles.treeRoot} cx="124" cy={rootY} r="25" />
            <circle className={styles.treeRootInner} cx="124" cy={rootY} r="9" />
            <text className={styles.treeRootLabel} x="74" y={rootY + 48}>OBJ · OBJECT ROOT</text>
          </svg>
          <svg
            className={styles.mobileDiagramSvg}
            viewBox="0 0 390 820"
            role="img"
            aria-labelledby="mobile-source-tree-title mobile-source-tree-desc"
          >
            <title id="mobile-source-tree-title">Mobile source and provenance tree for {graph.object.title}</title>
            <desc id="mobile-source-tree-desc">
              The object root branches by documented source relation and terminates in source evidence nodes. It contains no inferred influence edge.
            </desc>
            <g className={styles.mobileDiagramGrid} aria-hidden="true">
              {Array.from({ length: 14 }, (_, index) => <line key={`sv-${index}`} x1={index * 30} y1="0" x2={index * 30} y2="820" />)}
              {Array.from({ length: 28 }, (_, index) => <line key={`sh-${index}`} x1="0" y1={index * 30} x2="390" y2={index * 30} />)}
            </g>
            <rect className={styles.mobileRootCard} x="45" y="108" width="300" height="54" />
            <text className={styles.mobileRootCode} x="195" y="128" textAnchor="middle">OBJ · OBJECT ROOT</text>
            <text className={styles.mobileRootTitle} x="195" y="147" textAnchor="middle">{shortLabel(graph.object.title, 32)}</text>
            <circle className={styles.treeRoot} cx="195" cy="205" r="25" />
            <circle className={styles.treeRootInner} cx="195" cy="205" r="9" />
            {branches.slice(0, 4).map((branch, branchIndex) => {
              const branchY = 340 + branchIndex * 145;
              const left = branchIndex % 2 === 0;
              const hubX = left ? 82 : 308;
              const leafStart = left ? 158 : 232;
              return (
                <g key={`mobile-source-${branch.label}`}>
                  <path
                    className={styles.sourceTrunk}
                    data-selected={branch.edges.some((edge) => edge.id === selection?.edgeId)}
                    d={`M195 205 V${branchY - 48} Q195 ${branchY} ${hubX} ${branchY}`}
                  />
                  <circle className={styles.sourceHub} cx={hubX} cy={branchY} r="10" />
                  <text className={styles.mobileTreeBranchLabel} x="24" y={branchY - 17}>{traceTypeFor(branch.label).code} · {branch.label.replaceAll("_", " ")}</text>
                  {branch.edges.slice(0, 3).map((edge, edgeIndex) => {
                    const leafX = left ? leafStart + edgeIndex * 76 : leafStart - edgeIndex * 76;
                    const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
                    const href = stationHref(edge, peer);
                    const edgeSelection = selectionForEdge(graph, edge);
                    const nodeCode = marks.nodeMarks.get(edgeSelection.nodeId) ?? "N--";
                    const edgeCode = marks.edgeMarks.get(edge.id) ?? "SP-E--";
                    return (
                      <g key={`mobile-source-${edge.id}`}>
                        <path className={styles.sourceTwig} data-selected={selection?.edgeId === edge.id} d={`M${hubX} ${branchY} H${leafX}`} />
                        <a
                          href={href}
                          data-selected={selection?.edgeId === edge.id}
                          aria-label={`${nodeCode}, ${edgeCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                          onClick={(event) => selectOnPlainClick(event, edgeSelection, onSelect)}
                          {...externalProps(href)}
                        >
                          <circle className={styles.sourceLeaf} cx={leafX} cy={branchY} r="8" />
                          <text className={styles.mobileTreeNodeCode} x={leafX} y={branchY + 3.5} textAnchor="middle">{nodeCode}</text>
                          <text className={styles.mobileTreeLeafLabel} x={leafX} y={branchY + 25} textAnchor="middle">{shortLabel(peer?.label || edge.label, 16)}</text>
                        </a>
                      </g>
                    );
                  })}
                </g>
              );
            })}
            <g className={styles.mobileDiagramLegend}>
              <text x="24" y="783">ROOT → RELATION → SOURCE EVIDENCE</text>
              <text x="24" y="800">NO MEDIUM, PLACE OR INFLUENCE MERGED</text>
            </g>
          </svg>
          <MobileTraceNodeField
            graph={graph}
            edges={edges}
            activeEdgeId={activeEdgeId}
            onActiveEdgeId={setActiveEdgeId}
            onSelect={onSelect}
            family="sources"
          />
        </div>
      ) : <p className={styles.emptyDiagram}>No source or provenance edge is documented for this object.</p>}

      <p className={styles.mobileDiagramNote}>Swipe or tap the visual system; supporting evidence remains available from the information drawer.</p>
      <EvidenceIndex graph={graph} edges={edges} label="Sources / provenance" selection={selection} onSelect={onSelect} />
    </section>
  );
}

function EvidenceIndex({
  graph,
  edges,
  label,
  selection,
  onSelect,
}: {
  graph: TraceGraph;
  edges: TraceEdge[];
  label: string;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const nodes = nodeMap(graph);
  const marks = buildTraceMarks(graph);
  return (
    <div
      className={`${styles.stationIndex} ${styles.stationIndexSingle} ${styles.diagramEvidenceFallback}`}
      aria-label={`${label} evidence index`}
    >
      <section>
        <h4><span>{TRACE_FAMILY_META[edges[0]?.family ?? "medium_context"].code}</span>{label}</h4>
        {edges.length ? (
          <ol>
            {edges.map((edge) => {
              const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
              const href = stationHref(edge, peer);
              const edgeSelection = selectionForEdge(graph, edge);
              return (
                <li key={edge.id} data-selected={selection?.edgeId === edge.id}>
                  <button type="button" onClick={() => onSelect(edgeSelection)}>
                    {marks.nodeMarks.get(edgeSelection.nodeId)}
                  </button>
                  <span>
                    <a href={href} {...externalProps(href)}>{peer?.label || edge.label}</a>
                    <small>{marks.edgeMarks.get(edge.id)} · {edge.direction} · {traceTypeFor(edge.label).code} · {edge.reviewState.replaceAll("_", " ")}</small>
                  </span>
                </li>
              );
            })}
          </ol>
        ) : <p>No documented evidence in this view.</p>}
      </section>
    </div>
  );
}

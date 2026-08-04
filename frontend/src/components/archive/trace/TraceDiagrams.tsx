"use client";

import dynamic from "next/dynamic";
import {
  useEffect,
  useId,
  useRef,
  useState,
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
  const height = Math.max(330, groups.length * 96 + 130);
  const rootY = height / 2;

  return (
    <section className={styles.diagram} aria-labelledby="trace-medium-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>MEDIUM / CONTEXT METRO</p>
          <h3 id="trace-medium-title">Media and context routes</h3>
        </div>
        <span>{edges.length} medium/context stations · each trunk is one recorded relation type</span>
      </div>

      {edges.length ? (
        <div className={styles.diagramDesktop}>
          <svg
            className={styles.routeMapSvg}
            viewBox={`0 0 1120 ${height}`}
            role="img"
            aria-labelledby="medium-map-title medium-map-desc"
          >
            <title id="medium-map-title">Medium and context metro map for {graph.object.title}</title>
            <desc id="medium-map-desc">
              Only medium and documented context relations are shown. Parallel lines separate relation types; stations are evidence nodes, not influence claims.
            </desc>
            {groups.map((group, routeIndex) => {
              const y = 78 + routeIndex * 96;
              const path = `M 118 ${rootY} H 205 L 286 ${y} H 1040`;
              return (
                <g key={group.label}>
                  <path
                    className={styles.mediumRouteLine}
                    data-route-index={routeIndex % 4}
                    data-selected={group.edges.some((edge) => edge.id === selection?.edgeId)}
                    d={path}
                  />
                  <text className={styles.routeLabel} x="294" y={y - 20}>
                    {traceTypeFor(group.label).code} · {group.label.replaceAll("_", " ")}
                  </text>
                  {group.edges.map((edge, stationIndex) => {
                    const x = 330 + ((stationIndex + 0.5) / group.edges.length) * 660;
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
                        aria-label={`${nodeCode}, ${edgeCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                        onClick={(event) => selectOnPlainClick(event, edgeSelection, onSelect)}
                        {...externalProps(href)}
                      >
                        <circle className={styles.mediumRouteStation} data-route-index={routeIndex % 4} cx={x} cy={y} r="10" />
                        <text className={styles.stationCode} x={x} y={y + 3.5} textAnchor="middle">{nodeCode}</text>
                      </a>
                    );
                  })}
                </g>
              );
            })}
            <circle className={styles.interchangeOuter} cx="118" cy={rootY} r="24" />
            <circle className={styles.interchangeInner} cx="118" cy={rootY} r="10" />
            <text className={styles.interchangeLabel} x="80" y={rootY + 44}>OBJ · OBJECT</text>
            <text className={styles.objectLabel} x="58" y={rootY + 70}>{shortLabel(graph.object.title, 30)}</text>
          </svg>
        </div>
      ) : <p className={styles.emptyDiagram}>No medium or context edge is documented for this object.</p>}

      <p className={styles.mobileDiagramNote}>On small screens the evidence index replaces the full metro drawing.</p>
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
        <div className={styles.diagramDesktop}>
          <svg
            className={styles.treeSvg}
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
        </div>
      ) : <p className={styles.emptyDiagram}>No source or provenance edge is documented for this object.</p>}

      <p className={styles.mobileDiagramNote}>On small screens the evidence index replaces the full source tree.</p>
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

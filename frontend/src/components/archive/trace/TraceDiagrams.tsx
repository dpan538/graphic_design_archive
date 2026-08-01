import styles from "./TraceExplorer.module.css";
import type { RelationFamily, TraceEdge, TraceGraph, TraceNode } from "./trace-types";

type DiagramMode = "routes" | "tree";

type VisualRoute = {
  family: Exclude<RelationFamily, "historical_influence">;
  code: string;
  label: string;
  y: number;
};

const VISUAL_ROUTES: VisualRoute[] = [
  { family: "source_provenance", code: "P", label: "Source / provenance", y: 112 },
  { family: "time_place", code: "T", label: "Time / place", y: 230 },
  { family: "medium_context", code: "M", label: "Medium / context", y: 348 },
];

function nodeMap(graph: TraceGraph) {
  return new Map(graph.nodes.map((node) => [node.id, node]));
}

function peerNode(edge: TraceEdge, rootId: string, nodes: Map<string, TraceNode>) {
  if (edge.subject === rootId) return nodes.get(edge.object);
  if (edge.object === rootId) return nodes.get(edge.subject);
  return nodes.get(edge.object) ?? nodes.get(edge.subject);
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

function groupedEdges(graph: TraceGraph) {
  const groups = new Map<VisualRoute["family"], TraceEdge[]>();
  for (const route of VISUAL_ROUTES) groups.set(route.family, []);
  for (const edge of graph.edges) {
    if (edge.family === "historical_influence") continue;
    groups.get(edge.family)?.push(edge);
  }
  return groups;
}

export default function TraceDiagrams({ graph, mode }: { graph: TraceGraph; mode: DiagramMode }) {
  return mode === "routes" ? <EvidenceRouteMap graph={graph} /> : <RootedEvidenceTree graph={graph} />;
}

function EvidenceRouteMap({ graph }: { graph: TraceGraph }) {
  const nodes = nodeMap(graph);
  const groups = groupedEdges(graph);
  return (
    <section className={styles.diagram} aria-labelledby="trace-route-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>SCHEMATIC EVIDENCE NETWORK</p>
          <h3 id="trace-route-title">Object interchange and evidence routes</h3>
        </div>
        <span>{graph.edges.length} documented stations</span>
      </div>

      <div className={styles.diagramDesktop}>
        <svg
          className={styles.routeMapSvg}
          viewBox="0 0 1120 460"
          role="img"
          aria-labelledby="route-map-svg-title route-map-svg-desc"
        >
          <title id="route-map-svg-title">Evidence route map for {graph.object.title}</title>
          <desc id="route-map-svg-desc">
            Three coloured routes leave the selected object. Stations are documented source, time, place, medium and context nodes. Routes do not represent historical influence.
          </desc>

          {VISUAL_ROUTES.map((route) => {
            const edges = groups.get(route.family) ?? [];
            const bendY = route.y;
            const path = `M 118 230 H 205 L 286 ${bendY} H 1040`;
            return (
              <g key={route.family}>
                <path className={styles.routeLine} data-family={route.family} d={path} />
                <text className={styles.routeLabel} x="294" y={bendY - 20}>{route.code} · {route.label}</text>
                {edges.map((edge, index) => {
                  const x = 314 + ((index + 0.5) / Math.max(1, edges.length)) * 694;
                  const peer = peerNode(edge, graph.object.nodeId, nodes);
                  const href = stationHref(edge, peer);
                  const stationCode = `${route.code}${index + 1}`;
                  return (
                    <a
                      key={edge.id}
                      href={href}
                      aria-label={`${stationCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                      {...externalProps(href)}
                    >
                      <circle className={styles.routeStation} data-family={route.family} cx={x} cy={bendY} r="10" />
                      <text className={styles.stationCode} x={x} y={bendY + 3.5} textAnchor="middle">{stationCode}</text>
                    </a>
                  );
                })}
              </g>
            );
          })}

          <circle className={styles.interchangeOuter} cx="118" cy="230" r="24" />
          <circle className={styles.interchangeInner} cx="118" cy="230" r="10" />
          <text className={styles.interchangeLabel} x="80" y="274">OBJECT</text>
          <text className={styles.objectLabel} x="58" y="300">{shortLabel(graph.object.title, 30)}</text>
        </svg>
      </div>

      <p className={styles.mobileDiagramNote}>
        On small screens the station index below replaces the full route drawing.
      </p>
      <StationIndex graph={graph} groups={groups} nodes={nodes} />
    </section>
  );
}

function RootedEvidenceTree({ graph }: { graph: TraceGraph }) {
  const nodes = nodeMap(graph);
  const groups = groupedEdges(graph);
  const totalLeaves = VISUAL_ROUTES.reduce((sum, route) => sum + (groups.get(route.family)?.length ?? 0), 0);
  const height = Math.max(520, totalLeaves * 44 + 140);
  let leafCursor = 76;
  const branches = VISUAL_ROUTES.map((route) => {
    const edges = groups.get(route.family) ?? [];
    const leaves = edges.map((edge, index) => ({ edge, y: leafCursor + index * 44 }));
    const first = leaves.at(0)?.y ?? leafCursor;
    const last = leaves.at(-1)?.y ?? first;
    const y = (first + last) / 2;
    leafCursor = last + 86;
    return { route, leaves, y };
  });
  const rootY = branches.reduce((sum, branch) => sum + branch.y, 0) / branches.length;

  return (
    <section className={styles.diagram} aria-labelledby="trace-tree-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>ROOTED EVIDENCE TREE</p>
          <h3 id="trace-tree-title">One object, three documented branch families</h3>
        </div>
        <span>Line width indicates depth only</span>
      </div>

      <div className={styles.diagramDesktop}>
        <svg
          className={styles.treeSvg}
          viewBox={`0 0 1120 ${height}`}
          role="img"
          aria-labelledby="tree-svg-title tree-svg-desc"
        >
          <title id="tree-svg-title">Rooted evidence tree for {graph.object.title}</title>
          <desc id="tree-svg-desc">
            The selected object branches into source and provenance, time and place, and medium and documented context. Branches do not encode influence or strength.
          </desc>
          {branches.map(({ route, leaves, y }) => (
            <g key={route.family}>
              <path
                className={styles.treeTrunk}
                data-family={route.family}
                d={`M 124 ${rootY} C 230 ${rootY}, 210 ${y}, 342 ${y}`}
              />
              <circle className={styles.treeHub} data-family={route.family} cx="342" cy={y} r="12" />
              <text className={styles.treeBranchLabel} x="370" y={y - 15}>{route.code} · {route.label}</text>
              {leaves.map(({ edge, y: leafY }, index) => {
                const peer = peerNode(edge, graph.object.nodeId, nodes);
                const href = stationHref(edge, peer);
                const stationCode = `${route.code}${index + 1}`;
                return (
                  <g key={edge.id}>
                    <path
                      className={styles.treeTwig}
                      data-family={route.family}
                      d={`M 342 ${y} C 500 ${y}, 498 ${leafY}, 650 ${leafY}`}
                    />
                    <a
                      href={href}
                      aria-label={`${stationCode}: ${peer?.label || edge.label}; ${edge.label}; ${edge.direction}`}
                      {...externalProps(href)}
                    >
                      <circle className={styles.treeLeaf} data-family={route.family} cx="650" cy={leafY} r="7" />
                      <text className={styles.treeLeafLabel} x="672" y={leafY - 3}>{stationCode} · {shortLabel(peer?.label || edge.label, 48)}</text>
                      <text className={styles.treeLeafMeta} x="672" y={leafY + 14}>{edge.direction} · {edge.label.replaceAll("_", " ")}</text>
                    </a>
                  </g>
                );
              })}
            </g>
          ))}
          <circle className={styles.treeRoot} cx="124" cy={rootY} r="25" />
          <circle className={styles.treeRootInner} cx="124" cy={rootY} r="9" />
          <text className={styles.treeRootLabel} x="74" y={rootY + 48}>OBJECT ROOT</text>
        </svg>
      </div>

      <p className={styles.mobileDiagramNote}>
        On small screens the branch index below replaces the full tree drawing.
      </p>
      <StationIndex graph={graph} groups={groups} nodes={nodes} />
    </section>
  );
}

function StationIndex({
  graph,
  groups,
  nodes,
}: {
  graph: TraceGraph;
  groups: Map<VisualRoute["family"], TraceEdge[]>;
  nodes: Map<string, TraceNode>;
}) {
  return (
    <div className={styles.stationIndex} aria-label="Evidence station index">
      {VISUAL_ROUTES.map((route) => (
        <section key={route.family} data-family={route.family}>
          <h4><span>{route.code}</span>{route.label}</h4>
          {(groups.get(route.family) ?? []).length ? (
            <ol>
              {(groups.get(route.family) ?? []).map((edge, index) => {
                const peer = peerNode(edge, graph.object.nodeId, nodes);
                const href = stationHref(edge, peer);
                return (
                  <li key={edge.id}>
                    <b>{route.code}{index + 1}</b>
                    <span>
                      <a href={href} {...externalProps(href)}>{peer?.label || edge.label}</a>
                      <small>{edge.direction} · {edge.label.replaceAll("_", " ")} · {edge.reviewState.replaceAll("_", " ")}</small>
                    </span>
                  </li>
                );
              })}
            </ol>
          ) : <p>No station in this family.</p>}
        </section>
      ))}
    </div>
  );
}

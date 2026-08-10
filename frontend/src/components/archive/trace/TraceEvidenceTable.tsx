"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import styles from "./TraceExplorer.module.css";
import {
  TRACE_FAMILY_META,
  buildTraceMarks,
  selectionForEdge,
  tracePeerNode,
  traceTypeFor,
  type TraceSelection,
} from "./trace-taxonomy";
import type { RelationFamily, TraceGraph } from "./trace-types";

function externalProps(href: string) {
  return href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {};
}

export default function TraceEvidenceTable({
  graph,
  selection,
  onSelect,
}: {
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const [family, setFamily] = useState<RelationFamily | "all">("all");
  const [relation, setRelation] = useState("all");
  const nodes = useMemo(
    () => new Map(graph.nodes.map((node) => [node.id, node])),
    [graph.nodes],
  );
  const marks = useMemo(() => buildTraceMarks(graph), [graph]);
  const relationOptions = useMemo(
    () => Array.from(new Set(
      graph.edges
        .filter((edge) => family === "all" || edge.family === family)
        .map((edge) => edge.label),
    )).sort(),
    [family, graph.edges],
  );
  const rows = useMemo(
    () => graph.edges.filter((edge) =>
      (family === "all" || edge.family === family)
      && (relation === "all" || edge.label === relation)),
    [family, graph.edges, relation],
  );
  const selectedEdge = graph.edges.find((edge) => edge.id === selection?.edgeId);
  const selectedNode = selectedEdge
    ? tracePeerNode(selectedEdge, graph.object.nodeId, nodes)
    : undefined;

  return (
    <section className={styles.evidenceLedger} aria-labelledby="trace-evidence-ledger-title">
      <div className={styles.ledgerHeading}>
        <div>
          <p>TRACE LEDGER / NORMALIZED</p>
          <h3 id="trace-evidence-ledger-title">Nodes and edges</h3>
        </div>
        <dl aria-label="Local TRACE counts">
          <div><dt>Nodes</dt><dd>{graph.nodes.length}</dd></div>
          <div><dt>Edges</dt><dd>{graph.edges.length}</dd></div>
          <div><dt>Selected</dt><dd>{selection ? "1" : "0"}</dd></div>
        </dl>
      </div>

      <div className={styles.ledgerFilters}>
        <label>
          Family
          <select
            value={family}
            onChange={(event) => {
              setFamily(event.target.value as RelationFamily | "all");
              setRelation("all");
            }}
          >
            <option value="all">All families</option>
            {Object.entries(TRACE_FAMILY_META).map(([value, meta]) => (
              <option key={value} value={value}>{meta.code} · {meta.label}</option>
            ))}
          </select>
        </label>
        <label>
          Type
          <select value={relation} onChange={(event) => setRelation(event.target.value)}>
            <option value="all">All normalized types</option>
            {relationOptions.map((value) => {
              const definition = traceTypeFor(value);
              return <option key={value} value={value}>{definition.code} · {definition.label}</option>;
            })}
          </select>
        </label>
      </div>

      {selectedEdge ? (
        <div className={styles.ledgerSelection} aria-live="polite">
          <b>{marks.edgeMarks.get(selectedEdge.id)}</b>
          <span>
            <strong>{traceTypeFor(selectedEdge.label).label}</strong>
            <small>
              {marks.nodeMarks.get(selectedNode?.id ?? selectedEdge.object)} · {selectedNode?.label ?? "Evidence node"}
            </small>
          </span>
          <Link href={`/trace/types/${selectedEdge.label}`}>Type definition</Link>
        </div>
      ) : (
        <p className={styles.ledgerHint}>Select an edge mark to wake this evidence detail.</p>
      )}

      <ol className={styles.mobileLedgerList} aria-label={`Normalized TRACE edges for ${graph.object.title}`}>
        {rows.map((edge) => {
          const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
          const definition = traceTypeFor(edge.label);
          const rowSelection = selectionForEdge(graph, edge);
          const selected = selection?.edgeId === edge.id;
          const evidenceHref = edge.evidenceUrl || peer?.href || graph.object.evidenceReturnUrl;
          return (
            <li key={`mobile-${edge.id}`} data-selected={selected}>
              <button
                type="button"
                className={styles.traceMarkButton}
                aria-pressed={selected}
                aria-label={`Select ${definition.label} evidence edge`}
                onClick={() => onSelect(rowSelection)}
              >
                {marks.edgeMarks.get(edge.id)}
              </button>
              <div>
                <strong>{definition.label}</strong>
                <span>{marks.nodeMarks.get(rowSelection.nodeId)} · {peer?.label ?? "Evidence node"}</span>
              </div>
              <dl>
                <div><dt>Direction</dt><dd>{edge.direction}</dd></div>
                <div><dt>State</dt><dd>{edge.reviewState.replaceAll("_", " ")}</dd></div>
                <div><dt>Confidence</dt><dd>{edge.confidence.replaceAll("_", " ")}</dd></div>
              </dl>
              <div className={styles.mobileLedgerLinks}>
                <Link href={`/trace/types/${edge.label}`}>Type definition</Link>
                <a href={evidenceHref} {...externalProps(evidenceHref)}>{edge.evidenceField || "Source evidence"}</a>
              </div>
            </li>
          );
        })}
      </ol>

      <div className={styles.ledgerTableWrap}>
        <table className={styles.ledgerTable}>
          <caption>Normalized, selectable TRACE edges for {graph.object.title}</caption>
          <thead>
            <tr>
              <th scope="col">Edge</th>
              <th scope="col">Node</th>
              <th scope="col">Normalized type</th>
              <th scope="col">Direction</th>
              <th scope="col">Evidence state</th>
              <th scope="col">Return</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((edge) => {
              const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
              const definition = traceTypeFor(edge.label);
              const rowSelection = selectionForEdge(graph, edge);
              const selected = selection?.edgeId === edge.id;
              const evidenceHref = edge.evidenceUrl || peer?.href || graph.object.evidenceReturnUrl;
              return (
                <tr key={edge.id} data-selected={selected}>
                  <td>
                    <button
                      type="button"
                      className={styles.traceMarkButton}
                      aria-pressed={selected}
                      onClick={() => onSelect(rowSelection)}
                    >
                      {marks.edgeMarks.get(edge.id)}
                    </button>
                  </td>
                  <td>
                    <b>{marks.nodeMarks.get(rowSelection.nodeId)}</b>
                    <span>{peer?.label ?? "Evidence node"}</span>
                  </td>
                  <td>
                    <Link href={`/trace/types/${edge.label}`}>{definition.code}</Link>
                    <span>{definition.label}</span>
                  </td>
                  <td>{edge.direction}</td>
                  <td>
                    <span>{edge.reviewState.replaceAll("_", " ")}</span>
                    <small>{edge.confidence.replaceAll("_", " ")}</small>
                  </td>
                  <td>
                    <a href={evidenceHref} {...externalProps(evidenceHref)}>
                      {edge.evidenceField || "Source evidence"}
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className={styles.ledgerBoundary}>
        Marks identify local display nodes and edges. Their codes do not alter frozen IDs or create new historical relations.
      </p>
    </section>
  );
}

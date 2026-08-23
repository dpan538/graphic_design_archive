import { useMemo } from "react";
import type { TraceContextDataset } from "../types";
import { contextCanvasEntityId, type ContextCanvasConnection, type ContextCanvasSelection } from "./types";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasInspectorProps {
  readonly dataset: TraceContextDataset;
  readonly selection: ContextCanvasSelection;
  readonly connections: readonly ContextCanvasConnection[];
  readonly collapsed: boolean;
  readonly onToggleCollapsed: () => void;
  readonly onClose: () => void;
  readonly onHideEntity: (entityId: string) => void;
}

function refLabel(ref: Readonly<{ stableId: string; label?: string }>): string {
  return ref.label?.trim() || ref.stableId;
}

export function ContextCanvasInspector({
  dataset,
  selection,
  connections,
  collapsed,
  onToggleCollapsed,
  onClose,
  onHideEntity,
}: ContextCanvasInspectorProps) {
  const refs = useMemo(
    () => new Map(dataset.items.map((ref) => [contextCanvasEntityId(ref), ref])),
    [dataset],
  );
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const selectedRef = selection?.kind === "node" ? refs.get(selection.id) : undefined;
  const selectedConnection = selection?.kind === "connection"
    ? connections.find((item) => item.id === selection.id)
    : undefined;

  return (
    <aside className={`${styles.inspector} ${collapsed ? styles.panelCollapsed : ""}`} aria-label="Context Canvas inspector">
      <div className={styles.panelHeader}>
        <div>
          <h2>Inspector</h2>
          {!collapsed ? <p>{selection ? "One item selected" : "No selection"}</p> : null}
        </div>
        <div className={styles.panelHeaderActions}>
          {selection ? (
            <button type="button" className={styles.compactButton} onClick={onClose} aria-label="Close inspector selection">Close</button>
          ) : null}
          <button
            type="button"
            className={styles.compactButton}
            aria-expanded={!collapsed}
            aria-controls="context-canvas-inspector-content"
            onClick={onToggleCollapsed}
          >
            {collapsed ? "Expand inspector" : "Collapse inspector"}
          </button>
        </div>
      </div>
      {!collapsed ? (
        <div id="context-canvas-inspector-content" className={styles.inspectorContent}>
          {!selection ? (
            <p className={styles.emptyState}>Select an entity or connection to inspect its verified fields.</p>
          ) : selectedRef && selection.kind === "node" ? (
            <>
              <h3>{refLabel(selectedRef)}</h3>
              <dl className={styles.inspectorFields}>
                <div><dt>Kind</dt><dd>{selectedRef.kind}</dd></div>
                <div><dt>Stable public reference</dt><dd>{selectedRef.stableId}</dd></div>
                <div><dt>Availability</dt><dd>{dataset.availability.state}</dd></div>
                <div><dt>Canvas status</dt><dd>{selection.id === rootId ? "visible · selected root" : "visible"}</dd></div>
              </dl>
              {selection.id !== rootId ? (
                <button type="button" className={styles.removeButton} onClick={() => onHideEntity(selection.id)}>
                  Remove from canvas
                </button>
              ) : (
                <p className={styles.helpText}>The selected root object remains on the canvas.</p>
              )}
            </>
          ) : selectedConnection ? (
            <ConnectionInspector connection={selectedConnection} />
          ) : (
            <p className={styles.emptyState}>The selected item is no longer visible.</p>
          )}
        </div>
      ) : null}
    </aside>
  );
}

function ConnectionInspector({ connection }: { readonly connection: ContextCanvasConnection }) {
  switch (connection.connectionKind) {
    case "controlled_assignment":
      return (
        <>
          <h3>Controlled assignment</h3>
          <dl className={styles.inspectorFields}>
            <div><dt>connectionKind</dt><dd>{connection.connectionKind}</dd></div>
            <div><dt>assignmentType</dt><dd>{connection.assignment.assignmentType}</dd></div>
            <div><dt>state</dt><dd>{connection.assignment.state}</dd></div>
            <div><dt>subject</dt><dd>{refLabel(connection.assignment.subject)}</dd></div>
            <div><dt>value</dt><dd>{refLabel(connection.assignment.value)}</dd></div>
          </dl>
        </>
      );
    case "curated_membership":
      return (
        <>
          <h3>Curated membership</h3>
          <dl className={styles.inspectorFields}>
            <div><dt>connectionKind</dt><dd>{connection.connectionKind}</dd></div>
            <div><dt>membershipType</dt><dd>{connection.membership.membershipType}</dd></div>
            <div><dt>state</dt><dd>{connection.membership.state}</dd></div>
            <div><dt>member</dt><dd>{refLabel(connection.membership.member)}</dd></div>
            <div><dt>container</dt><dd>{refLabel(connection.membership.container)}</dd></div>
          </dl>
        </>
      );
    case "semantic_edge":
      return (
        <>
          <h3>Synthetic semantic edge</h3>
          <dl className={styles.inspectorFields}>
            <div><dt>connectionKind</dt><dd>{connection.connectionKind}</dd></div>
            <div><dt>predicateId</dt><dd>{connection.semanticEdge.predicateId}</dd></div>
            <div><dt>status</dt><dd>{connection.semanticEdge.status}</dd></div>
            <div><dt>evidence-reference count</dt><dd>{connection.semanticEdge.evidenceRefs.length}</dd></div>
          </dl>
        </>
      );
  }
}

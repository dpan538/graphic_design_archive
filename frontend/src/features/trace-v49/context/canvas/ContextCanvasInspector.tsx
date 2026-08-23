import { useMemo } from "react";
import type { TraceContextDataset } from "../types";
import {
  contextCanvasEntityRefsForMode,
  contextCanvasRepresentationByEntityId,
  getGovernedContextMetadata,
} from "./model";
import {
  contextCanvasEntityId,
  type ContextCanvasConnection,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasGovernedRepresentation,
  type ContextCanvasSelection,
} from "./types";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasInspectorProps {
  readonly dataset: TraceContextDataset;
  readonly dataMode: ContextCanvasDataMode;
  readonly metadata: ContextCanvasDataMetadata;
  readonly selection: ContextCanvasSelection;
  readonly connections: readonly ContextCanvasConnection[];
  readonly collapsed: boolean;
  readonly onToggleCollapsed: () => void;
  readonly onClose: () => void;
  readonly onHideEntity: (entityId: string) => void;
}

function refLabel(ref: Readonly<{ stableId: string; label?: string }>): string {
  return ref.label && ref.label.trim() ? ref.label : ref.stableId;
}

export function ContextCanvasInspector({
  dataset,
  dataMode,
  metadata,
  selection,
  connections,
  collapsed,
  onToggleCollapsed,
  onClose,
  onHideEntity,
}: ContextCanvasInspectorProps) {
  const refs = useMemo(
    () => new Map(
      contextCanvasEntityRefsForMode(dataset, dataMode, metadata)
        .map((ref) => [contextCanvasEntityId(ref), ref]),
    ),
    [dataMode, dataset, metadata],
  );
  const representationByEntityId = useMemo(
    () => contextCanvasRepresentationByEntityId(dataMode, metadata),
    [dataMode, metadata],
  );
  const governed = getGovernedContextMetadata(dataMode, metadata);
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const selectedRef = selection?.kind === "node" ? refs.get(selection.id) : undefined;
  const selectedConnection = selection?.kind === "connection"
    ? connections.find((item) => item.id === selection.id)
    : undefined;
  const selectedRefIsRoot = selection?.kind === "node" && selection.id === rootId;
  const selectedRepresentation = selection?.kind === "node"
    ? representationByEntityId.get(selection.id)
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
          ) : selectedRef && selection.kind === "node" && selectedRepresentation ? (
            <>
              <RepresentationInspector representation={selectedRepresentation} />
              <button type="button" className={styles.removeButton} onClick={() => onHideEntity(selection.id)}>
                Remove from canvas
              </button>
            </>
          ) : selectedRef && selection.kind === "node" ? (
            <>
              <h3>{refLabel(selectedRef)}</h3>
              <dl className={styles.inspectorFields}>
                <div><dt>Kind</dt><dd>{selectedRef.kind}</dd></div>
                <div>
                  <dt>{selectedRefIsRoot ? "Stable public reference" : "Validation-only identifier"}</dt>
                  <dd>{selectedRef.stableId}</dd>
                </div>
                <div><dt>Availability</dt><dd>{dataset.availability.state}</dd></div>
                <div><dt>Canvas status</dt><dd>{selectedRefIsRoot ? "visible · selected root" : "visible"}</dd></div>
                {selectedRefIsRoot && governed?.rootMetadata ? (
                  <>
                    <div><dt>Source-reported attribution</dt><dd>{governed.rootMetadata.creatorAttribution}</dd></div>
                    <div><dt>Source-reported object type</dt><dd>{governed.rootMetadata.objectType}</dd></div>
                    <div><dt>Source-reported date</dt><dd>{governed.rootMetadata.dateDisplay}</dd></div>
                    <div><dt>Source name</dt><dd>{governed.rootMetadata.sourceName}</dd></div>
                  </>
                ) : null}
              </dl>
              {!selectedRefIsRoot ? (
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
    case "context_representation":
      return <RepresentationInspector representation={connection.representation} />;
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

function RepresentationInspector({
  representation,
}: Readonly<{ representation: ContextCanvasGovernedRepresentation }>) {
  return (
    <>
      <h3>{representation.label}</h3>
      <dl className={styles.inspectorFields}>
        <div><dt>Context type</dt><dd>{representation.explanation.publicName}</dd></div>
        <div><dt>Full label</dt><dd>{representation.label}</dd></div>
        <div><dt>Meaning</dt><dd>{representation.explanation.longDefinition}</dd></div>
        <div><dt>Why shown</dt><dd>{representation.explanation.whyShown}</dd></div>
        <div><dt>Epistemic role</dt><dd>{representation.epistemicRole}</dd></div>
        <div><dt>Source basis</dt><dd>{representation.explanation.sourceBasis}</dd></div>
        <div><dt>Source state</dt><dd>{representation.provenance.sourceState}</dd></div>
        <div><dt>Governance decision</dt><dd>{representation.provenance.decision}</dd></div>
        <div><dt>Context publication</dt><dd>{representation.publicationState}</dd></div>
        <div><dt>Permitted interpretation</dt><dd>{representation.explanation.permittedInterpretation}</dd></div>
        <div>
          <dt>Prohibited interpretations</dt>
          <dd>
            <ul className={styles.inspectorList}>
              {representation.explanation.prohibitedInterpretations.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </dd>
        </div>
        <div><dt>Explanation code</dt><dd>{representation.explanationCode}</dd></div>
        <div><dt>Public representation ID</dt><dd>{representation.representationId}</dd></div>
        <div><dt>Public term ID</dt><dd>{representation.termId}</dd></div>
        <div><dt>Public provenance ID</dt><dd>{representation.provenance.provenanceId}</dd></div>
        <div><dt>Mapping policy version</dt><dd>{representation.provenance.mappingPolicyVersion}</dd></div>
        <div><dt>Governance policy version</dt><dd>{representation.provenance.governancePolicyVersion}</dd></div>
      </dl>
    </>
  );
}

import type { ContextCanvasGovernedRepresentation } from "@/features/trace-v49/context/canvas/types";
import { shortRelease } from "../lib/presentation";
import {
  ADD,
  CONTEXT_ROLE,
  COPY_HASH,
  COPY_TECHNICAL,
  COVERAGE,
  INSPECTOR_IDLE,
  INSPECTOR_ROOT_NOTE,
  INSPECTOR_TITLE,
  INTEGRITY,
  OPEN_OBJECT,
  PROJECTION,
  RELEASE,
  REMOVE,
  SELECTED_OBJECT,
  SOURCE_BASIS,
  TECHNICAL,
  WHY_APPEARS,
  kindWord,
} from "../lib/content";
import styles from "./Inspector.module.css";

/* 04 — the inspector (§7g): five things and one fold. For a context: its
   dimension, its label, "Project-curated context", why it appears (the
   governed registry's one sentence), how many public records carry the
   same classification, and the source basis. Then "Technical
   provenance ▸": Release (short), Projection, Integrity (the checksum's
   first eight characters, "Copy full"), and "Copy technical provenance"
   for everything the contract records — manifest, policy versions,
   identifiers, the reading rules — traceable, never displayed. The
   interpretation boundary stands once, on the canvas. The inspector is
   present only while open; it opens itself when a context is selected. */

export interface DatasetProvenance {
  readonly releaseId: string;
  readonly manifestSha256: string;
  readonly projectionId: string;
  readonly projectionSha256: string;
  readonly policyVersion: string;
  readonly explanationRegistryVersion: string;
}

export interface RootDetail {
  readonly title: string;
  readonly stableId: string;
  readonly creatorAttribution?: string;
  readonly objectType?: string;
  readonly dateDisplay?: string;
  readonly sourceName?: string;
}

export type InspectorSelection =
  | Readonly<{ kind: "none" }>
  | Readonly<{ kind: "root" }>
  | Readonly<{
    kind: "representation";
    representation: ContextCanvasGovernedRepresentation;
    entityId: string;
    visible: boolean;
    coverage: number | null;
  }>;

export interface InspectorProps {
  readonly selection: InspectorSelection;
  readonly root: RootDetail;
  readonly provenance: DatasetProvenance;
  readonly cohort: number;
  readonly locked: boolean;
  readonly onAdd: (entityId: string) => void;
  readonly onRemove: (entityId: string) => void;
  readonly onCopy: (text: string, note: string) => void;
  readonly copiedHashNote: string;
  readonly copiedTechnicalNote: string;
}

const fmt = (n: number) => n.toLocaleString("en-US");
const shortHash = (sha: string) => (sha.length > 8 ? `${sha.slice(0, 8)}…` : sha);

function Field({ label, value, mono = false }: Readonly<{ label: string; value: string | undefined; mono?: boolean }>) {
  if (!value || !value.trim()) return null;
  return (
    <div className={styles.field}>
      <dt>{label}</dt>
      <dd className={mono ? `${styles.mono} tnum` : undefined}>{value}</dd>
    </div>
  );
}

export function technicalText(provenance: DatasetProvenance, representation?: ContextCanvasGovernedRepresentation): string {
  const lines = [
    `Research release: ${provenance.releaseId}`,
    `Research manifest: ${provenance.manifestSha256}`,
    `Context projection: ${provenance.projectionId}`,
    `Projection hash: ${provenance.projectionSha256}`,
    `Governance policy: ${provenance.policyVersion}`,
    `Explanation registry: ${provenance.explanationRegistryVersion}`,
  ];
  if (representation) {
    lines.push(
      `Representation: ${representation.representationId}`,
      `Term: ${representation.termId}`,
      `Provenance: ${representation.provenance.provenanceId}`,
      `Explanation code: ${representation.explanationCode}`,
      `Mapping policy: ${representation.provenance.mappingPolicyVersion}`,
      `Source state: ${representation.provenance.sourceState}`,
      `Governance decision: ${representation.provenance.decision}`,
      `Publication: ${representation.publicationState}`,
      `Permitted reading: ${representation.explanation.permittedInterpretation}`,
      ...representation.explanation.prohibitedInterpretations.map((value) => `Not established: ${value}`),
    );
  }
  return `${lines.join("\n")}\n`;
}

function Technical({
  provenance,
  representation,
  onCopy,
  copiedHashNote,
  copiedTechnicalNote,
}: Readonly<{
  provenance: DatasetProvenance;
  representation?: ContextCanvasGovernedRepresentation;
  onCopy: InspectorProps["onCopy"];
  copiedHashNote: string;
  copiedTechnicalNote: string;
}>) {
  return (
    <details className={styles.fold}>
      <summary>{TECHNICAL}</summary>
      <dl className={styles.fields}>
        <Field label={RELEASE} value={shortRelease(provenance.releaseId)} mono />
        <Field label={PROJECTION} value={provenance.projectionId} mono />
        <div className={styles.field}>
          <dt>{INTEGRITY}</dt>
          <dd className={`${styles.mono} tnum`}>
            {shortHash(provenance.projectionSha256)}
            <button type="button" className={styles.small} onClick={() => onCopy(provenance.projectionSha256, copiedHashNote)}>
              {COPY_HASH}
            </button>
          </dd>
        </div>
      </dl>
      <p className={styles.actions}>
        <button type="button" className={styles.small} onClick={() => onCopy(technicalText(provenance, representation), copiedTechnicalNote)}>
          {COPY_TECHNICAL}
        </button>
      </p>
    </details>
  );
}

export default function Inspector({
  selection,
  root,
  provenance,
  cohort,
  locked,
  onAdd,
  onRemove,
  onCopy,
  copiedHashNote,
  copiedTechnicalNote,
}: InspectorProps) {
  const technical = (representation?: ContextCanvasGovernedRepresentation) => (
    <Technical
      provenance={provenance}
      representation={representation}
      onCopy={onCopy}
      copiedHashNote={copiedHashNote}
      copiedTechnicalNote={copiedTechnicalNote}
    />
  );
  return (
    <aside id="context-panel" className={styles.inspector} aria-labelledby="context-inspector-heading" aria-live="polite">
      <h2 id="context-inspector-heading" className={styles.label}>{INSPECTOR_TITLE}</h2>

      {selection.kind === "none" ? (
        <div className={styles.body}>
          <p className={styles.idle}>{INSPECTOR_IDLE}</p>
          {technical()}
        </div>
      ) : selection.kind === "root" ? (
        <div className={styles.body}>
          <p className={styles.kicker}>
            <span className={styles.dot} data-kind="object" aria-hidden="true" />
            {SELECTED_OBJECT}
          </p>
          <h3 className={styles.name}>{root.title.trim() || root.stableId}</h3>
          <p className={styles.note}>{INSPECTOR_ROOT_NOTE}</p>
          <dl className={styles.fields}>
            <Field label="Stable public ID" value={root.stableId} mono />
            <Field label="Attribution, as recorded" value={root.creatorAttribution} />
            <Field label="Object type, as recorded" value={root.objectType} />
            <Field label="Date, as recorded" value={root.dateDisplay} />
            <Field label="Source" value={root.sourceName} />
          </dl>
          <p className={styles.actions}>
            <a className={styles.link} href={`/surfaces/${encodeURIComponent(root.stableId)}`}>{OPEN_OBJECT} ↗</a>
          </p>
          {technical()}
        </div>
      ) : (
        <div className={styles.body} data-kind={selection.representation.kind}>
          <p className={styles.kicker}>
            <span className={styles.dot} data-kind={selection.representation.kind} aria-hidden="true" />
            {kindWord(selection.representation.kind)}
          </p>
          <h3 className={styles.name}>{selection.representation.label}</h3>
          <p className={styles.role}>{CONTEXT_ROLE}</p>

          <dl className={styles.fields}>
            <Field label={WHY_APPEARS} value={selection.representation.explanation.whyShown} />
            {selection.coverage !== null ? (
              <Field label="Coverage" value={COVERAGE(fmt(selection.coverage), fmt(cohort))} />
            ) : null}
            <Field label={SOURCE_BASIS} value={selection.representation.explanation.sourceBasis} />
          </dl>

          {technical(selection.representation)}

          <p className={styles.actions}>
            {selection.visible ? (
              <button type="button" className={styles.action} disabled={locked} onClick={() => onRemove(selection.entityId)}>
                {REMOVE}
              </button>
            ) : (
              <button type="button" className={styles.action} disabled={locked} onClick={() => onAdd(selection.entityId)}>
                {ADD}
              </button>
            )}
          </p>
        </div>
      )}
    </aside>
  );
}

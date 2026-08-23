import type { Metadata } from "next";
import ContextCanvas from "@/features/trace-v49/context/canvas/ContextCanvas";
import { adaptPublicContextDatasetForCanvas } from "@/features/trace-v49/context/governed/canvas";
import {
  getGovernedContextSampleOptions,
  lookupGovernedContextDataset,
} from "@/features/trace-v49/context/governed/index.server";
import styles from "./page.module.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Context Canvas governed-data workspace — TRACE v49",
  description: "Unlinked TRACE v49 Context Canvas workspace using the governed Context V1 read model.",
  robots: {
    index: false,
    follow: false,
  },
};

interface ContextCanvasPageProps {
  readonly searchParams: Promise<Readonly<{ record?: string | readonly string[] }>>;
}

type ParsedRecord =
  | Readonly<{ kind: "default" }>
  | Readonly<{ kind: "record"; stableId: string }>
  | Readonly<{ kind: "invalid" }>;

const PUBLIC_RECORD_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;

function parseRecordParameter(value: string | readonly string[] | undefined): ParsedRecord {
  if (value === undefined) return Object.freeze({ kind: "default" as const });
  if (
    Array.isArray(value)
    || typeof value !== "string"
    || value.length === 0
    || value.length > 80
    || !PUBLIC_RECORD_ID_PATTERN.test(value)
  ) return Object.freeze({ kind: "invalid" as const });
  return Object.freeze({ kind: "record" as const, stableId: value });
}

function RecordControls({
  activeStableId,
  samples,
}: Readonly<{
  activeStableId: string;
  samples: readonly Readonly<{ stableId: string; title: string }>[];
}>) {
  return (
    <section className={styles.recordControls} aria-label="Governed Context record controls">
      <div className={styles.recordControlHeading}>
        <strong>Governed Context record</strong>
        <span>Context V1 data/read model · unlinked visual workspace</span>
      </div>
      <form action="/trace/context-canvas" method="get" className={styles.recordForm}>
        <label htmlFor="context-canvas-record-id">Public stable ID</label>
        <input
          id="context-canvas-record-id"
          name="record"
          defaultValue={activeStableId}
          maxLength={80}
          pattern="SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*"
          autoComplete="off"
          spellCheck={false}
          placeholder="SURF-…"
        />
        <button type="submit">Load record</button>
      </form>
      {samples.length > 0 ? (
        <form action="/trace/context-canvas" method="get" className={styles.sampleForm}>
          <label htmlFor="context-canvas-sample-id">Deterministic public samples</label>
          <select id="context-canvas-sample-id" name="record" defaultValue={activeStableId}>
            {samples.map((sample) => (
              <option key={sample.stableId} value={sample.stableId}>
                {sample.title} · {sample.stableId}
              </option>
            ))}
          </select>
          <button type="submit">Load sample</button>
        </form>
      ) : null}
    </section>
  );
}

function LookupFailure({
  code,
  message,
}: Readonly<{ code: string; message: string }>) {
  return (
    <main className={styles.failureWorkspace}>
      <p className={styles.eyebrow}>TRACE v49 · fail-closed governed Context workspace</p>
      <h1>Context Canvas</h1>
      <p className={styles.failureCode}>{code}</p>
      <p>{message}</p>
      <p>No Canvas dataset was mounted and no local composition was read or persisted.</p>
    </main>
  );
}

export default async function ContextCanvasGovernedPage({
  searchParams,
}: ContextCanvasPageProps) {
  const query = await searchParams;
  const parsedRecord = parseRecordParameter(query.record);
  const samples = getGovernedContextSampleOptions();
  const defaultStableId = samples[0]?.stableId;

  if (parsedRecord.kind === "invalid" || !defaultStableId) {
    return (
      <div className={styles.pageShell}>
        <LookupFailure
          code={parsedRecord.kind === "invalid" ? "INVALID_RECORD_ID" : "INTEGRITY_FAILURE"}
          message={parsedRecord.kind === "invalid"
            ? "The record parameter is not a valid public stable ID."
            : "The governed Context projection has no available public sample."}
        />
      </div>
    );
  }

  const stableId = parsedRecord.kind === "record" ? parsedRecord.stableId : defaultStableId;
  const lookup = lookupGovernedContextDataset(stableId);
  if (!lookup.ok) {
    return (
      <div className={styles.pageShell}>
        <RecordControls activeStableId={stableId} samples={samples} />
        <LookupFailure code={lookup.code} message={lookup.message} />
      </div>
    );
  }

  const canvas = adaptPublicContextDatasetForCanvas(lookup.data);
  return (
    <div className={styles.pageShell}>
      <RecordControls
        activeStableId={lookup.data.selectedRecord.surfaceId}
        samples={samples}
      />
      <div className={styles.canvasHost}>
        <ContextCanvas
          dataset={canvas.dataset}
          dataMode={canvas.dataMode}
          metadata={canvas.metadata}
        />
      </div>
    </div>
  );
}

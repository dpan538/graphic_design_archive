import type { Metadata } from "next";
import ContextCanvas from "@/features/trace-v49/context/canvas/ContextCanvas";
import {
  CONTEXT_CANVAS_FIXTURE_METADATA,
  CONTEXT_CANVAS_SYNTHETIC_DATASET,
} from "@/features/trace-v49/context/canvas/fixture";
import type { ContextCanvasDataMetadata } from "@/features/trace-v49/context/canvas/types";
import {
  getRealContextValidationSampleOptions,
  lookupRealContextValidationDataset,
  realContextValidationEnabled,
  TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT,
} from "@/features/trace-v49/context/realdata/source-index.server";
import type {
  TraceContextValidationFailure,
  TraceContextValidationSampleOption,
} from "@/features/trace-v49/context/realdata/types";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Context Canvas validation workspace — TRACE v49",
  description: "Not-published TRACE v49 Context Canvas validation workspace.",
  robots: {
    index: false,
    follow: false,
  },
};

interface ContextCanvasPageProps {
  readonly searchParams: Promise<Readonly<{ record?: string | readonly string[] }>>;
}

type ParsedRecord =
  | Readonly<{ kind: "none" }>
  | Readonly<{ kind: "record"; stableId: string }>
  | Readonly<{ kind: "invalid" }>;

function parseRecordParameter(value: string | readonly string[] | undefined): ParsedRecord {
  if (value === undefined) return Object.freeze({ kind: "none" as const });
  if (Array.isArray(value) || typeof value !== "string" || value.length === 0 || value.length > 80) {
    return Object.freeze({ kind: "invalid" as const });
  }
  return Object.freeze({ kind: "record" as const, stableId: value });
}

function invalidRecordFailure(): TraceContextValidationFailure {
  return Object.freeze({
    status: "error" as const,
    code: "INVALID_RECORD_ID" as const,
    message: "The record parameter is not a valid public stable ID.",
  });
}

function safeSampleOptions(enabled: boolean): readonly TraceContextValidationSampleOption[] {
  if (!enabled) return Object.freeze([]);
  try {
    return getRealContextValidationSampleOptions();
  } catch {
    return Object.freeze([]);
  }
}

function RecordControls({
  activeStableId,
  validationEnabled,
  samples,
}: Readonly<{
  activeStableId?: string;
  validationEnabled: boolean;
  samples: readonly TraceContextValidationSampleOption[];
}>) {
  return (
    <section className={styles.recordControls} aria-label="Context validation record controls">
      <div className={styles.recordControlHeading}>
        <strong>Validation record</strong>
        <span>{validationEnabled ? "real-v49-validation gate active" : "synthetic default · real validation gate inactive"}</span>
      </div>
      <form action="/trace/context-canvas" method="get" className={styles.recordForm}>
        <label htmlFor="context-canvas-record-id">Public stable ID</label>
        <input
          id="context-canvas-record-id"
          name="record"
          defaultValue={activeStableId}
          maxLength={80}
          autoComplete="off"
          spellCheck={false}
          placeholder="SURF-…"
        />
        <button type="submit">Load record</button>
      </form>
      {samples.length > 0 ? (
        <form action="/trace/context-canvas" method="get" className={styles.sampleForm}>
          <label htmlFor="context-canvas-sample-id">Deterministic samples</label>
          <select id="context-canvas-sample-id" name="record" defaultValue={activeStableId || samples[0]?.stableId}>
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

function ValidationFailure({ failure }: Readonly<{ failure: TraceContextValidationFailure }>) {
  return (
    <main className={styles.failureWorkspace}>
      <p className={styles.eyebrow}>TRACE v49 · fail-closed validation workspace</p>
      <h1>Context Canvas</h1>
      <p className={styles.failureCode}>{failure.code}</p>
      <p>{failure.message}</p>
      <p>No Canvas dataset was mounted and no local composition was read or persisted.</p>
    </main>
  );
}

export default async function ContextCanvasValidationPage({
  searchParams,
}: ContextCanvasPageProps) {
  const query = await searchParams;
  const parsedRecord = parseRecordParameter(query.record);
  const validationEnabled = realContextValidationEnabled();
  const samples = safeSampleOptions(validationEnabled);

  if (!validationEnabled && parsedRecord.kind === "none") {
    return (
      <div className={styles.pageShell}>
        <RecordControls validationEnabled={false} samples={samples} />
        <div className={styles.canvasHost}>
          <ContextCanvas
            dataset={CONTEXT_CANVAS_SYNTHETIC_DATASET}
            dataMode="synthetic_contract"
            metadata={CONTEXT_CANVAS_FIXTURE_METADATA}
          />
        </div>
      </div>
    );
  }

  const lookup = parsedRecord.kind === "invalid"
    ? invalidRecordFailure()
    : lookupRealContextValidationDataset(
      parsedRecord.kind === "record" ? parsedRecord.stableId : undefined,
    );

  if (lookup.status === "error") {
    return (
      <div className={styles.pageShell}>
        <RecordControls
          activeStableId={parsedRecord.kind === "record" ? parsedRecord.stableId : undefined}
          validationEnabled={validationEnabled}
          samples={samples}
        />
        <ValidationFailure failure={lookup} />
      </div>
    );
  }

  const canvasMetadata: ContextCanvasDataMetadata = Object.freeze({
    dataLabel: "real v49 validation candidates",
    mappingVersion: lookup.projection.metadata.mappingVersion,
    candidateState: "not_published" as const,
    historicalEvidence: false as const,
    governedPublicRelease: false as const,
    publicReleaseData: false as const,
    publicObjectCohortCount: TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT,
  });

  return (
    <div className={styles.pageShell}>
      <RecordControls
        activeStableId={lookup.projection.dataset.selectedRecord.stableId}
        validationEnabled={validationEnabled}
        samples={samples}
      />
      <div className={styles.canvasHost}>
        <ContextCanvas
          dataset={lookup.projection.dataset}
          dataMode="real_v49_validation"
          metadata={canvasMetadata}
        />
      </div>
    </div>
  );
}

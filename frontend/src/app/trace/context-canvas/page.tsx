import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import SiteNav from "@/components/site/SiteNav";
import { isLikelyMobileTraceRequest, TraceDesktopRequired } from "@/features/trace-v49/mobile.server";
import contextManifest from "../../../../generated/trace-context-v1/manifest.json";
import { INVALID_RECORD_ID_MESSAGE, NAME, STATEMENT } from "./lib/content";

/* /trace/context-canvas — TRACE Function 1 (FRONTEND_DESIGN_DECISION.md §7g).
   Server route: the mobile guard first (the desktop-required notice
   before any research runtime is imported); without ?record= the page
   sends the reader to an object — the one opened most recently in this
   browser (a first-party cookie the canvas sets for thirty minutes), or
   else the LANDING record — so entering Context Canvas always opens a
   canvas; with ?record= the governed Context lookup for that public
   stable ID, adapted for the canvas and handed to the desktop tree. A failed
   lookup mounts nothing: the failure page keeps the requested ID for
   correction and offers the same request again. The projection's twelve
   deterministic samples are a QA tool: listed in development or with
   ?qa=1 only, never a reader's default.
   Development builds accept previews: ?state=empty (the valid empty
   state, which the v49 projection itself never produces), ?state=loading
   (the canvas held in its initialising state), and ?state=stress /
   ?state=stress-missing (the fixed synthetic stress fixture — layout
   testing only, banner-labelled, built on the real release identity and
   explanations). */

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Context Canvas — TRACE",
  description: `${NAME}: ${STATEMENT} Medium, theme and movement contexts from the sealed v49 research release.`,
  robots: { index: false, follow: false },
};

interface ContextCanvasPageProps {
  readonly searchParams: Promise<Readonly<{ record?: string | readonly string[]; state?: string | readonly string[]; qa?: string | readonly string[] }>>;
}

type ParsedRecord =
  | Readonly<{ kind: "default" }>
  | Readonly<{ kind: "record"; stableId: string }>
  | Readonly<{ kind: "invalid"; requested: string }>;

type Preview = "empty" | "loading" | "stress" | "stress-missing" | null;

const PUBLIC_RECORD_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
/* the object opened most recently in this browser: a first-party cookie
   the canvas sets and renews for thirty minutes (a public stable ID,
   nothing else) */
export const LAST_RECORD_COOKIE = "mgda-context-last";

function parseRecordParameter(value: string | readonly string[] | undefined): ParsedRecord {
  if (value === undefined) return Object.freeze({ kind: "default" as const });
  if (
    Array.isArray(value)
    || typeof value !== "string"
    || value.length === 0
    || value.length > 80
    || !PUBLIC_RECORD_ID_PATTERN.test(value)
  ) return Object.freeze({ kind: "invalid" as const, requested: typeof value === "string" ? value.slice(0, 80) : "" });
  return Object.freeze({ kind: "record" as const, stableId: value });
}

function parsePreview(value: string | readonly string[] | undefined): Preview {
  if (process.env.NODE_ENV === "production") return null;
  return value === "empty" || value === "loading" || value === "stress" || value === "stress-missing" ? value : null;
}

export default async function ContextCanvasPage({ searchParams }: ContextCanvasPageProps) {
  if (await isLikelyMobileTraceRequest()) {
    return (
      <>
        <SiteNav variant="mobile" active="trace" />
        <TraceDesktopRequired functionName={NAME} />
      </>
    );
  }
  const [
    { default: ContextDesktop },
    { default: ContextFailure },
    { adaptPublicContextDatasetForCanvas },
    contextIndex,
    { coverageForTermIds },
  ] = await Promise.all([
    import("./desktop/ContextDesktop"),
    import("./desktop/ContextFailure"),
    import("@/features/trace-v49/context/governed/canvas"),
    import("@/features/trace-v49/context/governed/index.server"),
    import("./lib/coverage.server"),
  ]);
  const {
    getGovernedContextExampleOptions,
    getGovernedContextLandingRecord,
    getGovernedContextSampleOptions,
    lookupGovernedContextDataset,
  } = contextIndex;
  const query = await searchParams;
  const parsed = parseRecordParameter(query.record);
  const preview = parsePreview(query.state);
  const examples = getGovernedContextExampleOptions();
  const landing = getGovernedContextLandingRecord();
  /* the QA samples: development, or ?qa=1 */
  const qaSamples = process.env.NODE_ENV !== "production" || query.qa === "1" ? getGovernedContextSampleOptions() : null;
  const cohort = contextManifest.counts.publicObjectCount.toLocaleString("en-US");

  if (parsed.kind === "invalid") {
    return (
      <ContextFailure
        code="INVALID_RECORD_ID"
        message={INVALID_RECORD_ID_MESSAGE}
        requestedId={parsed.requested}
        examples={examples}
        qaSamples={qaSamples}
        cohort={cohort}
        retryHref={null}
      />
    );
  }

  /* no object asked for: the one remembered (thirty minutes), or the
     landing record — always as its own ?record= address; a development
     preview needs no address and takes the landing record as its base */
  if (parsed.kind === "default" && preview === null) {
    const remembered = (await cookies()).get(LAST_RECORD_COOKIE)?.value ?? "";
    const target = PUBLIC_RECORD_ID_PATTERN.test(remembered) && lookupGovernedContextDataset(remembered).ok ? remembered : landing.stableId;
    redirect(`/trace/context-canvas?record=${encodeURIComponent(target)}`);
  }

  const stableId = parsed.kind === "record" ? parsed.stableId : landing.stableId;
  const lookup = lookupGovernedContextDataset(stableId);
  if (!lookup.ok) {
    return (
      <ContextFailure
        code={lookup.code}
        message={lookup.message}
        requestedId={stableId}
        examples={examples}
        qaSamples={qaSamples}
        cohort={cohort}
        retryHref={`/trace/context-canvas?record=${encodeURIComponent(stableId)}`}
      />
    );
  }

  if (preview === "stress" || preview === "stress-missing") {
    const { buildStressFixture, stressCoverage } = await import("./lib/stress-fixture.server");
    const fixture = buildStressFixture(lookup.data, preview === "stress" ? "full" : "missing");
    const themes = fixture.representations.filter((r) => r.kind === "theme");
    const canvas = adaptPublicContextDatasetForCanvas(fixture);
    return (
      <ContextDesktop
        dataset={canvas.dataset}
        dataMode={canvas.dataMode}
        metadata={canvas.metadata}
        examples={examples}
        qaSamples={qaSamples}
        coverage={stressCoverage(fixture)}
        cohort={contextManifest.counts.publicObjectCount}
        preview="stress"
        initialSetAsideTermIds={themes.slice(-1).map((r) => r.termId)}
        initialSelectTermId={themes[0]?.termId ?? null}
      />
    );
  }

  const publicDataset = preview === "empty"
    ? Object.freeze({
      ...lookup.data,
      availability: "empty" as const,
      representations: Object.freeze([]),
      counts: Object.freeze({ representations: 0, byKind: Object.freeze({ medium: 0, theme: 0, movementContext: 0 }) }),
      explanations: Object.freeze([]),
      accessibleRows: Object.freeze(lookup.data.accessibleRows.filter((row) => row.category === "selected_record")),
    })
    : lookup.data;
  const canvas = adaptPublicContextDatasetForCanvas(publicDataset);
  const coverage = coverageForTermIds(publicDataset.representations.map((r) => r.termId));
  /* an object opens with one representation of each dimension on the
     canvas and the rest left to add — the counts say so ("1/2 on
     canvas", "+ 1 available") — so every canvas shows every relation and
     the add is there to be found; previews open whole */
  const firstOfKind = new Set<string>();
  const initialSetAsideTermIds = preview === null
    ? publicDataset.representations.filter((r) => {
      if (firstOfKind.has(r.kind)) return true;
      firstOfKind.add(r.kind);
      return false;
    }).map((r) => r.termId)
    : undefined;

  return (
    <ContextDesktop
      dataset={canvas.dataset}
      dataMode={canvas.dataMode}
      metadata={canvas.metadata}
      examples={examples}
      qaSamples={qaSamples}
      coverage={coverage}
      cohort={contextManifest.counts.publicObjectCount}
      preview={preview === "empty" || preview === "loading" ? preview : null}
      initialSetAsideTermIds={initialSetAsideTermIds}
    />
  );
}

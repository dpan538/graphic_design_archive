"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  deriveNativePatternFillUrl,
  deriveSpacetimeRendererModel,
  spacetimeGeometryRuntimeCache,
  TRACE_NATIVE_COUNT_TIERS,
  TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
  type PreparedSpacetimeProjection,
  type PreparedSpacetimeRendererMark,
  type SpacetimeRendererMode,
} from "@/features/trace-v49/spacetime/gis";
import type {
  PublicSpacetimeAtlasDataset,
  PublicSpacetimePrecisionBreakdown,
  PublicSpacetimePeriodsDataset,
  PublicSpacetimeRecordPage,
  PublicSpacetimeRecordSummary,
} from "@/features/trace-v49/spacetime/governed/types";
import {
  applySpacetimeRecordPage,
  spacetimeAtlasResultMatches,
  SpacetimeRequestEpochGate,
  type SpacetimeRecordAccumulator,
} from "./request-epochs";
import styles from "./SpacetimeWorkspace.module.css";

const MAP_WIDTH = 1_200;
const MAP_HEIGHT = 640;
const MAP_PADDING = 28;
const RECORD_PAGE_SIZE = 25;
const FULL_MAP_VIEWBOX = `0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`;

type RequestState = "idle" | "loading" | "ready" | "error";

interface ReadApiEnvelope<T> {
  readonly apiVersion: "v1";
  readonly data: T;
}

function apiPath(
  releaseId: string,
  tail: string,
): string {
  return `/api/v1/releases/${encodeURIComponent(releaseId)}/trace/spacetime/${tail}`;
}

async function readApi<T>(
  input: string,
  manifestSha256: string,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(input, {
    method: "GET",
    cache: "no-store",
    headers: {
      "Archive-Research-Manifest-Sha256": manifestSha256,
    },
    signal,
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => null) as { detail?: unknown } | null;
    throw new Error(typeof problem?.detail === "string" ? problem.detail : `Request failed (${response.status})`);
  }
  const envelope = await response.json() as ReadApiEnvelope<T>;
  return envelope.data;
}

function deriveSelectionViewBox(
  atlas: PublicSpacetimeAtlasDataset,
  geometry: PreparedSpacetimeProjection,
  geographyId: string,
): string {
  const geography = atlas.mappedGeographies.find((candidate) => candidate.geographyId === geographyId);
  if (!geography) return FULL_MAP_VIEWBOX;
  const bounds = geography.geometryIds
    .map((geometryId) => geometry.boundsById.get(geometryId))
    .filter((value): value is readonly [readonly [number, number], readonly [number, number]] => Boolean(value));
  if (bounds.length === 0) return FULL_MAP_VIEWBOX;
  const minimumX = Math.min(...bounds.map((value) => value[0][0]));
  const minimumY = Math.min(...bounds.map((value) => value[0][1]));
  const maximumX = Math.max(...bounds.map((value) => value[1][0]));
  const maximumY = Math.max(...bounds.map((value) => value[1][1]));
  if (![minimumX, minimumY, maximumX, maximumY].every(Number.isFinite)) return FULL_MAP_VIEWBOX;
  const width = Math.max(120, maximumX - minimumX);
  const height = Math.max(90, maximumY - minimumY);
  const padding = Math.max(18, Math.min(width, height) * 0.18);
  return `${Number((minimumX - padding).toFixed(3))} ${Number((minimumY - padding).toFixed(3))} ${Number((width + padding * 2).toFixed(3))} ${Number((height + padding * 2).toFixed(3))}`;
}

function precisionSummary(
  value: PublicSpacetimePrecisionBreakdown,
): string {
  return [
    ["day", value.day],
    ["month", value.month],
    ["year", value.year],
    ["range", value.range],
    ["approximate", value.approximate],
    ["unknown", value.unknown],
  ].filter(([, count]) => Number(count) > 0)
    .map(([label, count]) => `${label} ${count}`)
    .join(", ");
}

function MapGraphic({
  atlas,
  geometry,
  marks,
  mode,
  viewBox,
  selectedGeographyId,
  onSelect,
}: Readonly<{
  atlas: PublicSpacetimeAtlasDataset;
  geometry: PreparedSpacetimeProjection;
  marks: readonly PreparedSpacetimeRendererMark[];
  mode: SpacetimeRendererMode;
  viewBox: string;
  selectedGeographyId: string | null;
  onSelect: (geographyId: string) => void;
}>) {
  const geographyByGeometryId = useMemo(() => {
    const result = new Map<string, string>();
    for (const item of atlas.mappedGeographies) {
      for (const geometryId of item.geometryIds) result.set(geometryId, item.geographyId);
    }
    return result;
  }, [atlas.mappedGeographies]);
  const patternByGeographyId = useMemo(
    () => new Map(marks.flatMap((mark) =>
      mark.pattern ? [[mark.geography.geographyId, mark.pattern] as const] : [])),
    [marks],
  );
  const patterns = useMemo(
    () => marks.flatMap((mark) => mark.pattern ? [mark.pattern] : []),
    [marks],
  );

  return (
    <svg
      className={styles.map}
      viewBox={viewBox}
      role="img"
      aria-labelledby="spacetime-map-title spacetime-map-description"
    >
      <title id="spacetime-map-title">Recorded geographic context for {atlas.selectedPeriod.label}</title>
      <desc id="spacetime-map-description">
        Aggregate map of records whose recorded temporal extent overlaps this period. Marks are derived layout positions, not object coordinates.
      </desc>
      {mode === "texture" ? (
        <defs>
          {patterns.map((pattern) => (
            <pattern
              key={pattern.id}
              id={pattern.id}
              patternUnits="userSpaceOnUse"
              width={pattern.width}
              height={pattern.height}
            >
              {pattern.primitive.kind === "circle" ? (
                <circle
                  cx={pattern.primitive.cx}
                  cy={pattern.primitive.cy}
                  r={pattern.primitive.radius}
                  className={styles.patternPrimitive}
                />
              ) : (
                <line
                  x1={pattern.primitive.x1}
                  y1={pattern.primitive.y1}
                  x2={pattern.primitive.x2}
                  y2={pattern.primitive.y2}
                  strokeWidth={pattern.primitive.strokeWidth}
                  className={styles.patternPrimitive}
                />
              )}
            </pattern>
          ))}
        </defs>
      ) : null}
      <g aria-hidden="true">
        {geometry.source.collection.features.map((feature) => {
          const geometryId = String(feature.id);
          const geographyId = geographyByGeometryId.get(geometryId);
          const selected = geographyId === selectedGeographyId;
          const pattern = geographyId ? patternByGeographyId.get(geographyId) : undefined;
          return (
            <path
              key={geometryId}
              d={geometry.pathById.get(geometryId) ?? ""}
              className={`${styles.land} ${geographyId ? styles.mappedLand : ""} ${selected ? styles.selectedLand : ""}`}
              style={mode === "texture" && pattern
                ? { fill: deriveNativePatternFillUrl(pattern) }
                : undefined}
              onClick={geographyId ? () => onSelect(geographyId) : undefined}
            />
          );
        })}
      </g>
      {mode !== "texture" ? (
        <g aria-hidden="true">
          {marks.map((mark) => (
            <g key={mark.geography.geographyId}>
              {mode === "density" && mark.density && mark.density.dots.length > 0
                ? mark.density.dots.map((dot) => (
                <circle
                  key={dot.id}
                  cx={dot.x}
                  cy={dot.y}
                  r={2.1}
                  className={mark.geography.geographyId === selectedGeographyId ? styles.selectedMark : styles.densityMark}
                  onClick={() => onSelect(mark.geography.geographyId)}
                />
                ))
                : null}
              {mode !== "density"
              || !mark.density
              || mark.density.dots.length === 0
              || mark.density.anchorRemainderCount > 0 ? (
                <circle
                  cx={mark.x}
                  cy={mark.y}
                  r={Math.max(4, Math.min(18, 3 + Math.sqrt(
                    mode === "density" && mark.density && mark.density.anchorRemainderCount > 0
                      ? mark.density.anchorRemainderCount
                      : mark.geography.recordCount,
                  ) * 0.75))}
                  className={mark.geography.geographyId === selectedGeographyId ? styles.selectedMark : styles.aggregateMark}
                  onClick={() => onSelect(mark.geography.geographyId)}
                />
              ) : null}
            </g>
          ))}
        </g>
      ) : null}
    </svg>
  );
}

function RecordList({
  state,
  records,
  page,
  onLoadMore,
}: Readonly<{
  state: RequestState;
  records: readonly PublicSpacetimeRecordSummary[];
  page: PublicSpacetimeRecordPage | null;
  onLoadMore: () => void;
}>) {
  if (state === "loading" && records.length === 0) return <p role="status">Loading matching public records…</p>;
  if (state === "error") return <p role="alert">The matching record page could not be loaded.</p>;
  if (!page) return <p>Select a geography from the accessible table or aggregate map.</p>;
  return (
    <>
      <p className={styles.listStatus}>{page.totalCount.toLocaleString()} matching public records</p>
      <ol className={styles.recordList}>
        {records.map((record) => (
          <li key={record.stableId}>
            <Link href={`/surfaces/${encodeURIComponent(record.stableId)}`}>{record.title}</Link>
            <span>{record.time.sourceDisplay} · {record.stableId}</span>
          </li>
        ))}
      </ol>
      {page.pageInfo.hasNextPage ? (
        <button type="button" onClick={onLoadMore} disabled={state === "loading"}>
          {state === "loading" ? "Loading…" : "Load more records"}
        </button>
      ) : null}
    </>
  );
}

export default function SpacetimeWorkspace({
  periods,
  initialAtlas,
}: Readonly<{
  periods: PublicSpacetimePeriodsDataset;
  initialAtlas: PublicSpacetimeAtlasDataset;
}>) {
  const [atlas, setAtlas] = useState(initialAtlas);
  const [selectedPeriodId, setSelectedPeriodId] = useState(initialAtlas.selectedPeriod.periodId);
  const [selectedGeographyId, setSelectedGeographyId] = useState<string | null>(null);
  const [mode, setMode] = useState<SpacetimeRendererMode>("aggregate");
  const [viewBox, setViewBox] = useState(FULL_MAP_VIEWBOX);
  const [geometry, setGeometry] = useState<PreparedSpacetimeProjection | null>(null);
  const [geometryState, setGeometryState] = useState<RequestState>("loading");
  const [atlasState, setAtlasState] = useState<RequestState>("ready");
  const [recordsState, setRecordsState] = useState<RequestState>("idle");
  const [recordAccumulator, setRecordAccumulator] = useState<SpacetimeRecordAccumulator | null>(null);
  const atlasRef = useRef(initialAtlas);
  const recordAccumulatorRef = useRef<SpacetimeRecordAccumulator | null>(null);
  const selectedPeriodIdRef = useRef(initialAtlas.selectedPeriod.periodId);
  const requestGateRef = useRef(new SpacetimeRequestEpochGate());

  const releaseId = periods.release.researchReleaseId;
  const manifestSha256 = periods.release.researchManifestSha256;
  const spacetimeProjectionSha256 = periods.release.spacetimeProjectionSha256;

  const clearRecords = useCallback((state: RequestState = "idle") => {
    recordAccumulatorRef.current = null;
    setRecordAccumulator(null);
    setRecordsState(state);
  }, []);

  useEffect(() => {
    let active = true;
    setGeometry(null);
    setGeometryState("loading");
    void spacetimeGeometryRuntimeCache.loadSource(periods.geometry)
      .then((source) => {
        const prepared = spacetimeGeometryRuntimeCache.prepareProjection(source, {
          projectionId: "equal-earth",
          viewport: Object.freeze({
            width: MAP_WIDTH,
            height: MAP_HEIGHT,
            padding: MAP_PADDING,
          }),
        });
        if (!active) return;
        setGeometry(prepared);
        setGeometryState("ready");
      })
      .catch(() => {
        if (active) setGeometryState("error");
      });
    return () => {
      active = false;
    };
  }, [
    periods.geometry.assetPath,
    periods.geometry.assetSha256,
    periods.geometry.featureCount,
    periods.geometry.geometryArtifactId,
  ]);

  const selectPeriod = useCallback((periodId: string) => {
    if (periodId === selectedPeriodIdRef.current) return;
    selectedPeriodIdRef.current = periodId;
    requestGateRef.current.abort("records");
    setSelectedGeographyId(null);
    setViewBox(FULL_MAP_VIEWBOX);
    clearRecords();
    setSelectedPeriodId(periodId);
    if (periodId === atlasRef.current.selectedPeriod.periodId) {
      requestGateRef.current.abort("atlas");
      setAtlasState("ready");
      return;
    }
    const ticket = requestGateRef.current.begin("atlas");
    const identity = Object.freeze({ spacetimeProjectionSha256, periodId });
    setAtlasState("loading");
    void readApi<PublicSpacetimeAtlasDataset>(
      `${apiPath(releaseId, "atlas")}?period=${encodeURIComponent(periodId)}`,
      manifestSha256,
      ticket.signal,
    ).then((nextAtlas) => {
      if (!ticket.isCurrent()) return;
      if (!spacetimeAtlasResultMatches(identity, nextAtlas)) {
        selectedPeriodIdRef.current = atlasRef.current.selectedPeriod.periodId;
        setSelectedPeriodId(atlasRef.current.selectedPeriod.periodId);
        setAtlasState("error");
        return;
      }
      atlasRef.current = nextAtlas;
      setAtlas(nextAtlas);
      setAtlasState("ready");
    }).catch(() => {
      if (!ticket.isCurrent()) return;
      selectedPeriodIdRef.current = atlasRef.current.selectedPeriod.periodId;
      setSelectedPeriodId(atlasRef.current.selectedPeriod.periodId);
      setAtlasState("error");
    });
  }, [
    clearRecords,
    manifestSha256,
    releaseId,
    spacetimeProjectionSha256,
  ]);

  useEffect(() => () => {
    requestGateRef.current.abortAll();
  }, []);

  const loadRecordPage = useCallback((after?: string) => {
    if (!selectedGeographyId) return;
    const ticket = requestGateRef.current.begin("records");
    const identity = Object.freeze({
      spacetimeProjectionSha256,
      periodId: selectedPeriodId,
      geographyId: selectedGeographyId,
      after: after ?? null,
    });
    setRecordsState("loading");
    const query = new URLSearchParams({
      period: identity.periodId,
      first: String(RECORD_PAGE_SIZE),
    });
    if (identity.after) query.set("after", identity.after);
    void readApi<PublicSpacetimeRecordPage>(
      `${apiPath(releaseId, `geographies/${encodeURIComponent(identity.geographyId)}/records`)}?${query}`,
      manifestSha256,
      ticket.signal,
    ).then((page) => {
      if (!ticket.isCurrent()) return;
      try {
        const next = applySpacetimeRecordPage(recordAccumulatorRef.current, identity, page);
        recordAccumulatorRef.current = next;
        setRecordAccumulator(next);
        setRecordsState("ready");
      } catch {
        setRecordsState("error");
      }
    }).catch(() => {
      if (ticket.isCurrent()) setRecordsState("error");
    });
  }, [
    manifestSha256,
    releaseId,
    selectedGeographyId,
    selectedPeriodId,
    spacetimeProjectionSha256,
  ]);

  useEffect(() => {
    if (!selectedGeographyId) {
      clearRecords();
      return;
    }
    loadRecordPage();
  }, [clearRecords, loadRecordPage, selectedGeographyId]);

  const renderer = useMemo(
    () => geometry
      ? deriveSpacetimeRendererModel({
          atlas,
          projection: geometry,
          mode,
          selectedGeographyId,
        })
      : null,
    [atlas, geometry, mode, selectedGeographyId],
  );
  const marks = renderer?.marks ?? Object.freeze([]);
  const recordPage = recordAccumulator?.page ?? null;
  const records = recordAccumulator?.records ?? Object.freeze([]);
  const selectedIndex = periods.periods.findIndex((period) => period.periodId === selectedPeriodId);
  const selectedGeography = atlas.accessibleRows.find((row) => row.geographyId === selectedGeographyId) ?? null;
  const selectGeography = useCallback((geographyId: string) => {
    if (atlasState === "loading") return;
    if (geographyId === selectedGeographyId) {
      if (recordsState === "error") loadRecordPage();
      return;
    }
    requestGateRef.current.abort("records");
    clearRecords();
    setSelectedGeographyId(geographyId);
    if (geometry) setViewBox(deriveSelectionViewBox(atlas, geometry, geographyId));
  }, [atlas, atlasState, clearRecords, geometry, loadRecordPage, recordsState, selectedGeographyId]);
  const resetMap = useCallback(() => {
    requestGateRef.current.abort("records");
    clearRecords();
    setSelectedGeographyId(null);
    setViewBox(FULL_MAP_VIEWBOX);
  }, [clearRecords]);

  return (
    <main className={styles.workspace}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>TRACE v49 · governed functional foundation</p>
          <h1>Spacetime atlas</h1>
          <p>Recorded geographic and temporal context in the selected public archive release.</p>
        </div>
        <div className={styles.statusGrid} aria-label="Current map counts">
          <span><strong>{atlas.counts.denominator.toLocaleString()}</strong> denominator</span>
          <span><strong>{atlas.counts.mappedRecords.toLocaleString()}</strong> mapped</span>
          <span><strong>{atlas.counts.unmappedRecords.toLocaleString()}</strong> not mapped</span>
          <span><strong>{atlas.counts.heldExcluded.toLocaleString()}</strong> held excluded</span>
        </div>
      </header>

      <section className={styles.controls} aria-label="Spacetime controls">
        <button
          type="button"
          onClick={() => selectedIndex > 0 && selectPeriod(periods.periods[selectedIndex - 1].periodId)}
          disabled={selectedIndex <= 0}
        >
          Previous period
        </button>
        <label>
          Time period
          <select
            value={selectedPeriodId}
            onChange={(event) => selectPeriod(event.target.value)}
          >
            {periods.periods.map((period) => (
              <option key={period.periodId} value={period.periodId}>
                {period.label} · {period.recordCount.toLocaleString()} records
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => selectedIndex >= 0 && selectedIndex < periods.periods.length - 1
            && selectPeriod(periods.periods[selectedIndex + 1].periodId)}
          disabled={selectedIndex < 0 || selectedIndex >= periods.periods.length - 1}
        >
          Next period
        </button>
        <label>
          Functional renderer
          <select value={mode} onChange={(event) => setMode(event.target.value as SpacetimeRendererMode)}>
            <option value="aggregate">Aggregate anchors</option>
            <option value="density">Deterministic density dots</option>
            <option value="texture">Native count-tier texture</option>
          </select>
        </label>
        <button type="button" onClick={resetMap} disabled={!selectedGeographyId && viewBox === FULL_MAP_VIEWBOX}>
          Fit / reset map
        </button>
      </section>

      <div className={styles.contentGrid}>
        <section
          className={styles.mapPanel}
          aria-label="Functional aggregate map"
          aria-busy={atlasState === "loading"}
        >
          <div className={styles.methodNote}>
            <strong>{atlas.selectedPeriod.label}</strong>
            <span>Records whose recorded temporal extent overlaps this period.</span>
            <span>Map marks are aggregate selectors—not object locations or semantic relations.</span>
          </div>
          {geometryState === "loading" ? <p role="status" className={styles.loading}>Loading governed geometry…</p> : null}
          {geometryState === "error" ? <p role="alert" className={styles.loading}>Governed geometry could not be loaded.</p> : null}
          {atlasState === "loading" ? <p role="status" className={styles.loading}>Loading selected period…</p> : null}
          {atlasState === "error" ? <p role="alert" className={styles.loading}>The selected period could not be loaded.</p> : null}
          {geometry ? (
            <MapGraphic
              atlas={atlas}
              geometry={geometry}
              marks={marks}
              mode={mode}
              viewBox={viewBox}
              selectedGeographyId={selectedGeographyId}
              onSelect={selectGeography}
            />
          ) : null}
          <p className={styles.legend}>
            Equal Earth projection · Natural Earth {atlas.geometry.sourceVersion} {atlas.geometry.sourceScale} ·
            {mode === "density"
              ? " one synthetic aggregate dot per record where geometry capacity permits; an anchor carries any remainder"
              : mode === "texture"
                ? ` ${TRACE_NATIVE_COUNT_TIER_POLICY_VERSION} pattern spacing encodes count tier: ${TRACE_NATIVE_COUNT_TIERS.map((tier) => `${tier.legendValue} (${tier.spacingPx}px)`).join("; ")}`
                : " circle size encodes aggregate count"}.
          </p>
        </section>

        <aside className={styles.detailPanel} aria-label="Selected geography records">
          <p className={styles.eyebrow}>Selection</p>
          <h2>{selectedGeography?.label ?? "No geography selected"}</h2>
          {selectedGeography ? (
            <dl className={styles.selectionFacts}>
              <div><dt>Mapping state</dt><dd>{selectedGeography.mappingState.replace("_", " ")}</dd></div>
              <div><dt>Records</dt><dd>{selectedGeography.recordCount.toLocaleString()}</dd></div>
              <div><dt>Denominator</dt><dd>{selectedGeography.denominator.toLocaleString()}</dd></div>
              <div><dt>Precision</dt><dd>{precisionSummary(selectedGeography.precisionBreakdown)}</dd></div>
            </dl>
          ) : null}
          <RecordList
            state={recordsState}
            records={records}
            page={recordPage}
            onLoadMore={() => recordPage?.pageInfo.endCursor && loadRecordPage(recordPage.pageInfo.endCursor)}
          />
        </aside>
      </div>

      <details className={styles.accessiblePanel} open>
        <summary>Accessible geography table ({atlas.accessibleRows.length})</summary>
        <div className={styles.tableWrap}>
          <table>
            <caption>
              Numerical equivalent for the selected period. Choosing a row updates the matching public record list.
            </caption>
            <thead>
              <tr>
                <th scope="col">Geography</th>
                <th scope="col">Mapping</th>
                <th scope="col">Records</th>
                <th scope="col">Denominator</th>
                <th scope="col">Precision</th>
                <th scope="col">Interpretation</th>
              </tr>
            </thead>
            <tbody>
              {atlas.accessibleRows.map((row) => (
                <tr key={row.id} data-selected={row.geographyId === selectedGeographyId || undefined}>
                  <th scope="row">
                    <button
                      type="button"
                      onClick={() => selectGeography(row.geographyId)}
                      disabled={atlasState === "loading"}
                    >
                      {row.label}
                    </button>
                  </th>
                  <td>{row.mappingState.replace("_", " ")}</td>
                  <td>{row.recordCount.toLocaleString()}</td>
                  <td>{row.denominator.toLocaleString()}</td>
                  <td>{precisionSummary(row.precisionBreakdown)}</td>
                  <td>{row.interpretation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </main>
  );
}

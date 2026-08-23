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
  buildAggregateDotSeed,
  deriveGeoPath,
  deriveNativePatternDefinition,
  deriveNativePatternFillUrl,
  deriveNativeCountTier,
  deriveSpacetimeMapViewModel,
  fitProjection,
  generateAggregateDotField,
  indexGovernedGeometry,
  loadGovernedGeometry,
  prepareAggregateDotGeometry,
  TRACE_NATIVE_COUNT_TIERS,
  TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
  type AggregateDensityDot,
  type GovernedGeometryCollection,
  type GovernedGeometryFeature,
  type NativePatternDefinition,
  type PreparedAggregateDotGeometry,
  type SpacetimeMapRegionMark,
} from "@/features/trace-v49/spacetime/gis";
import type {
  PublicSpacetimeAtlasDataset,
  PublicSpacetimePrecisionBreakdown,
  PublicSpacetimePeriodsDataset,
  PublicSpacetimeRecordPage,
  PublicSpacetimeRecordSummary,
} from "@/features/trace-v49/spacetime/governed/types";
import styles from "./SpacetimeWorkspace.module.css";

const MAP_WIDTH = 1_200;
const MAP_HEIGHT = 640;
const MAP_PADDING = 28;
const RECORD_PAGE_SIZE = 25;
const FULL_MAP_VIEWBOX = `0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`;

type RendererMode = "aggregate" | "density" | "texture";
type RequestState = "idle" | "loading" | "ready" | "error";

interface ReadApiEnvelope<T> {
  readonly apiVersion: "v1";
  readonly data: T;
}

interface PreparedGeometry {
  readonly collection: GovernedGeometryCollection;
  readonly byId: ReadonlyMap<string, GovernedGeometryFeature>;
  readonly pathById: ReadonlyMap<string, string>;
  readonly dotGeometryById: Map<string, PreparedAggregateDotGeometry>;
  readonly projection: ReturnType<typeof fitProjection>;
}

interface PreparedMark {
  readonly geography: SpacetimeMapRegionMark;
  readonly x: number;
  readonly y: number;
  readonly dots: readonly AggregateDensityDot[];
  readonly fallbackCount: number;
  readonly pattern: NativePatternDefinition;
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

function prepareGeometry(
  collection: GovernedGeometryCollection,
): PreparedGeometry {
  const projection = fitProjection("equal-earth", collection, {
    width: MAP_WIDTH,
    height: MAP_HEIGHT,
    padding: MAP_PADDING,
  });
  const path = deriveGeoPath(projection);
  const pathById = new Map<string, string>();
  for (const feature of collection.features) {
    const value = path(feature);
    if (value) pathById.set(String(feature.id), value);
  }
  return Object.freeze({
    collection,
    byId: indexGovernedGeometry(collection),
    pathById,
    dotGeometryById: new Map<string, PreparedAggregateDotGeometry>(),
    projection,
  });
}

function prepareMarks(
  atlas: PublicSpacetimeAtlasDataset,
  geometry: PreparedGeometry,
  mode: RendererMode,
): readonly PreparedMark[] {
  const viewModel = deriveSpacetimeMapViewModel({
    atlas,
    geometryIndex: geometry.byId,
    projection: geometry.projection,
  });
  return Object.freeze(viewModel.mappedMarks.flatMap((geography) => {
    const anchorGeometry = geometry.byId.get(geography.anchor.geometryId);
    if (!anchorGeometry) return [];
    const projected = geometry.projection([geography.anchor.longitude, geography.anchor.latitude]);
    if (!projected) return [];
    const tier = deriveNativeCountTier(geography.recordCount);
    const pattern = deriveNativePatternDefinition({
      namespace: `${TRACE_NATIVE_COUNT_TIER_POLICY_VERSION}:${atlas.selectedPeriod.periodId}:${geography.geographyId}`,
      family: "dots",
      encodedVariable: "record_count_tier",
      legendValue: tier.legendValue,
      spacingPx: tier.spacingPx,
      weightPx: tier.weightPx,
    });

    // Multi-geometry concepts use one aggregate anchor. Repeating a dot field in
    // every target geometry would multiply the represented record count.
    let preparedDotGeometry: PreparedAggregateDotGeometry | undefined;
    if (mode === "density" && geography.geometryIds.length === 1) {
      preparedDotGeometry = geometry.dotGeometryById.get(anchorGeometry.id);
      if (!preparedDotGeometry) {
        preparedDotGeometry = prepareAggregateDotGeometry(
          anchorGeometry,
          geometry.projection,
          `equal-earth:${MAP_WIDTH}x${MAP_HEIGHT}:padding-${MAP_PADDING}`,
        );
        geometry.dotGeometryById.set(anchorGeometry.id, preparedDotGeometry);
      }
    }
    const density = preparedDotGeometry
      ? generateAggregateDotField({
          geometry: anchorGeometry,
          projection: geometry.projection,
          recordCount: geography.recordCount,
          seed: buildAggregateDotSeed({
            releaseId: atlas.release.researchReleaseId,
            geometryId: anchorGeometry.id,
            timeBucketId: atlas.selectedPeriod.periodId,
            recordCount: geography.recordCount,
            policyVersion: "trace-dot-density-grid-v1",
          }),
          fallbackAnchor: geography.anchor,
          preparedGeometry: preparedDotGeometry,
        })
      : null;
    return [Object.freeze({
      geography,
      x: projected[0],
      y: projected[1],
      dots: density?.dots ?? Object.freeze([]),
      fallbackCount: density?.fallback?.representedRecordCount ?? 0,
      pattern,
    })];
  }));
}

function deriveSelectionViewBox(
  atlas: PublicSpacetimeAtlasDataset,
  geometry: PreparedGeometry,
  geographyId: string,
): string {
  const geography = atlas.mappedGeographies.find((candidate) => candidate.geographyId === geographyId);
  if (!geography) return FULL_MAP_VIEWBOX;
  const path = deriveGeoPath(geometry.projection);
  const bounds = geography.geometryIds
    .map((geometryId) => geometry.byId.get(geometryId))
    .filter((feature): feature is GovernedGeometryFeature => Boolean(feature))
    .map((feature) => path.bounds(feature));
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
  geometry: PreparedGeometry;
  marks: readonly PreparedMark[];
  mode: RendererMode;
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
    () => new Map(marks.map((mark) => [mark.geography.geographyId, mark.pattern])),
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
          {marks.map((mark) => (
            <pattern
              key={mark.pattern.id}
              id={mark.pattern.id}
              patternUnits="userSpaceOnUse"
              width={mark.pattern.width}
              height={mark.pattern.height}
            >
              {mark.pattern.primitive.kind === "circle" ? (
                <circle
                  cx={mark.pattern.primitive.cx}
                  cy={mark.pattern.primitive.cy}
                  r={mark.pattern.primitive.radius}
                  className={styles.patternPrimitive}
                />
              ) : (
                <line
                  x1={mark.pattern.primitive.x1}
                  y1={mark.pattern.primitive.y1}
                  x2={mark.pattern.primitive.x2}
                  y2={mark.pattern.primitive.y2}
                  strokeWidth={mark.pattern.primitive.strokeWidth}
                  className={styles.patternPrimitive}
                />
              )}
            </pattern>
          ))}
        </defs>
      ) : null}
      <g aria-hidden="true">
        {geometry.collection.features.map((feature) => {
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
              {mode === "density" && mark.dots.length > 0 ? mark.dots.map((dot) => (
                <circle
                  key={dot.id}
                  cx={dot.x}
                  cy={dot.y}
                  r={2.1}
                  className={mark.geography.geographyId === selectedGeographyId ? styles.selectedMark : styles.densityMark}
                  onClick={() => onSelect(mark.geography.geographyId)}
                />
              )) : null}
              {mode !== "density" || mark.dots.length === 0 || mark.fallbackCount > 0 ? (
                <circle
                  cx={mark.x}
                  cy={mark.y}
                  r={Math.max(4, Math.min(18, 3 + Math.sqrt(
                    mode === "density" && mark.fallbackCount > 0
                      ? mark.fallbackCount
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
  const [mode, setMode] = useState<RendererMode>("aggregate");
  const [viewBox, setViewBox] = useState(FULL_MAP_VIEWBOX);
  const [geometry, setGeometry] = useState<PreparedGeometry | null>(null);
  const [geometryState, setGeometryState] = useState<RequestState>("loading");
  const [atlasState, setAtlasState] = useState<RequestState>("ready");
  const [recordsState, setRecordsState] = useState<RequestState>("idle");
  const [recordPage, setRecordPage] = useState<PublicSpacetimeRecordPage | null>(null);
  const [records, setRecords] = useState<readonly PublicSpacetimeRecordSummary[]>(Object.freeze([]));
  const geometryAbortRef = useRef<AbortController | null>(null);
  const atlasAbortRef = useRef<AbortController | null>(null);
  const recordsAbortRef = useRef<AbortController | null>(null);

  const releaseId = periods.release.researchReleaseId;
  const manifestSha256 = periods.release.researchManifestSha256;

  useEffect(() => {
    const controller = new AbortController();
    geometryAbortRef.current?.abort();
    geometryAbortRef.current = controller;
    setGeometryState("loading");
    void fetch(periods.geometry.assetPath, { cache: "force-cache", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Geometry request failed (${response.status})`);
        const json = await response.json() as unknown;
        return loadGovernedGeometry(json, {
          featureCount: periods.geometry.featureCount,
          geometryArtifactId: periods.geometry.geometryArtifactId,
        });
      })
      .then((collection) => {
        if (controller.signal.aborted) return;
        setGeometry(prepareGeometry(collection));
        setGeometryState("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setGeometryState("error");
      });
    return () => controller.abort();
  }, [periods.geometry.assetPath, periods.geometry.featureCount, periods.geometry.geometryArtifactId]);

  const selectPeriod = useCallback((periodId: string) => {
    if (periodId === selectedPeriodId) return;
    const controller = new AbortController();
    atlasAbortRef.current?.abort();
    recordsAbortRef.current?.abort();
    atlasAbortRef.current = controller;
    setAtlasState("loading");
    setSelectedGeographyId(null);
    setViewBox(FULL_MAP_VIEWBOX);
    setRecordPage(null);
    setRecords(Object.freeze([]));
    setRecordsState("idle");
    void readApi<PublicSpacetimeAtlasDataset>(
      `${apiPath(releaseId, "atlas")}?period=${encodeURIComponent(periodId)}`,
      manifestSha256,
      controller.signal,
    ).then((nextAtlas) => {
      if (controller.signal.aborted) return;
      setAtlas(nextAtlas);
      setSelectedPeriodId(nextAtlas.selectedPeriod.periodId);
      setAtlasState("ready");
    }).catch(() => {
      if (!controller.signal.aborted) setAtlasState("error");
    });
  }, [manifestSha256, releaseId, selectedPeriodId]);

  useEffect(() => () => {
    geometryAbortRef.current?.abort();
    atlasAbortRef.current?.abort();
    recordsAbortRef.current?.abort();
  }, []);

  const loadRecordPage = useCallback((after?: string) => {
    if (!selectedGeographyId) return;
    const controller = new AbortController();
    recordsAbortRef.current?.abort();
    recordsAbortRef.current = controller;
    setRecordsState("loading");
    const query = new URLSearchParams({
      period: selectedPeriodId,
      first: String(RECORD_PAGE_SIZE),
    });
    if (after) query.set("after", after);
    void readApi<PublicSpacetimeRecordPage>(
      `${apiPath(releaseId, `geographies/${encodeURIComponent(selectedGeographyId)}/records`)}?${query}`,
      manifestSha256,
      controller.signal,
    ).then((page) => {
      if (controller.signal.aborted) return;
      setRecordPage(page);
      setRecords((current) => Object.freeze(after ? [...current, ...page.nodes] : [...page.nodes]));
      setRecordsState("ready");
    }).catch(() => {
      if (!controller.signal.aborted) setRecordsState("error");
    });
  }, [manifestSha256, releaseId, selectedGeographyId, selectedPeriodId]);

  useEffect(() => {
    if (!selectedGeographyId) {
      setRecordPage(null);
      setRecords(Object.freeze([]));
      setRecordsState("idle");
      return;
    }
    loadRecordPage();
  }, [loadRecordPage, selectedGeographyId]);

  const marks = useMemo(
    () => geometry ? prepareMarks(atlas, geometry, mode) : Object.freeze([]),
    [atlas, geometry, mode],
  );
  const selectedIndex = periods.periods.findIndex((period) => period.periodId === selectedPeriodId);
  const selectedGeography = atlas.accessibleRows.find((row) => row.geographyId === selectedGeographyId) ?? null;
  const selectGeography = useCallback((geographyId: string) => {
    if (geographyId === selectedGeographyId) return;
    recordsAbortRef.current?.abort();
    setRecordPage(null);
    setRecords(Object.freeze([]));
    setRecordsState("idle");
    setSelectedGeographyId(geographyId);
    if (geometry) setViewBox(deriveSelectionViewBox(atlas, geometry, geographyId));
  }, [atlas, geometry, selectedGeographyId]);
  const resetMap = useCallback(() => {
    recordsAbortRef.current?.abort();
    setRecordPage(null);
    setRecords(Object.freeze([]));
    setRecordsState("idle");
    setSelectedGeographyId(null);
    setViewBox(FULL_MAP_VIEWBOX);
  }, []);

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
          disabled={selectedIndex <= 0 || atlasState === "loading"}
        >
          Previous period
        </button>
        <label>
          Time period
          <select
            value={selectedPeriodId}
            onChange={(event) => selectPeriod(event.target.value)}
            disabled={atlasState === "loading"}
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
          disabled={selectedIndex < 0 || selectedIndex >= periods.periods.length - 1 || atlasState === "loading"}
        >
          Next period
        </button>
        <label>
          Functional renderer
          <select value={mode} onChange={(event) => setMode(event.target.value as RendererMode)}>
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
        <section className={styles.mapPanel} aria-label="Functional aggregate map">
          <div className={styles.methodNote}>
            <strong>{atlas.selectedPeriod.label}</strong>
            <span>Records whose recorded temporal extent overlaps this period.</span>
            <span>Map marks are aggregate selectors—not object locations or semantic relations.</span>
          </div>
          {geometryState === "loading" ? <p role="status" className={styles.loading}>Loading governed geometry…</p> : null}
          {geometryState === "error" ? <p role="alert" className={styles.loading}>Governed geometry could not be loaded.</p> : null}
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
                    <button type="button" onClick={() => selectGeography(row.geographyId)}>
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

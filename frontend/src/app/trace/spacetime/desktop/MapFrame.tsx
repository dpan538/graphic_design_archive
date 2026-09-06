"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { MapGraphic, type MapGraphicClassNames, type SpacetimeLayer, type SpacetimeRankedRow, type SpacetimeTemporalSeries } from "@/features/trace-v49/spacetime/map";
import {
  TRACE_NATIVE_COUNT_TIERS,
  type PreparedSpacetimeDensity,
  type PreparedSpacetimeProjection,
  type PreparedSpacetimeRendererMark,
  type SpacetimeRendererMode,
} from "@/features/trace-v49/spacetime/gis";
import type { PublicSpacetimeAtlasDataset } from "@/features/trace-v49/spacetime/governed/types";
import {
  BOUNDARY,
  EMPTY_PERIOD,
  GEOMETRY_FAILED,
  LABEL_RECORDS,
  LEGEND,
  LEGEND_TEMPORAL,
  LOADING_GEOMETRY,
  LOADING_PERIOD,
  MAP_LABEL,
  NOT_PLOTTED_NOTE,
  NOT_PLOTTED_TITLE,
  PERIOD_FAILED,
  PROJECTION_NOTE,
  RETRY,
  UNAVAILABLE,
  WORLD_VIEW,
} from "../lib/content";
import styles from "./MapFrame.module.css";

/* 02 — the map (§7h): a research cartography surface over the sealed
   geometry, after the owner's reference sheets — a fine line map, its
   coast a firm line (an under-layer of every land path's stroke, of
   which the fills leave only the outer edge), its boundaries hairlines,
   the land a pale warm tone, mapped land a pale blue; nothing solid
   sits on it. DISTRIBUTION draws each mapped geography's records as a
   RING at its governed anchor — its radius the sealed count policy, its
   form the sealed count tier (a thin ring, a ring, a ring with its
   centre, a double ring) — or the sealed density dots, or the sealed
   texture. TEMPORAL draws, at the same anchor, three bars — records in
   the previous, this and the next period, from the three governed
   atlases — the current bar in cobalt, its neighbours neutral, the
   chosen place's in red; at world scale only geographies of the third
   count tier and above carry the full glyph, the rest a small ring
   until hovered or chosen; a focused view shows every glyph. Places
   without a safe map position stand in a NOT PLOTTED list with the
   same three bars. The selection is red; its sealed dot field, one dot
   a record, shows inside the focused geography. Labels are
   interaction-led: the selected place and the hovered one. */

export interface MapFrameProps {
  readonly atlas: PublicSpacetimeAtlasDataset;
  readonly geometry: PreparedSpacetimeProjection | null;
  readonly geometryState: "idle" | "loading" | "ready" | "error";
  readonly atlasState: "idle" | "loading" | "ready" | "error";
  readonly loadingPeriodLabel: string | null;
  readonly marks: readonly PreparedSpacetimeRendererMark[];
  readonly mode: SpacetimeRendererMode;
  readonly layer: SpacetimeLayer;
  readonly viewBox: string;
  readonly fullViewBox: string;
  readonly selectedGeographyId: string | null;
  readonly selectedDensity: PreparedSpacetimeDensity | null;
  readonly temporal: ReadonlyMap<string, SpacetimeTemporalSeries>;
  readonly windowState: "idle" | "loading" | "ready" | "error";
  readonly notPlotted: readonly SpacetimeRankedRow[];
  readonly status: string;
  readonly onSelect: (geographyId: string) => void;
  readonly onWorldView: () => void;
  readonly onRetryPeriod: () => void;
}

const CLASS_NAMES: MapGraphicClassNames = {
  map: styles.map,
  land: styles.land,
  mappedLand: styles.mappedLand,
  selectedLand: styles.selectedLand,
  aggregateMark: styles.aggregateMark,
  densityMark: styles.densityMark,
  selectedMark: styles.selectedMark,
  patternPrimitive: styles.patternPrimitive,
};

/* the sealed count policy's radius, as the functional view draws it */
const sealedRadius = (count: number) => Math.max(4, Math.min(18, 3 + Math.sqrt(count) * 0.75));
const tierIndex = (count: number) => TRACE_NATIVE_COUNT_TIERS.findIndex((tier) => count >= tier.minimumInclusive && (tier.maximumInclusive === null || count <= tier.maximumInclusive));
const FULL_GLYPH_TIER = 2;

interface LabelSpot {
  readonly geographyId: string;
  readonly label: string;
  readonly count: number;
  readonly x: number;
  readonly y: number;
}

export default function MapFrame({
  atlas,
  geometry,
  geometryState,
  atlasState,
  loadingPeriodLabel,
  marks,
  mode,
  layer,
  viewBox,
  fullViewBox,
  selectedGeographyId,
  selectedDensity,
  temporal,
  windowState,
  notPlotted,
  status,
  onSelect,
  onWorldView,
  onRetryPeriod,
}: MapFrameProps) {
  const stageRef = useRef<HTMLDivElement>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [spots, setSpots] = useState<readonly LabelSpot[]>([]);
  const focused = viewBox !== fullViewBox;
  const empty = atlasState === "ready" && atlas.counts.denominator === 0;

  const geographyByGeometryId = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of atlas.mappedGeographies) for (const id of item.geometryIds) map.set(id, item.geographyId);
    return map;
  }, [atlas.mappedGeographies]);
  const markById = useMemo(() => new Map(marks.map((mark) => [mark.geography.geographyId, mark])), [marks]);
  const zoom = useMemo(() => {
    const parts = viewBox.split(/\s+/).map(Number);
    const full = fullViewBox.split(/\s+/).map(Number);
    return parts.length === 4 && full.length === 4 && full[2] > 0 ? parts[2] / full[2] : 1;
  }, [fullViewBox, viewBox]);
  /* the window's scale: the most records any mapped place carries in
     the three periods — the same bar heights for every glyph */
  const windowMost = useMemo(() => {
    let most = 1;
    for (const series of temporal.values()) {
      if (series.mappingState !== "mapped") continue;
      for (const stat of [series.previous, series.current, series.next]) if (stat && stat.records > most) most = stat.records;
    }
    return most;
  }, [temporal]);
  const notPlottedMost = useMemo(() => Math.max(1, ...notPlotted.flatMap(({ row }) => {
    const series = temporal.get(row.geographyId);
    return series ? [series.previous?.records ?? 0, series.current?.records ?? 0, series.next?.records ?? 0] : [row.recordCount];
  })), [notPlotted, temporal]);

  /* the pointer's geography: a glyph names its own; a land path is the
     feature at its index */
  const geographyAt = useCallback((target: EventTarget | null): string | null => {
    if (!(target instanceof Element) || !geometry) return null;
    const named = target.closest("[data-geography]");
    if (named) return named.getAttribute("data-geography");
    const svg = target.closest("svg");
    if (!svg || target.tagName !== "path") return null;
    const paths = [...svg.querySelectorAll("g > path")] as Element[];
    const feature = geometry.source.collection.features[paths.indexOf(target)];
    return feature ? geographyByGeometryId.get(String(feature.id)) ?? null : null;
  }, [geographyByGeometryId, geometry]);

  /* the labels' places: the marks' anchors, projected to the stage */
  const place = useCallback(() => {
    const stage = stageRef.current;
    const svg = stage?.querySelector<SVGSVGElement>("[data-layer=\"marks\"] svg");
    if (!stage || !svg) {
      setSpots([]);
      return;
    }
    const wanted = [selectedGeographyId, hoverId].filter((id, index, all): id is string => Boolean(id) && all.indexOf(id) === index);
    const rect = stage.getBoundingClientRect();
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    setSpots(wanted.flatMap((id) => {
      const mark = markById.get(id);
      if (!mark) return [];
      const point = new DOMPoint(mark.x, mark.y).matrixTransform(ctm);
      return [{ geographyId: id, label: mark.geography.label, count: mark.geography.recordCount, x: point.x - rect.left, y: point.y - rect.top }];
    }));
  }, [hoverId, markById, selectedGeographyId]);

  useLayoutEffect(place, [place, viewBox, mode, layer, geometry]);
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(place);
    observer.observe(stage);
    return () => observer.disconnect();
  }, [place]);

  const barHeight = (records: number) => (records > 0 ? (2 + 18 * Math.sqrt(records / windowMost)) * zoom : 0);
  const legend = layer === "temporal" ? LEGEND_TEMPORAL : LEGEND[mode];

  return (
    <section className={styles.frame} aria-label={MAP_LABEL} aria-busy={atlasState === "loading" || geometryState === "loading" || undefined}>
      <div
        ref={stageRef}
        className={styles.stage}
        data-mode={mode}
        data-layer={layer}
        data-state={atlasState}
        data-focused={focused || undefined}
        onPointerOver={(event) => setHoverId(geographyAt(event.target))}
        onPointerOut={(event) => { if (geographyAt(event.target)) setHoverId(null); }}
      >
        {geometry ? (
          <>
            <svg className={styles.coast} viewBox={viewBox} aria-hidden="true" data-layer="coast">
              <g>
                {geometry.source.collection.features.map((feature) => (
                  <path key={String(feature.id)} d={geometry.pathById.get(String(feature.id)) ?? ""} />
                ))}
              </g>
            </svg>
            <div data-layer="marks" className={styles.marks}>
              <MapGraphic
                atlas={atlas}
                geometry={geometry}
                marks={marks}
                mode={mode}
                viewBox={viewBox}
                selectedGeographyId={selectedGeographyId}
                onSelect={onSelect}
                classNames={CLASS_NAMES}
              />
            </div>
            <svg className={styles.glyphs} viewBox={viewBox} aria-hidden="true" data-layer="glyphs">
              {/* the focused place's sealed dot field: one dot a record */}
              {focused && selectedDensity && selectedGeographyId ? (
                <g className={styles.focusField}>
                  {selectedDensity.dots.map((dot) => (
                    <circle key={dot.id} cx={dot.x} cy={dot.y} r={1.5 * zoom} />
                  ))}
                </g>
              ) : null}
              {layer === "distribution" && mode === "aggregate" ? marks.map((mark) => {
                const id = mark.geography.geographyId;
                const selected = id === selectedGeographyId;
                const r = sealedRadius(mark.geography.recordCount);
                const tier = tierIndex(mark.geography.recordCount);
                return (
                  <g
                    key={id}
                    className={styles.ring}
                    data-geography={id}
                    data-tier={tier}
                    data-selected={selected || undefined}
                    data-hover={id === hoverId || undefined}
                    onClick={() => onSelect(id)}
                  >
                    <title>{mark.geography.label} · {LABEL_RECORDS(mark.geography.recordCount)}</title>
                    <circle cx={mark.x} cy={mark.y} r={r} className={styles.ringOuter} />
                    {tier >= 3 ? <circle cx={mark.x} cy={mark.y} r={Math.max(2, r - 4)} className={styles.ringInner} /> : null}
                    {tier === 2 ? <circle cx={mark.x} cy={mark.y} r={1.6} className={styles.ringCentre} /> : null}
                  </g>
                );
              }) : null}
              {layer === "temporal" ? marks.map((mark) => {
                const id = mark.geography.geographyId;
                const series = temporal.get(id);
                const selected = id === selectedGeographyId;
                const hovered = id === hoverId;
                const full = focused || selected || hovered || tierIndex(mark.geography.recordCount) >= FULL_GLYPH_TIER;
                const w = 4 * zoom;
                const gap = 1.5 * zoom;
                const base = mark.y + 6 * zoom;
                const left = mark.x - (w * 3 + gap * 2) / 2;
                const stats = series ? [series.previous, series.current, series.next] : [null, null, null];
                return (
                  <g
                    key={id}
                    className={styles.glyph}
                    data-geography={id}
                    data-selected={selected || undefined}
                    data-hover={hovered || undefined}
                    data-full={full || undefined}
                    onClick={() => onSelect(id)}
                  >
                    <title>{mark.geography.label} · {stats.map((stat) => stat ? `${stat.label} ${stat.records.toLocaleString("en-US")}` : UNAVAILABLE).join(" · ")}</title>
                    {full ? (
                      <>
                        <rect x={left} y={base - 0.4 * zoom} width={w * 3 + gap * 2} height={0.8 * zoom} className={styles.glyphBase} />
                        {stats.map((stat, index) => {
                          const x = left + index * (w + gap);
                          if (!stat) return <rect key={index} x={x} y={base - 1.5 * zoom} width={w} height={1.5 * zoom} className={styles.glyphMissing} />;
                          const h = barHeight(stat.records);
                          return (
                            <rect
                              key={index}
                              x={x}
                              y={base - h}
                              width={w}
                              height={h}
                              className={styles.glyphBar}
                              data-role={index === 1 ? "current" : "neighbour"}
                            />
                          );
                        })}
                      </>
                    ) : (
                      <circle cx={mark.x} cy={mark.y} r={2.6 * zoom} className={styles.glyphCompact} />
                    )}
                  </g>
                );
              }) : null}
            </svg>
            {spots.map((spot) => {
              const series = layer === "temporal" ? temporal.get(spot.geographyId) : null;
              return (
                <span
                  key={spot.geographyId}
                  className={styles.label}
                  data-selected={spot.geographyId === selectedGeographyId || undefined}
                  style={{ left: spot.x, top: spot.y }}
                  aria-hidden="true"
                >
                  <span className={styles.labelName}>{spot.label}</span>
                  <span className={`${styles.labelCount} tnum`}>
                    {series
                      ? [series.previous, series.current, series.next].map((stat) => stat ? `${stat.label} ${stat.records.toLocaleString("en-US")}` : UNAVAILABLE).join(" · ")
                      : LABEL_RECORDS(spot.count)}
                  </span>
                </span>
              );
            })}
          </>
        ) : null}

        {layer === "temporal" && notPlotted.length > 0 ? (
          <div className={styles.notPlotted} role="group" aria-label={NOT_PLOTTED_TITLE}>
            <p className={styles.notPlottedTitle}>{NOT_PLOTTED_TITLE}</p>
            <p className={styles.notPlottedNote}>{NOT_PLOTTED_NOTE}</p>
            <ul className={styles.notPlottedList}>
              {notPlotted.map(({ row }) => {
                const series = temporal.get(row.geographyId);
                const stats = series ? [series.previous, series.current, series.next] : [null, null, null];
                const selected = row.geographyId === selectedGeographyId;
                return (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={styles.notPlottedRow}
                      data-selected={selected || undefined}
                      aria-pressed={selected}
                      title={stats.map((stat) => stat ? `${stat.label} ${stat.records.toLocaleString("en-US")}` : UNAVAILABLE).join(" · ")}
                      onClick={() => onSelect(row.geographyId)}
                    >
                      <span className={styles.notPlottedName}>{row.label}</span>
                      <span className={styles.miniGlyph} aria-hidden="true">
                        {stats.map((stat, index) => (
                          <span
                            key={index}
                            className={styles.miniBar}
                            data-role={index === 1 ? "current" : stat ? "neighbour" : "missing"}
                            style={{ height: stat ? `${Math.max(stat.records > 0 ? 2 : 1, 14 * Math.sqrt(stat.records / notPlottedMost))}px` : "1px" }}
                          />
                        ))}
                      </span>
                      <span className={`${styles.notPlottedCount} tnum`}>{windowState === "loading" ? "…" : (series?.current?.records ?? row.recordCount).toLocaleString("en-US")}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        {geometryState === "loading" ? (
          <p className={styles.caption} role="status">{LOADING_GEOMETRY}</p>
        ) : geometryState === "error" ? (
          <p className={styles.caption} role="alert">{GEOMETRY_FAILED}</p>
        ) : atlasState === "loading" && loadingPeriodLabel ? (
          <p className={styles.caption} role="status">{LOADING_PERIOD(loadingPeriodLabel)}</p>
        ) : atlasState === "error" ? (
          <div className={styles.caption} role="alert">
            <span>{PERIOD_FAILED}</span>
            <button type="button" className={styles.retry} onClick={onRetryPeriod}>{RETRY}</button>
          </div>
        ) : empty ? (
          <p className={styles.caption} role="status">{EMPTY_PERIOD}</p>
        ) : null}

        <p className={styles.legend}>
          <span>{legend}</span>
          <span className={styles.projection}>{PROJECTION_NOTE(atlas.geometry.sourceVersion, atlas.geometry.sourceScale)}</span>
        </p>
        <p className={styles.boundary}>{BOUNDARY}</p>
      </div>

      <div className={styles.bar}>
        <div className={styles.tools}>
          {focused || selectedGeographyId ? (
            <button type="button" onClick={onWorldView}>{WORLD_VIEW}</button>
          ) : null}
        </div>
        <p className={styles.status} role="status" aria-live="polite">{status}</p>
      </div>
    </section>
  );
}

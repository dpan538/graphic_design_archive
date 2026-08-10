"use client";

import { geoEqualEarth, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import type { CSSProperties, KeyboardEvent } from "react";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import worldAtlas from "world-atlas/countries-50m.json";
import styles from "./TraceExplorer.module.css";
import type { RelationFamily, TraceAtlas } from "./trace-types";

export interface EvolutionObservation {
  region: string;
  decade: number;
  count: number;
}

type TimeMode = "cumulative" | "decade";

const FAMILY_ORDER: RelationFamily[] = [
  "source_provenance",
  "time_place",
  "medium_context",
  "historical_influence",
];

const FAMILY_LABELS: Record<RelationFamily, string> = {
  source_provenance: "Source / provenance",
  time_place: "Time / place",
  medium_context: "Medium / context",
  historical_influence: "Influence — absent",
};

const FAMILY_SHORT_LABELS: Record<RelationFamily, string> = {
  source_provenance: "Source",
  time_place: "Time / place",
  medium_context: "Medium / context",
  historical_influence: "Influence 0",
};

const REGION_ALIASES: Record<string, string[]> = {
  "United States": ["United States of America"],
  "Aotearoa New Zealand": ["New Zealand"],
  "Australia / Indigenous": ["Australia"],
  "Bosnia and Herzegovina": ["Bosnia and Herz."],
  "Cape Verde": ["Cabo Verde"],
  "China / Hong Kong": ["China"],
  "Czech Republic": ["Czechia"],
  "Democratic Republic of the Congo": ["Dem. Rep. Congo"],
  "Dominican Republic": ["Dominican Rep."],
  "Federated States of Micronesia": ["Micronesia"],
  "Hawaii": ["United States of America"],
  "Israel / Palestine": ["Israel", "Palestine"],
  "Korean Peninsula": ["North Korea", "South Korea"],
  "Mexico City": ["Mexico"],
  "North Macedonia": ["Macedonia"],
  "Republic of the Congo": ["Congo"],
  "Solomon Islands": ["Solomon Is."],
};

const topology = worldAtlas as unknown as Topology;
const countries = feature(
  topology,
  topology.objects.countries as GeometryCollection<Record<string, string>>,
) as FeatureCollection<Geometry, Record<string, string>>;
const projection = geoEqualEarth().fitExtent([[378, 610], [924, 846]], countries);
const mapPath = geoPath(projection);

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return { x: cx + Math.cos(radians) * radius, y: cy + Math.sin(radians) * radius };
}

function bandPath(cx: number, cy: number, outer: number, inner: number, startAngle: number, endAngle: number) {
  const outerStart = polarPoint(cx, cy, outer, startAngle);
  const outerEnd = polarPoint(cx, cy, outer, endAngle);
  const innerEnd = polarPoint(cx, cy, inner, endAngle);
  const innerStart = polarPoint(cx, cy, inner, startAngle);
  return [
    `M${outerStart.x.toFixed(2)},${outerStart.y.toFixed(2)}`,
    `A${outer},${outer} 0 0 1 ${outerEnd.x.toFixed(2)},${outerEnd.y.toFixed(2)}`,
    `L${innerEnd.x.toFixed(2)},${innerEnd.y.toFixed(2)}`,
    `A${inner},${inner} 0 0 0 ${innerStart.x.toFixed(2)},${innerStart.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

function countryNames(region: string) {
  return REGION_ALIASES[region] ?? [region];
}

function logarithmicDepth(count: number, maximum: number, minimum: number, maximumDepth: number) {
  if (count <= 0 || maximum <= 0) return 1;
  return minimum + (Math.log1p(count) / Math.log1p(maximum)) * (maximumDepth - minimum);
}

function activate(event: KeyboardEvent<SVGGElement>, callback: () => void) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    callback();
  }
}

export default function EvolutionSystemPlate({
  atlas,
  selectedIndex,
  selectedRegion,
  mode,
  focusCell,
  onFocusCell,
  onActivate,
}: {
  atlas: TraceAtlas;
  selectedIndex: number;
  selectedRegion: string;
  mode: TimeMode;
  focusCell: EvolutionObservation;
  onFocusCell: (cell: EvolutionObservation) => void;
  onActivate: (cell: EvolutionObservation) => void;
}) {
  const cx = 650;
  const cy = 470;
  const selectedDecade = atlas.decades[selectedIndex];
  const visibleTotal = mode === "cumulative"
    ? atlas.decadeTotals.slice(0, selectedIndex + 1).reduce((sum, count) => sum + count, 0)
    : atlas.decadeTotals[selectedIndex];
  const regionSpan = 252 / atlas.regionMatrix.length;
  const maximumRegion = Math.max(...atlas.regionMatrix.map((row) => row.total));
  const familyTotals = atlas.relationTypes.reduce<Record<RelationFamily, number>>(
    (result, item) => ({ ...result, [item.family]: result[item.family] + item.count }),
    { source_provenance: 0, time_place: 0, medium_context: 0, historical_influence: 0 },
  );
  const maximumFamily = Math.max(...Object.values(familyTotals), 1);
  const maximumMedium = Math.max(...atlas.mediumGroups.map((medium) => medium.count), 1);
  const regionMapPoints = atlas.regionMatrix.flatMap((row) => {
    const aliases = countryNames(row.region);
    const country = countries.features.find((item) => aliases.includes(item.properties?.name ?? ""));
    if (!country) return [];
    const point = mapPath.centroid(country);
    return Number.isFinite(point[0]) && Number.isFinite(point[1]) ? [{ row, point }] : [];
  });
  const mappedRegionNames = new Set(regionMapPoints.map(({ row }) => row.region));
  const unmappedRegionRows = atlas.regionMatrix.filter((row) => !mappedRegionNames.has(row.region));
  const maximumMappedDecadeCount = Math.max(
    ...regionMapPoints.map(({ row }) => row.counts[selectedIndex] ?? 0),
    1,
  );

  return (
    <div className={styles.systemPlateWrap}>
      <svg className={styles.systemPlate} viewBox="0 0 1300 900" role="img" aria-labelledby="evolution-system-title evolution-system-desc">
        <title id="evolution-system-title">TRACE archive evolution system diagram</title>
        <desc id="evolution-system-desc">Fifteen geographic aggregates, seven display-only medium groups, and four evidence families are shown as independent count scales beside a real Equal Earth map. Arc depth encodes a logarithmic count. Mapped country centroids and the separate non-coordinate aggregate are selectable. No mark claims historical influence.</desc>
        <defs>
          <linearGradient id="system-field" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#fff9ea" /><stop offset="100%" stopColor="#eee5d2" /></linearGradient>
        </defs>
        <rect width="1300" height="900" fill="url(#system-field)" />
        <g className={styles.systemRegistration} aria-hidden="true">
          {Array.from({ length: 33 }, (_, index) => <line key={`v-${index}`} x1={20 + index * 40} y1="0" x2={20 + index * 40} y2="900" />)}
          {Array.from({ length: 23 }, (_, index) => <line key={`h-${index}`} x1="0" y1={20 + index * 40} x2="1300" y2={20 + index * 40} />)}
          <circle cx={cx} cy={cy} r="390" /><circle cx={cx} cy={cy} r="318" /><circle cx={cx} cy={cy} r="236" />
        </g>
        <g className={styles.systemMeta} aria-hidden="true">
          <text x="38" y="40">TRACE / SYSTEM DIAGRAM 01</text><text x="38" y="62">INDEPENDENT COUNT SCALES · ARC DEPTH = LOG COUNT</text>
          <text x="1262" y="40" textAnchor="end">FROZEN CANDIDATE V48</text><text x="1262" y="62" textAnchor="end">NO INFERRED INFLUENCE</text>
        </g>

        <g className={styles.systemRegionArc}>
          {atlas.regionMatrix.map((row, index) => {
            const start = -126 + index * regionSpan + 1.1;
            const end = -126 + (index + 1) * regionSpan - 1.1;
            const middle = (start + end) / 2;
            const labelPoint = polarPoint(cx, cy, 410, middle);
            const cell = { region: row.region, decade: selectedDecade, count: row.counts[selectedIndex] ?? 0 };
            const active = row.region === selectedRegion;
            const depth = logarithmicDepth(row.total, maximumRegion, 9, 48);
            return (
              <g key={row.region} role="button" tabIndex={0} data-active={active} aria-label={`${row.region}: ${row.total.toLocaleString()} active objects across all decades; ${cell.count.toLocaleString()} in the ${selectedDecade}s`} onMouseEnter={() => onFocusCell(cell)} onFocus={() => onFocusCell(cell)} onClick={() => onActivate(cell)} onKeyDown={(event) => activate(event, () => onActivate(cell))}>
                <path d={bandPath(cx, cy, 388, 388 - depth, start, end)} style={{ "--system-weight": Math.max(0.36, Math.sqrt(row.total / maximumRegion)) } as CSSProperties} />
                <text x={labelPoint.x} y={labelPoint.y} textAnchor={labelPoint.x < cx ? "end" : "start"}>{row.region.length > 18 ? `${row.region.slice(0, 16)}…` : row.region}</text>
                <title>{row.region}: {row.total.toLocaleString()} active objects across all decades; {cell.count.toLocaleString()} in the {selectedDecade}s</title>
              </g>
            );
          })}
        </g>

        <g className={styles.systemDecades} aria-hidden="true">
          {atlas.decades.map((decade, index) => {
            const angle = -126 + (index / Math.max(1, atlas.decades.length - 1)) * 252;
            const start = polarPoint(cx, cy, 334, angle);
            const end = polarPoint(cx, cy, index === selectedIndex ? 352 : 344, angle);
            return <g key={decade} data-active={index === selectedIndex}><line x1={start.x} y1={start.y} x2={end.x} y2={end.y} />{index % 4 === 0 || index === atlas.decades.length - 1 ? <text x={end.x} y={end.y - 6} textAnchor="middle">{decade}</text> : null}</g>;
          })}
        </g>

        <g className={styles.systemMediumArc}>
          {atlas.mediumGroups.map((medium, index) => {
            const span = 216 / atlas.mediumGroups.length;
            const start = -108 + index * span + 1.8;
            const end = -108 + (index + 1) * span - 1.8;
            const depth = logarithmicDepth(medium.count, maximumMedium, 7, 42);
            const labelPoint = polarPoint(cx, cy, 304 - depth / 2, (start + end) / 2);
            return <g key={medium.name} data-medium-index={index}><path d={bandPath(cx, cy, 304, 304 - depth, start, end)} /><text x={labelPoint.x} y={labelPoint.y + 3} textAnchor="middle">{medium.name.replace("graphic object / other", "graphic / other")} · {medium.count.toLocaleString()}</text><title>{medium.name}: {medium.count.toLocaleString()} active objects</title></g>;
          })}
        </g>

        <g className={styles.systemFamilyArc}>
          {FAMILY_ORDER.map((family, index) => {
            const start = -82 + index * 48;
            const end = start + 38;
            const depth = logarithmicDepth(familyTotals[family], maximumFamily, 8, 42);
            const labelPoint = polarPoint(cx, cy, 226 - depth / 2, (start + end) / 2);
            return <g key={family} data-family={family} data-empty={familyTotals[family] === 0}>{familyTotals[family] > 0 ? <path d={bandPath(cx, cy, 226, 226 - depth, start, end)} /> : null}<text x={labelPoint.x} y={labelPoint.y + 3} textAnchor="middle">{FAMILY_SHORT_LABELS[family]} · {familyTotals[family].toLocaleString()}</text><title>{FAMILY_LABELS[family]}: {familyTotals[family].toLocaleString()} documented edges</title></g>;
          })}
        </g>

        <g className={styles.systemCore}><circle cx={cx} cy={cy} r="118" /><text x={cx} y={cy - 36} textAnchor="middle">OBSERVED THROUGH</text><text x={cx} y={cy + 6} textAnchor="middle" data-year="true">{selectedDecade}</text><text x={cx} y={cy + 35} textAnchor="middle">{visibleTotal.toLocaleString()} ACTIVE OBJECTS</text><text x={cx} y={cy + 57} textAnchor="middle">{mode === "cumulative" ? "CUMULATIVE COVERAGE" : "SINGLE DECADE"}</text></g>

        <g className={styles.systemMap}>
          <path d={mapPath({ type: "Sphere" }) ?? undefined} data-sphere="true" />
          {countries.features.map((country, index) => <path key={`${String(country.id ?? "country")}-${index}`} d={mapPath(country) ?? undefined} />)}
          {regionMapPoints.map(({ row, point }, index) => {
            const count = row.counts[selectedIndex] ?? 0;
            const radius = count ? 3 + Math.sqrt(count / maximumMappedDecadeCount) * 10 : 2.4;
            const cell = { region: row.region, decade: selectedDecade, count };
            return (
              <g key={row.region} role="button" tabIndex={0} aria-label={`${row.region} map centroid: ${count.toLocaleString()} active objects in the ${selectedDecade}s`} onMouseEnter={() => onFocusCell(cell)} onFocus={() => onFocusCell(cell)} onClick={() => onActivate(cell)} onKeyDown={(event) => activate(event, () => onActivate(cell))}>
                <circle cx={point[0]} cy={point[1]} r={radius} data-active={row.region === selectedRegion} data-order={index} style={{ opacity: count ? 0.9 : 0.24 }} />
                <title>{row.region}: country-geometry centroid, {count.toLocaleString()} active objects in the {selectedDecade}s</title>
              </g>
            );
          })}
          {unmappedRegionRows.map((row, index) => {
            const count = row.counts[selectedIndex] ?? 0;
            const cell = { region: row.region, decade: selectedDecade, count };
            return (
              <g key={row.region} role="button" tabIndex={0} transform={`translate(286 ${690 + index * 72})`} data-unmapped="true" data-active={row.region === selectedRegion} aria-label={`${row.region}: non-coordinate aggregate, ${row.total.toLocaleString()} active objects across all decades and ${count.toLocaleString()} in the ${selectedDecade}s`} onMouseEnter={() => onFocusCell(cell)} onFocus={() => onFocusCell(cell)} onClick={() => onActivate(cell)} onKeyDown={(event) => activate(event, () => onActivate(cell))}>
                <rect width="270" height="58" rx="29" fill="#fff9ea" stroke="#252b28" />
                <circle cx="29" cy="29" r={9 + Math.sqrt(row.total / maximumRegion) * 8} data-active={row.region === selectedRegion} />
                <text x="58" y="35">{row.region} · {row.total.toLocaleString()}</text>
                <title>{row.region}: {row.total.toLocaleString()} active objects across all decades. This aggregate has no single geographic coordinate and is not plotted as a country.</title>
              </g>
            );
          })}
        </g>

        <g className={styles.systemFocus} transform="translate(40 684)"><rect width="274" height="154" /><text x="18" y="28">CURRENT OBSERVATION</text><text x="18" y="62" data-title="true">{focusCell.region}</text><text x="18" y="94" data-value="true">{focusCell.count.toLocaleString()}</text><text x="18" y="116">ACTIVE OBJECTS · {focusCell.decade}s</text><line x1="18" y1="132" x2="256" y2="132" /><text x="18" y="148">SELECT ARC OR MAP MARK</text></g>
        <g className={styles.systemFamilyScale} transform="translate(984 680)"><text x="0" y="0">DOCUMENTED EDGE VOLUME</text>{FAMILY_ORDER.map((family, index) => <g key={family} transform={`translate(0 ${22 + index * 34})`} data-family={family}><rect width={familyTotals[family] === 0 ? 0 : 24 + (familyTotals[family] / maximumFamily) * 220} height="12" /><text x="0" y="27">{FAMILY_LABELS[family]}</text><text x="260" y="11" textAnchor="end">{familyTotals[family].toLocaleString()}</text></g>)}</g>
      </svg>
    </div>
  );
}

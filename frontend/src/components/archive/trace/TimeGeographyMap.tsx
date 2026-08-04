"use client";

import {
  geoCentroid,
  geoEqualEarth,
  geoGraticule10,
  geoOrthographic,
  geoPath,
  type GeoProjection,
} from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import worldAtlas from "world-atlas/countries-50m.json";
import styles from "./TraceExplorer.module.css";
import {
  buildTraceMarks,
  selectionForEdge,
  tracePeerNode,
  traceTypeFor,
  type TraceSelection,
} from "./trace-taxonomy";
import type {
  ActiveCatalogItem,
  CompactPayload,
  TraceAtlas,
  TraceGraph,
} from "./trace-types";

type CountryProperties = { name: string };
type CountryFeature = Feature<Geometry, CountryProperties>;
type MapMode = "map" | "globe";
type TimeMode = "cumulative" | "decade";

type MappedRegion = {
  region: string;
  count: number;
  coordinates: [number, number];
  countries: string[];
};

const topology = worldAtlas as unknown as Topology;
const countries = feature(
  topology,
  topology.objects.countries as GeometryCollection<CountryProperties>,
) as FeatureCollection<Geometry, CountryProperties>;

const featureByName = new Map(
  countries.features
    .filter((country): country is CountryFeature => Boolean(country.properties?.name))
    .map((country) => [country.properties.name, country]),
);

const REGION_ALIASES: Record<string, string[]> = {
  "United States": ["United States of America"],
  "Aotearoa New Zealand": ["New Zealand"],
  "Australia / Indigenous": ["Australia"],
  "Bosnia and Herzegovina": ["Bosnia and Herz."],
  "Cape Verde": ["Cabo Verde"],
  "China / Hong Kong": ["China"],
  "Cook Islands": ["Cook Is."],
  "Cuba / transnational": ["Cuba"],
  "Czech Republic": ["Czechia"],
  "Democratic Republic of the Congo": ["Dem. Rep. Congo"],
  "Dominican Republic": ["Dominican Rep."],
  "Federated States of Micronesia": ["Micronesia"],
  "Hawaii": ["United States of America"],
  "Israel / Palestine": ["Israel", "Palestine"],
  "Korean Peninsula": ["North Korea", "South Korea"],
  "Marshall Islands": ["Marshall Is."],
  "Mexico City": ["Mexico"],
  "North Macedonia": ["Macedonia"],
  "Palestine / transnational": ["Palestine"],
  "Republic of the Congo": ["Congo"],
  "Solomon Islands": ["Solomon Is."],
  "Wallis and Futuna": ["Wallis and Futuna Is."],
  "Global / transnational": [],
  "Latin America": [],
  "Manchukuo": [],
  "Tokelau": [],
  "Yugoslavia": [],
};

function decodeCompact<T>(payload: CompactPayload): T[] {
  return payload.items.map((values) => {
    const result: Record<string, unknown> = {};
    payload.schema.forEach((field, index) => {
      const dictionary = payload.dictionaries[field];
      const value = values[index];
      result[field] = dictionary ? dictionary[Number(value)] : value;
    });
    return result as T;
  });
}

function resolveCountryNames(region: string) {
  if (region in REGION_ALIASES) return REGION_ALIASES[region];
  if (featureByName.has(region)) return [region];
  const suffix = region.split(",").at(-1)?.trim();
  if (suffix && suffix !== region) {
    const aliases = REGION_ALIASES[suffix] ?? [suffix];
    if (aliases.every((name) => featureByName.has(name))) return aliases;
  }
  return [];
}

function regionCentroid(countryNames: string[]): [number, number] | null {
  const features = countryNames
    .map((name) => featureByName.get(name))
    .filter((country): country is CountryFeature => Boolean(country));
  if (!features.length || features.length !== countryNames.length) return null;
  return geoCentroid({ type: "FeatureCollection", features });
}

function buildProjection(mode: MapMode, rotation: [number, number]): GeoProjection {
  if (mode === "globe") {
    return geoOrthographic()
      .translate([560, 286])
      .scale(245)
      .rotate([-rotation[0], -rotation[1]])
      .clipAngle(90)
      .precision(0.5);
  }
  return geoEqualEarth().fitExtent([[28, 24], [1092, 548]], countries);
}

function periodLabel(decade: number, timeMode: TimeMode) {
  return timeMode === "cumulative" ? `1800–${decade + 9}` : `${decade}–${decade + 9}`;
}

function externalProps(href: string) {
  return href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {};
}

export default function TimeGeographyMap({
  atlas,
  graph,
  selection,
  onSelect,
}: {
  atlas: TraceAtlas;
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  const [catalog, setCatalog] = useState<ActiveCatalogItem[] | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [mapMode, setMapMode] = useState<MapMode>("map");
  const [timeMode, setTimeMode] = useState<TimeMode>("cumulative");
  const objectDecade = Math.floor(graph.object.year / 10) * 10;
  const initialIndex = Math.max(0, atlas.decades.indexOf(objectDecade));
  const [decadeIndex, setDecadeIndex] = useState(initialIndex);
  const [playing, setPlaying] = useState(false);
  const [rotation, setRotation] = useState<[number, number]>([0, 5]);
  const [selectedRegion, setSelectedRegion] = useState(graph.object.region);
  const decade = atlas.decades[decadeIndex] ?? atlas.decades.at(-1) ?? 2020;

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    fetch(atlas.assets.catalog, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Active TRACE catalog unavailable (${response.status})`);
        return response.json() as Promise<CompactPayload>;
      })
      .then((payload) => {
        if (active) setCatalog(decodeCompact<ActiveCatalogItem>(payload));
      })
      .catch((cause: unknown) => {
        if (active && !controller.signal.aborted) {
          setCatalogError(cause instanceof Error ? cause.message : "Active TRACE catalog unavailable");
        }
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [atlas.assets.catalog]);

  useEffect(() => {
    setDecadeIndex(Math.max(0, atlas.decades.indexOf(Math.floor(graph.object.year / 10) * 10)));
    setSelectedRegion(graph.object.region);
    setPlaying(false);
  }, [atlas.decades, graph.object.id, graph.object.region, graph.object.year]);

  useEffect(() => {
    if (!playing) return;
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setPlaying(false);
      return;
    }
    const timer = window.setInterval(() => {
      setDecadeIndex((current) => {
        if (current >= atlas.decades.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 850);
    return () => window.clearInterval(timer);
  }, [atlas.decades.length, playing]);

  const distribution = useMemo(() => {
    const visible = (catalog ?? []).filter((item) => {
      const itemDecade = Math.floor(item.year / 10) * 10;
      return timeMode === "cumulative" ? itemDecade <= decade : itemDecade === decade;
    });
    const counts = new Map<string, number>();
    for (const item of visible) counts.set(item.region, (counts.get(item.region) ?? 0) + 1);

    const mapped: MappedRegion[] = [];
    let unmapped = 0;
    for (const [region, count] of counts) {
      const countryNames = resolveCountryNames(region);
      const coordinates = regionCentroid(countryNames);
      if (!coordinates) {
        unmapped += count;
        continue;
      }
      mapped.push({ region, count, coordinates, countries: countryNames });
    }
    mapped.sort((left, right) => right.count - left.count || left.region.localeCompare(right.region));
    return { mapped, unmapped, visible: visible.length };
  }, [catalog, decade, timeMode]);

  const selectedMapped = distribution.mapped.find((entry) => entry.region === selectedRegion)
    ?? distribution.mapped.find((entry) => entry.region === graph.object.region)
    ?? distribution.mapped[0];
  const maxCount = distribution.mapped[0]?.count ?? 1;
  const projection = useMemo(() => buildProjection(mapMode, rotation), [mapMode, rotation]);
  const path = geoPath(projection);
  const marks = buildTraceMarks(graph);
  const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
  const evidenceEdges = graph.edges.filter((edge) => edge.family === "time_place");
  const countryCounts = useMemo(() => {
    const result = new Map<string, number>();
    distribution.mapped.forEach((entry) => {
      entry.countries.forEach((country) => result.set(country, (result.get(country) ?? 0) + entry.count));
    });
    return result;
  }, [distribution.mapped]);
  const relatedRegions = selectedMapped
    ? distribution.mapped.filter((entry) => entry.region !== selectedMapped.region).slice(0, 3)
    : [];

  function togglePlayback() {
    if (!playing && decadeIndex >= atlas.decades.length - 1) setDecadeIndex(0);
    setPlaying((value) => !value);
  }

  function chooseRegion(entry: MappedRegion) {
    setSelectedRegion(entry.region);
    if (mapMode === "globe") setRotation(entry.coordinates);
  }

  return (
    <section className={`${styles.diagram} ${styles.geoDashboard}`} aria-labelledby="trace-geography-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>TIME / GEOGRAPHY ANALYSIS</p>
          <h3 id="trace-geography-title">Documented distribution through time</h3>
        </div>
        <span>Real country geometry · region-centroid aggregation · no object coordinate or influence is inferred</span>
      </div>

      <div className={styles.geoControlBar} aria-label="Time and geography view controls">
        <div className={styles.segmentedControl} aria-label="Map projection">
          <button type="button" aria-pressed={mapMode === "map"} onClick={() => setMapMode("map")}>World map</button>
          <button type="button" aria-pressed={mapMode === "globe"} onClick={() => setMapMode("globe")}>Globe</button>
        </div>
        <div className={styles.segmentedControl} aria-label="Time accumulation">
          <button type="button" aria-pressed={timeMode === "cumulative"} onClick={() => setTimeMode("cumulative")}>Development</button>
          <button type="button" aria-pressed={timeMode === "decade"} onClick={() => setTimeMode("decade")}>Single decade</button>
        </div>
        <p><b>{periodLabel(decade, timeMode)}</b><span>{catalog ? `${distribution.visible.toLocaleString()} active objects` : "Loading active distribution…"}</span></p>
      </div>

      <div className={styles.geoCanvas} data-map-mode={mapMode}>
        <svg
          className={styles.worldMapSvg}
          viewBox="0 0 1120 620"
          role="img"
          aria-labelledby="time-map-title time-map-desc"
        >
          <title id="time-map-title">Active design-object distribution for {periodLabel(decade, timeMode)}</title>
          <desc id="time-map-desc">
            Real Natural Earth country geometry displays active objects at normalized region aggregate centroids. Marker size represents object count. Dashed links show same-period regional co-presence only and are not TRACE or influence edges.
          </desc>
          <path className={styles.mapSphere} d={path({ type: "Sphere" }) ?? undefined} />
          <path className={styles.mapGraticule} d={path(geoGraticule10()) ?? undefined} />
          {countries.features.map((country, countryIndex) => {
            const name = country.properties?.name ?? "Unnamed geography";
            const count = countryCounts.get(name) ?? 0;
            return (
              <path
                key={`${String(country.id ?? name)}-${countryIndex}`}
                className={count ? `${styles.worldCountry} ${styles.worldCountryActive}` : styles.worldCountry}
                d={path(country) ?? undefined}
                style={{ "--country-intensity": `${Math.min(72, 10 + (count / maxCount) * 62)}%` } as CSSProperties}
                aria-hidden="true"
              />
            );
          })}

          {selectedMapped ? relatedRegions.map((entry) => (
            <path
              key={`context-${entry.region}`}
              className={styles.mapContextLink}
              d={path({ type: "LineString", coordinates: [selectedMapped.coordinates, entry.coordinates] }) ?? undefined}
            />
          )) : null}

          {distribution.mapped.map((entry, index) => {
            const point = projection(entry.coordinates);
            if (!point) return null;
            const selected = entry.region === selectedRegion;
            const radius = 3.5 + Math.sqrt(entry.count / maxCount) * 17;
            const code = `R${String(index + 1).padStart(2, "0")}`;
            return (
              <a
                key={entry.region}
                href={`/trace?region=${encodeURIComponent(entry.region)}&decade=${decade}`}
                aria-label={`${code}: ${entry.region}, ${entry.count.toLocaleString()} objects in ${periodLabel(decade, timeMode)}; aggregate country centroid`}
                data-selected={selected}
                onClick={(event) => {
                  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                  event.preventDefault();
                  chooseRegion(entry);
                }}
              >
                <circle className={styles.mapRegionPointHalo} cx={point[0]} cy={point[1]} r={radius + 5} />
                <circle className={styles.mapRegionPoint} cx={point[0]} cy={point[1]} r={radius} />
                {selected ? (
                  <>
                    <text className={styles.mapPointCode} x={point[0]} y={point[1] - radius - 10} textAnchor="middle">{code}</text>
                    <text className={styles.mapPointLabel} x={point[0]} y={point[1] + radius + 18} textAnchor="middle">{entry.region} · {entry.count.toLocaleString()}</text>
                  </>
                ) : null}
              </a>
            );
          })}

          <g className={styles.mapLegend} transform="translate(28 568)">
            <circle cx="5" cy="0" r="5" /><text x="18" y="4">region aggregate centroid</text>
            <path d="M 220 0 H 270" /><text x="282" y="4">same-period co-presence, not influence</text>
          </g>
        </svg>

        <aside className={styles.geoReadout} aria-live="polite">
          <p>Selected region</p>
          <h4>{selectedMapped?.region ?? graph.object.region}</h4>
          <dl>
            <div><dt>Mapped objects</dt><dd>{distribution.mapped.reduce((sum, entry) => sum + entry.count, 0).toLocaleString()}</dd></div>
            <div><dt>Not mapped</dt><dd>{distribution.unmapped.toLocaleString()}</dd></div>
            <div><dt>Regions shown</dt><dd>{distribution.mapped.length}</dd></div>
            <div><dt>Selected count</dt><dd>{selectedMapped?.count.toLocaleString() ?? "—"}</dd></div>
          </dl>
          <p className={styles.geoReadoutNote}>Coordinates are calculated from country geometry. They are not asserted object production locations.</p>
        </aside>
      </div>

      <div className={styles.timeController}>
        <button type="button" onClick={togglePlayback} aria-label={playing ? "Pause time animation" : "Play time animation"}>
          {playing ? "Pause" : "Play"}
        </button>
        <label>
          <span>Recorded time · {periodLabel(decade, timeMode)}</span>
          <input
            type="range"
            min="0"
            max={atlas.decades.length - 1}
            step="1"
            value={decadeIndex}
            onChange={(event) => {
              setPlaying(false);
              setDecadeIndex(Number(event.target.value));
            }}
          />
        </label>
        <div className={styles.timelineTicks} aria-hidden="true">
          {atlas.decades.map((value, index) => <i key={value} style={{ left: `${(index / (atlas.decades.length - 1)) * 100}%` }}>{index % 5 === 0 || index === atlas.decades.length - 1 ? value : ""}</i>)}
        </div>
      </div>

      {catalogError ? <p className={styles.mapDataError}>{catalogError}</p> : null}
      <p className={styles.mobileDiagramNote}>Use the map controls and timeline first; open the information drawer for normalized evidence rows.</p>
      <div className={`${styles.stationIndex} ${styles.stationIndexSingle} ${styles.diagramEvidenceFallback}`} aria-label="Time and geography evidence index">
        <section data-family="time_place">
          <h4><span>TG</span>Object time / geography evidence</h4>
          {evidenceEdges.length ? (
            <ol>
              {evidenceEdges.map((edge) => {
                const peer = tracePeerNode(edge, graph.object.nodeId, nodes);
                const href = peer?.href || edge.evidenceUrl;
                const edgeSelection = selectionForEdge(graph, edge);
                return (
                  <li key={edge.id} data-selected={selection?.edgeId === edge.id}>
                    <button type="button" onClick={() => onSelect(edgeSelection)}>{marks.nodeMarks.get(edgeSelection.nodeId)}</button>
                    <span>
                      <a href={href} {...externalProps(href)}>{peer?.label || edge.label}</a>
                      <small>{marks.edgeMarks.get(edge.id)} · {edge.direction} · {traceTypeFor(edge.label).code} · {edge.reviewState.replaceAll("_", " ")}</small>
                    </span>
                  </li>
                );
              })}
            </ol>
          ) : <p>No documented date or place evidence in this object view.</p>}
        </section>
      </div>
    </section>
  );
}

"use client";

import { geoEqualEarth, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import worldAtlas from "world-atlas/countries-110m.json";
import styles from "./TraceExplorer.module.css";
import type { TraceEdge, TraceGraph, TraceNode } from "./trace-types";

type CountryProperties = { name: string };

const topology = worldAtlas as unknown as Topology;
const countries = feature(
  topology,
  topology.objects.countries as GeometryCollection<CountryProperties>,
) as FeatureCollection<Geometry, CountryProperties>;
const projection = geoEqualEarth().fitExtent([[28, 22], [1092, 446]], countries);
const path = geoPath(projection);

const REGION_ALIASES: Record<string, string[]> = {
  "United States": ["United States of America"],
  "Aotearoa New Zealand": ["New Zealand"],
  "Australia / Indigenous": ["Australia"],
  "China / Hong Kong": ["China"],
  "Cuba / transnational": ["Cuba"],
  "Palestine / transnational": ["Palestine"],
  "Israel / Palestine": ["Israel", "Palestine"],
  "Korean Peninsula": ["North Korea", "South Korea"],
  "Bosnia and Herzegovina": ["Bosnia and Herz."],
  "Czech Republic": ["Czechia"],
  "Democratic Republic of the Congo": ["Dem. Rep. Congo"],
  "Dominican Republic": ["Dominican Rep."],
  "Eswatini": ["eSwatini"],
  "North Macedonia": ["Macedonia"],
  "Solomon Islands": ["Solomon Is."],
  "Federated States of Micronesia": [],
  "Wallis and Futuna": [],
  "Global / transnational": [],
  "Latin America": [
    "Mexico", "Guatemala", "Belize", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama",
    "Cuba", "Dominican Rep.", "Haiti", "Colombia", "Venezuela", "Guyana", "Suriname", "Ecuador", "Peru",
    "Bolivia", "Brazil", "Paraguay", "Uruguay", "Argentina", "Chile",
  ],
};

const MIN_YEAR = 1800;
const MAX_YEAR = 2030;
const TIMELINE_TICKS = [1800, 1850, 1900, 1950, 2000, 2030];

function targetCountryNames(region: string) {
  if (region in REGION_ALIASES) return REGION_ALIASES[region];
  return region
    .split(/\s*\/\s*/)
    .filter((part) => part && part.toLocaleLowerCase() !== "transnational")
    .flatMap((part) => REGION_ALIASES[part] ?? [part]);
}

function peerNode(edge: TraceEdge, rootId: string, nodes: Map<string, TraceNode>) {
  if (edge.subject === rootId) return nodes.get(edge.object);
  if (edge.object === rootId) return nodes.get(edge.subject);
  return nodes.get(edge.object) ?? nodes.get(edge.subject);
}

function externalProps(href: string) {
  return href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {};
}

function timelineX(year: number) {
  const clamped = Math.min(MAX_YEAR, Math.max(MIN_YEAR, year));
  return 70 + ((clamped - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 980;
}

export default function TimeGeographyMap({ graph }: { graph: TraceGraph }) {
  const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
  const edges = graph.edges.filter((edge) => edge.family === "time_place");
  const targets = new Set(targetCountryNames(graph.object.region));
  const matchedTargets = new Set(
    countries.features
      .map((country) => country.properties?.name)
      .filter((name): name is string => Boolean(name && targets.has(name))),
  );
  const year = graph.object.year;
  const mapState = matchedTargets.size
    ? `${Array.from(matchedTargets).join(" + ")} highlighted from normalized object geography`
    : `${graph.object.region} remains a non-point regional category; no country outline is inferred`;

  return (
    <section className={styles.diagram} aria-labelledby="trace-geography-title">
      <div className={styles.diagramHeading}>
        <div>
          <p>TIME / GEOGRAPHY MAP</p>
          <h3 id="trace-geography-title">Recorded place and date</h3>
        </div>
        <span>{graph.object.region} · {year} · country fill is not a coordinate claim</span>
      </div>

      <div className={styles.diagramDesktop}>
        <svg
          className={styles.worldMapSvg}
          viewBox="0 0 1120 610"
          role="img"
          aria-labelledby="time-map-title time-map-desc"
        >
          <title id="time-map-title">Time and geography map for {graph.object.title}</title>
          <desc id="time-map-desc">
            A Natural Earth country map highlights only the normalized object region when it resolves to a country outline. A shared 1800 to 2030 axis marks the recorded object year. No object coordinate, travel path, diffusion or influence is inferred.
          </desc>
          <path className={styles.mapSphere} d={path({ type: "Sphere" }) ?? undefined} />
          {countries.features.map((country) => {
            const name = country.properties?.name ?? "Unnamed geography";
            const highlighted = matchedTargets.has(name);
            return (
              <path
                key={String(country.id ?? name)}
                className={highlighted ? `${styles.worldCountry} ${styles.worldCountryHighlighted}` : styles.worldCountry}
                d={path(country) ?? undefined}
                data-highlighted={highlighted}
                aria-hidden="true"
              />
            );
          })}
          <text className={styles.mapRegionLabel} x="42" y="476">{mapState}</text>

          <line className={styles.mapTimeline} x1="70" y1="548" x2="1050" y2="548" />
          {TIMELINE_TICKS.map((tick) => {
            const x = timelineX(tick);
            return (
              <g key={tick}>
                <line className={styles.mapTick} x1={x} y1="538" x2={x} y2="558" />
                <text className={styles.mapTickLabel} x={x} y="584" textAnchor="middle">{tick}</text>
              </g>
            );
          })}
          <circle className={styles.mapYearMarker} cx={timelineX(year)} cy="548" r="11" />
          <text className={styles.mapYearLabel} x={timelineX(year)} y="522" textAnchor="middle">{year}</text>
        </svg>
      </div>

      <p className={styles.mobileDiagramNote}>
        Mobile view: {mapState}. Recorded year: {year}.
      </p>
      <div
        className={`${styles.stationIndex} ${styles.stationIndexSingle} ${styles.diagramEvidenceFallback}`}
        aria-label="Time and geography evidence index"
      >
        <section>
          <h4><span>G</span>Time / geography</h4>
          {edges.length ? (
            <ol>
              {edges.map((edge, index) => {
                const peer = peerNode(edge, graph.object.nodeId, nodes);
                const href = peer?.href || edge.evidenceUrl;
                return (
                  <li key={edge.id}>
                    <b>G{index + 1}</b>
                    <span>
                      <a href={href} {...externalProps(href)}>{peer?.label || edge.label}</a>
                      <small>{edge.direction} · {edge.label.replaceAll("_", " ")} · {edge.reviewState.replaceAll("_", " ")}</small>
                    </span>
                  </li>
                );
              })}
            </ol>
          ) : <p>No documented date or place evidence in this view.</p>}
        </section>
      </div>
    </section>
  );
}

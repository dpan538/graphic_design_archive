"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./TraceExplorer.module.css";
import type {
  ActiveCatalogItem,
  AtlasRegion,
  CompactPayload,
  TraceAtlas,
} from "./trace-types";

type TimeMode = "cumulative" | "decade";

interface ObservationCell {
  region: string;
  decade: number;
  count: number;
}

const MEDIUM_COLORS = [
  "#68859a",
  "#c56f59",
  "#687e62",
  "#79739b",
  "#76b9b1",
  "#b99b5b",
  "#98849d",
];

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

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return {
    x: cx + Math.cos(radians) * radius,
    y: cy + Math.sin(radians) * radius,
  };
}

function linePath(values: number[], width: number, height: number, inset: number, maximum: number) {
  return values.map((value, index) => {
    const x = inset + (index / Math.max(1, values.length - 1)) * (width - inset * 2);
    const y = height - inset - (value / Math.max(1, maximum)) * (height - inset * 2);
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

function areaPath(
  lower: number[],
  upper: number[],
  width: number,
  height: number,
  inset: number,
  maximum: number,
) {
  const top = upper.map((value, index) => {
    const x = inset + (index / Math.max(1, upper.length - 1)) * (width - inset * 2);
    const y = height - inset - (value / Math.max(1, maximum)) * (height - inset * 2);
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  });
  const bottom = lower.map((value, index) => {
    const reverseIndex = lower.length - index - 1;
    const x = inset + (reverseIndex / Math.max(1, lower.length - 1)) * (width - inset * 2);
    const y = height - inset - (lower[reverseIndex] / Math.max(1, maximum)) * (height - inset * 2);
    return `L${x.toFixed(2)},${y.toFixed(2)}`;
  });
  return `${top.join(" ")} ${bottom.join(" ")} Z`;
}

function activateCell(
  event: React.KeyboardEvent<SVGCircleElement>,
  cell: ObservationCell,
  onActivate: (cell: ObservationCell) => void,
) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onActivate(cell);
  }
}

function RadialObservationField({
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
  focusCell: ObservationCell;
  onFocusCell: (cell: ObservationCell) => void;
  onActivate: (cell: ObservationCell) => void;
}) {
  const size = 760;
  const center = size / 2;
  const innerRadius = 70;
  const outerRadius = 282;
  const maximum = Math.max(...atlas.regionMatrix.flatMap((row) => row.counts));
  const selectedDecade = atlas.decades[selectedIndex];
  const visibleTotal = mode === "cumulative"
    ? atlas.decadeTotals.slice(0, selectedIndex + 1).reduce((sum, count) => sum + count, 0)
    : atlas.decadeTotals[selectedIndex];

  return (
    <svg
      className={styles.evolutionRadial}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-labelledby="evolution-field-title evolution-field-desc"
    >
      <title id="evolution-field-title">Observed geographic expansion field</title>
      <desc id="evolution-field-desc">
        Concentric rings are decades from 1800 to 2020. Radial axes are normalized object regions.
        Point area is a log-scaled active-object count. Outer ticks are documented TRACE relation types.
      </desc>
      <defs>
        <radialGradient id="evolution-field-wash" cx="50%" cy="47%" r="58%">
          <stop offset="0%" stopColor="#7657ba" stopOpacity="0.5" />
          <stop offset="38%" stopColor="#3f7580" stopOpacity="0.3" />
          <stop offset="76%" stopColor="#272d2c" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#272d2c" stopOpacity="0" />
        </radialGradient>
        <filter id="evolution-focus-glow" x="-120%" y="-120%" width="340%" height="340%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <circle cx={center} cy={center} r="338" className={styles.evolutionFieldBoundary} />
      <circle cx={center} cy={center} r="314" fill="url(#evolution-field-wash)" />

      {atlas.decades.map((decade, index) => {
        const radius = innerRadius + (index / Math.max(1, atlas.decades.length - 1)) * (outerRadius - innerRadius);
        const isSelected = index === selectedIndex;
        return (
          <g key={decade}>
            <circle
              cx={center}
              cy={center}
              r={radius}
              className={styles.evolutionDecadeRing}
              data-selected={isSelected}
              data-visible={index <= selectedIndex}
            />
            {(index % 4 === 0 || index === atlas.decades.length - 1) ? (
              <text x={center + 5} y={center - radius + 1} className={styles.evolutionDecadeLabel}>
                {decade}
              </text>
            ) : null}
          </g>
        );
      })}

      {atlas.regionMatrix.map((row, regionIndex) => {
        const angle = (regionIndex / atlas.regionMatrix.length) * 360;
        const rayStart = polarPoint(center, center, innerRadius - 10, angle);
        const rayEnd = polarPoint(center, center, outerRadius + 18, angle);
        const labelPoint = polarPoint(center, center, outerRadius + 31, angle);
        const labelAnchor = labelPoint.x < center - 8 ? "end" : labelPoint.x > center + 8 ? "start" : "middle";
        return (
          <g key={row.region} data-region-active={row.region === selectedRegion}>
            <line
              x1={rayStart.x}
              y1={rayStart.y}
              x2={rayEnd.x}
              y2={rayEnd.y}
              className={styles.evolutionRegionRay}
            />
            <text
              x={labelPoint.x}
              y={labelPoint.y}
              textAnchor={labelAnchor}
              className={styles.evolutionRegionLabel}
            >
              {row.region.length > 17 ? `${row.region.slice(0, 15)}…` : row.region}
            </text>
            {row.counts.map((count, decadeIndex) => {
              if (!count) return null;
              const radius = innerRadius + (decadeIndex / Math.max(1, atlas.decades.length - 1)) * (outerRadius - innerRadius);
              const position = polarPoint(center, center, radius, angle);
              const cell = { region: row.region, decade: atlas.decades[decadeIndex], count };
              const isFocused = focusCell.region === row.region && focusCell.decade === cell.decade;
              const isVisible = mode === "cumulative" ? decadeIndex <= selectedIndex : decadeIndex === selectedIndex;
              const markRadius = 2.5 + (Math.log1p(count) / Math.log1p(maximum)) * 8.5;
              return (
                <circle
                  key={cell.decade}
                  cx={position.x}
                  cy={position.y}
                  r={markRadius}
                  role="button"
                  tabIndex={0}
                  aria-label={`${row.region}, ${cell.decade}s: ${count.toLocaleString()} active objects. Open filtered object list.`}
                  className={styles.evolutionCell}
                  data-visible={isVisible}
                  data-selected={isFocused}
                  data-region-active={row.region === selectedRegion}
                  style={{ ["--evolution-order" as string]: decadeIndex }}
                  onMouseEnter={() => onFocusCell(cell)}
                  onFocus={() => onFocusCell(cell)}
                  onClick={() => onActivate(cell)}
                  onKeyDown={(event) => activateCell(event, cell, onActivate)}
                />
              );
            })}
          </g>
        );
      })}

      {atlas.relationTypes.map((relation, index) => {
        const angle = (index / atlas.relationTypes.length) * 360;
        const start = polarPoint(center, center, 319, angle);
        const length = 8 + (Math.log1p(relation.count) / Math.log1p(atlas.relationTypes[0]?.count ?? 1)) * 30;
        const end = polarPoint(center, center, 319 + length, angle);
        return (
          <line
            key={relation.label}
            x1={start.x}
            y1={start.y}
            x2={end.x}
            y2={end.y}
            className={styles.evolutionRelationTick}
            data-family={relation.family}
          >
            <title>{relation.label.replaceAll("_", " ")}: {relation.count.toLocaleString()} documented edges</title>
          </line>
        );
      })}

      <circle cx={center} cy={center} r="55" className={styles.evolutionCore} />
      <text x={center} y={center - 14} textAnchor="middle" className={styles.evolutionCoreLabel}>
        {mode === "cumulative" ? "THROUGH" : "DECADE"}
      </text>
      <text x={center} y={center + 8} textAnchor="middle" className={styles.evolutionCoreYear}>
        {selectedDecade}
      </text>
      <text x={center} y={center + 29} textAnchor="middle" className={styles.evolutionCoreCount}>
        {visibleTotal.toLocaleString()} OBJECTS
      </text>
    </svg>
  );
}

export default function ChronogeographicRoutes({
  atlas,
  exploreCell,
}: {
  atlas: TraceAtlas;
  exploreCell: (row: AtlasRegion, decade: number) => void;
}) {
  const lastIndex = atlas.decades.length - 1;
  const [selectedIndex, setSelectedIndex] = useState(lastIndex);
  const [selectedRegion, setSelectedRegion] = useState(
    atlas.regionMatrix.find((row) => (row.counts.at(-1) ?? 0) > 0)?.region
      ?? atlas.regionMatrix[0]?.region
      ?? "",
  );
  const [timeMode, setTimeMode] = useState<TimeMode>("cumulative");
  const [playing, setPlaying] = useState(false);
  const [catalog, setCatalog] = useState<ActiveCatalogItem[] | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [hoveredCell, setHoveredCell] = useState<ObservationCell | null>(null);
  const storyRef = useRef<HTMLDivElement>(null);
  const selectedDecade = atlas.decades[selectedIndex];
  const selectedRow = atlas.regionMatrix.find((row) => row.region === selectedRegion) ?? atlas.regionMatrix[0];
  const selectedCount = selectedRow?.counts[selectedIndex] ?? 0;
  const focusCell = hoveredCell ?? { region: selectedRegion, decade: selectedDecade, count: selectedCount };
  const maximum = Math.max(...atlas.regionMatrix.flatMap((row) => row.counts));
  const gridStyle = { ["--trace-decades" as string]: String(atlas.decades.length) };

  useEffect(() => {
    const controller = new AbortController();
    fetch(atlas.assets.catalog, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Active TRACE catalog unavailable (${response.status})`);
        return response.json() as Promise<CompactPayload>;
      })
      .then((payload) => setCatalog(decodeCompact<ActiveCatalogItem>(payload)))
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setCatalogError(cause instanceof Error ? cause.message : "Active TRACE catalog unavailable");
        }
      });
    return () => controller.abort();
  }, [atlas.assets.catalog]);

  useEffect(() => {
    if (!playing) return;
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setPlaying(false);
      return;
    }
    const timer = window.setInterval(() => {
      setSelectedIndex((current) => {
        if (current >= lastIndex) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 720);
    return () => window.clearInterval(timer);
  }, [lastIndex, playing]);

  useEffect(() => {
    const story = storyRef.current;
    if (!story) return;
    const chapters = Array.from(story.querySelectorAll<HTMLElement>("[data-evolution-decade]"));
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      const decade = Number((visible?.target as HTMLElement | undefined)?.dataset.evolutionDecade);
      const index = atlas.decades.indexOf(decade);
      if (index >= 0) setSelectedIndex(index);
    }, { threshold: [0.25, 0.5, 0.75], rootMargin: "-24% 0px -42% 0px" });
    chapters.forEach((chapter) => observer.observe(chapter));
    return () => observer.disconnect();
  }, [atlas.decades]);

  const mediumMatrix = useMemo(() => {
    const rows = atlas.mediumGroups.map(() => atlas.decades.map(() => 0));
    if (!catalog) return rows;
    const mediumIndex = new Map(atlas.mediumGroups.map((item, index) => [item.name, index]));
    const decadeIndex = new Map(atlas.decades.map((decade, index) => [decade, index]));
    for (const item of catalog) {
      const rowIndex = mediumIndex.get(item.mediumGroup);
      const columnIndex = decadeIndex.get(Math.floor(item.year / 10) * 10);
      if (rowIndex !== undefined && columnIndex !== undefined) rows[rowIndex][columnIndex] += 1;
    }
    return rows;
  }, [atlas.decades, atlas.mediumGroups, catalog]);

  const stackedLayers = useMemo(() => {
    const lower = atlas.decades.map(() => 0);
    return mediumMatrix.map((counts, index) => {
      const base = [...lower];
      counts.forEach((count, decadeIndex) => { lower[decadeIndex] += count; });
      return {
        name: atlas.mediumGroups[index].name,
        color: MEDIUM_COLORS[index % MEDIUM_COLORS.length],
        lower: base,
        upper: [...lower],
        counts,
      };
    });
  }, [atlas.decades, atlas.mediumGroups, mediumMatrix]);

  const visibleTotal = timeMode === "cumulative"
    ? atlas.decadeTotals.slice(0, selectedIndex + 1).reduce((sum, count) => sum + count, 0)
    : atlas.decadeTotals[selectedIndex];
  const dominantRegions = atlas.regionMatrix
    .map((row) => ({ row, count: row.counts[selectedIndex] }))
    .filter((item) => item.count)
    .sort((a, b) => b.count - a.count)
    .slice(0, 4);
  const selectedMediumCounts = stackedLayers
    .map((layer) => ({ name: layer.name, color: layer.color, count: layer.counts[selectedIndex] }))
    .filter((item) => item.count)
    .sort((a, b) => b.count - a.count);
  const milestones = atlas.decades.filter((_, index) => index === 0 || index === lastIndex || index % 4 === 0);

  function activateObservation(cell: ObservationCell) {
    const row = atlas.regionMatrix.find((candidate) => candidate.region === cell.region);
    if (row) exploreCell(row, cell.decade);
  }

  function togglePlayback() {
    if (!playing && selectedIndex >= lastIndex) setSelectedIndex(0);
    setPlaying((value) => !value);
  }

  return (
    <section className={styles.chronoRoutes} aria-labelledby="chrono-routes-title">
      <header className={styles.chronoHeading}>
        <div>
          <p>OBSERVED EVOLUTION / VERIFIED OBJECT GEOGRAPHY</p>
          <h3 id="chrono-routes-title">Archive evolution field</h3>
        </div>
        <p>
          The field visualizes changing archive coverage. It does not claim geographic diffusion,
          cultural continuity or historical influence.
        </p>
      </header>

      <div className={styles.evolutionControls} aria-label="Evolution field controls">
        <button type="button" onClick={togglePlayback} aria-label={playing ? "Pause decade animation" : "Play decade animation"}>
          {playing ? "Pause" : "Play"}
        </button>
        <div className={styles.segmentedControl} aria-label="Time aggregation">
          <button type="button" aria-pressed={timeMode === "cumulative"} onClick={() => setTimeMode("cumulative")}>Development</button>
          <button type="button" aria-pressed={timeMode === "decade"} onClick={() => setTimeMode("decade")}>Single decade</button>
        </div>
        <label>
          Focus region
          <select value={selectedRegion} onChange={(event) => setSelectedRegion(event.target.value)}>
            {atlas.regionMatrix.map((row) => <option key={row.region} value={row.region}>{row.region}</option>)}
          </select>
        </label>
        <label className={styles.evolutionRange}>
          <span>{atlas.decades[0]}</span>
          <input
            type="range"
            min={0}
            max={lastIndex}
            value={selectedIndex}
            aria-label="Selected evolution decade"
            onChange={(event) => {
              setPlaying(false);
              setSelectedIndex(Number(event.target.value));
            }}
          />
          <span>{atlas.decades[lastIndex]}</span>
        </label>
      </div>

      <div className={styles.evolutionStory} ref={storyRef}>
        <div className={styles.evolutionStage}>
          <div className={styles.evolutionPlate}>
            <div className={styles.evolutionPlateMeta} aria-hidden="true">
              <span>15 REGION AXES</span><span>23 DECADE RINGS</span><span>LOG AREA</span>
            </div>
            <RadialObservationField
              atlas={atlas}
              selectedIndex={selectedIndex}
              selectedRegion={selectedRegion}
              mode={timeMode}
              focusCell={focusCell}
              onFocusCell={setHoveredCell}
              onActivate={activateObservation}
            />
            <div className={styles.evolutionPlateLegend}>
              <span><i />Recorded object count</span>
              <span><i />Selected region / decade</span>
              <span><i />Documented relation vocabulary</span>
            </div>
          </div>

          <aside className={styles.evolutionReadout} aria-live="polite">
            <p>Current observation</p>
            <h4>{focusCell.region}</h4>
            <strong>{focusCell.decade}s</strong>
            <dl>
              <div><dt>Cell count</dt><dd>{focusCell.count.toLocaleString()}</dd></div>
              <div><dt>{timeMode === "cumulative" ? "Visible through" : "Decade total"}</dt><dd>{visibleTotal.toLocaleString()}</dd></div>
              <div><dt>TRACE edges</dt><dd>{atlas.counts.traceEdges.toLocaleString()}</dd></div>
              <div><dt>Influence edges</dt><dd>{atlas.counts.influenceEdges}</dd></div>
            </dl>
            <button type="button" onClick={() => activateObservation(focusCell)} disabled={!focusCell.count}>
              Open matching objects
            </button>
            <p className={styles.evolutionCaution}>Every point is an aggregate observation. Position does not encode an inferred causal route.</p>
          </aside>
        </div>

        <ol className={styles.evolutionChapters} aria-label="Scroll through archive development">
          {milestones.map((decade) => {
            const index = atlas.decades.indexOf(decade);
            const leaders = atlas.regionMatrix
              .map((row) => ({ region: row.region, count: row.counts[index] }))
              .filter((item) => item.count)
              .sort((a, b) => b.count - a.count)
              .slice(0, 3);
            const cumulative = atlas.decadeTotals.slice(0, index + 1).reduce((sum, count) => sum + count, 0);
            return (
              <li key={decade} data-evolution-decade={decade}>
                <article>
                  <span>{String(index + 1).padStart(2, "0")} / {atlas.decades.length}</span>
                  <h4>{decade}s</h4>
                  <p>{atlas.decadeTotals[index].toLocaleString()} active records · {cumulative.toLocaleString()} observed through this ring</p>
                  <ul>{leaders.map((item) => <li key={item.region}><span>{item.region}</span><b>{item.count.toLocaleString()}</b></li>)}</ul>
                </article>
              </li>
            );
          })}
        </ol>
      </div>

      <section className={styles.evolutionLandscape} aria-labelledby="evolution-landscape-title">
        <header>
          <div>
            <p>MEDIUM STRATA / 1800–2020</p>
            <h4 id="evolution-landscape-title">Recorded medium landscape</h4>
          </div>
          <p>Stacked bands are exact catalog counts by decade and display-only medium group.</p>
        </header>
        <div className={styles.evolutionLandscapeCanvas}>
          <svg viewBox="0 0 1200 430" role="img" aria-labelledby="medium-landscape-title medium-landscape-desc">
            <title id="medium-landscape-title">Medium group counts through time</title>
            <desc id="medium-landscape-desc">Stacked area bands show active object counts by medium group and decade. A white line shows the selected region.</desc>
            <defs>
              <linearGradient id="landscape-field" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#213235" />
                <stop offset="55%" stopColor="#29242f" />
                <stop offset="100%" stopColor="#272d2c" />
              </linearGradient>
              <filter id="landscape-soft-glow" x="-20%" y="-40%" width="140%" height="180%">
                <feGaussianBlur stdDeviation="6" />
              </filter>
            </defs>
            <rect width="1200" height="430" fill="url(#landscape-field)" />
            {atlas.decades.map((decade, index) => {
              const x = 42 + (index / lastIndex) * 1116;
              return (
                <g key={decade}>
                  <line x1={x} y1="28" x2={x} y2="390" className={styles.evolutionLandscapeGrid} data-selected={index === selectedIndex} />
                  {(index % 2 === 0 || index === lastIndex) ? <text x={x} y="414" textAnchor="middle" className={styles.evolutionLandscapeAxis}>{decade}</text> : null}
                </g>
              );
            })}
            {stackedLayers.map((layer, index) => (
              <path
                key={layer.name}
                d={areaPath(layer.lower, layer.upper, 1200, 430, 42, Math.max(...atlas.decadeTotals))}
                fill={layer.color}
                fillOpacity={0.42 + index * 0.055}
                className={styles.evolutionLandscapeLayer}
              >
                <title>{layer.name}</title>
              </path>
            ))}
            <path
              d={linePath(selectedRow?.counts ?? atlas.decadeTotals.map(() => 0), 1200, 430, 42, Math.max(...selectedRow?.counts ?? [1]))}
              className={styles.evolutionRegionProfileGlow}
              filter="url(#landscape-soft-glow)"
            />
            <path
              d={linePath(selectedRow?.counts ?? atlas.decadeTotals.map(() => 0), 1200, 430, 42, Math.max(...selectedRow?.counts ?? [1]))}
              className={styles.evolutionRegionProfile}
            />
            <line
              x1={42 + (selectedIndex / lastIndex) * 1116}
              y1="24"
              x2={42 + (selectedIndex / lastIndex) * 1116}
              y2="392"
              className={styles.evolutionCursor}
            />
            {atlas.decades.map((decade, index) => {
              const x = 42 + (index / lastIndex) * 1116;
              return (
                <rect
                  key={decade}
                  x={x - 24}
                  y="20"
                  width="48"
                  height="378"
                  role="button"
                  tabIndex={0}
                  aria-label={`${decade}s: ${atlas.decadeTotals[index].toLocaleString()} active objects`}
                  className={styles.evolutionLandscapeTarget}
                  onMouseEnter={() => setSelectedIndex(index)}
                  onFocus={() => setSelectedIndex(index)}
                  onClick={() => setSelectedIndex(index)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelectedIndex(index);
                    }
                  }}
                />
              );
            })}
          </svg>
          {!catalog ? <p className={styles.evolutionLoading}>{catalogError || "Loading exact medium strata…"}</p> : null}
        </div>
        <div className={styles.evolutionLandscapeFooter}>
          <ul>{selectedMediumCounts.map((item) => <li key={item.name}><i style={{ background: item.color }} /><span>{item.name}</span><b>{item.count.toLocaleString()}</b></li>)}</ul>
          <p><span>{selectedRegion}</span><b>{selectedCount.toLocaleString()}</b> active objects in the {selectedDecade}s</p>
        </div>
      </section>

      <header className={`${styles.chronoHeading} ${styles.chronoHeadingSecondary}`}>
        <div><p>EXACT LEDGER / REGION × DECADE</p><h3>Chronogeographic observation routes</h3></div>
        <p>Region rails are categorical axes. Only stations denote records; connecting rails do not assert continuity.</p>
      </header>
      <div className={styles.chronoDesktop}>
        <div className={styles.chronoAxisRow}>
          <span>Object geography</span>
          <div className={styles.chronoAxis} style={gridStyle} aria-hidden="true">
            {atlas.decades.map((decade) => <span key={decade}>{decade}</span>)}
          </div>
          <span>Total</span>
        </div>
        {atlas.regionMatrix.map((row) => (
          <div className={styles.chronoRow} key={row.region}>
            <strong>{row.region}</strong>
            <div className={styles.chronoRail} style={gridStyle}>
              {row.counts.map((count, index) => (
                <span className={styles.chronoCell} key={atlas.decades[index]}>
                  {count ? (
                    <button
                      type="button"
                      className={styles.chronoStation}
                      style={{
                        ["--station-size" as string]: `${Math.round(
                          11 + (Math.log1p(count) / Math.log1p(maximum)) * 15,
                        )}px`,
                      }}
                      aria-label={`${row.region}, ${atlas.decades[index]}s: ${count} active objects. Open filtered object list.`}
                      onClick={() => exploreCell(row, atlas.decades[index])}
                    >
                      <span className={styles.srOnly}>{count.toLocaleString()}</span>
                    </button>
                  ) : <i aria-hidden="true" />}
                </span>
              ))}
            </div>
            <b>{row.total.toLocaleString()}</b>
          </div>
        ))}
      </div>
      <div className={styles.chronoLegend}>
        <span><i className={styles.legendRail} />Normalized region rail</span>
        <span><i className={styles.legendStation} />Recorded objects; area uses log-scaled count</span>
        <span><i className={styles.legendGap} />No active record in that decade</span>
      </div>
    </section>
  );
}

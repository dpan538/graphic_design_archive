"use client";

import { useMemo, useState } from "react";
import styles from "./TraceExplorer.module.css";
import type {
  AtlasRelation,
  AtlasTreeCount,
  RelationFamily,
  TraceAtlas,
} from "./trace-types";

type FocusRecord =
  | { kind: "tree"; key: string; item: AtlasTreeCount; rank: number }
  | { kind: "relation"; key: string; item: AtlasRelation; rank: number };

const FAMILY_LABELS: Record<RelationFamily, string> = {
  source_provenance: "Source / provenance",
  time_place: "Time / place",
  medium_context: "Medium / context",
  historical_influence: "Historical influence",
};

const THRESHOLDS = [
  { value: 1, label: "All 30 trees" },
  { value: 25, label: "25+ members" },
  { value: 100, label: "100+ members" },
] as const;

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return {
    x: cx + Math.cos(radians) * radius,
    y: cy + Math.sin(radians) * radius,
  };
}

function arcPath(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarPoint(cx, cy, radius, startAngle);
  const end = polarPoint(cx, cy, radius, endAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
}

function activate(
  event: React.KeyboardEvent<SVGGElement>,
  record: FocusRecord,
  onFocusRecord: (record: FocusRecord) => void,
) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onFocusRecord(record);
  }
}

export default function TraceConstellation({ atlas }: { atlas: TraceAtlas }) {
  const [minimum, setMinimum] = useState(1);
  const [family, setFamily] = useState<RelationFamily | "all">("all");
  const [showLabels, setShowLabels] = useState(true);
  const [focus, setFocus] = useState<FocusRecord>(() => ({
    kind: "tree",
    key: atlas.treeCounts[0]?.tree ?? "",
    item: atlas.treeCounts[0],
    rank: 1,
  }));

  const visibleTrees = useMemo(
    () => atlas.treeCounts.filter((item) => item.count >= minimum),
    [atlas.treeCounts, minimum],
  );
  const visibleRelations = useMemo(
    () => atlas.relationTypes.filter((item) => family === "all" || item.family === family),
    [atlas.relationTypes, family],
  );

  const cx = 565;
  const cy = 420;
  const maximumTree = atlas.treeCounts[0]?.count ?? 1;
  const rings = [
    { start: 0, end: 6, radius: 145, phase: -12 },
    { start: 6, end: 16, radius: 245, phase: 7 },
    { start: 16, end: Number.POSITIVE_INFINITY, radius: 340, phase: -4 },
  ];
  const relationWeights = visibleRelations.map((item) => Math.sqrt(item.count));
  const relationWeightTotal = relationWeights.reduce((sum, value) => sum + value, 0);
  const relationGap = 1.8;
  const relationAvailable = 350 - Math.max(0, visibleRelations.length - 1) * relationGap;
  let relationCursor = -175;

  const treeRecords = visibleTrees.map((item, visibleIndex) => {
    const absoluteRank = atlas.treeCounts.findIndex((entry) => entry.tree === item.tree);
    const ring = rings.find((entry) => absoluteRank >= entry.start && absoluteRank < entry.end) ?? rings[2];
    const ringItems = atlas.treeCounts
      .slice(ring.start, Number.isFinite(ring.end) ? ring.end : atlas.treeCounts.length)
      .filter((entry) => entry.count >= minimum);
    const ringPosition = ringItems.findIndex((entry) => entry.tree === item.tree);
    const angle = ring.phase + (ringPosition / Math.max(1, ringItems.length)) * 360;
    const point = polarPoint(cx, cy, ring.radius, angle);
    const radius = 7 + (Math.log1p(item.count) / Math.log1p(maximumTree)) * 18;
    const densityCount = 3 + Math.round((Math.log1p(item.count) / Math.log1p(maximumTree)) * 10);
    return {
      item,
      visibleIndex,
      absoluteRank,
      point,
      radius,
      densityCount,
      record: {
        kind: "tree" as const,
        key: item.tree,
        item,
        rank: absoluteRank + 1,
      },
    };
  });

  const relationRecords = visibleRelations.map((item) => {
    const absoluteRank = atlas.relationTypes.findIndex((entry) => entry.label === item.label);
    const weight = Math.sqrt(item.count);
    const span = relationWeightTotal ? (weight / relationWeightTotal) * relationAvailable : 0;
    const start = relationCursor;
    const end = start + span;
    relationCursor = end + relationGap;
    return {
      item,
      start,
      end,
      middle: start + span / 2,
      record: {
        kind: "relation" as const,
        key: item.label,
        item,
        rank: absoluteRank + 1,
      },
    };
  });

  const familyTotals = atlas.relationTypes.reduce<Record<RelationFamily, number>>(
    (totals, item) => ({ ...totals, [item.family]: totals[item.family] + item.count }),
    { source_provenance: 0, time_place: 0, medium_context: 0, historical_influence: 0 },
  );
  const isFocused = (key: string) => focus.key === key;

  return (
    <section className={styles.constellationShell} aria-labelledby="constellation-title">
      <header className={styles.constellationHeader}>
        <div>
          <p>TRACE model 02 / evidence constellation</p>
          <h2 id="constellation-title">Thirty research trees, one documented relation vocabulary.</h2>
        </div>
        <p>
          Geometry is deterministic: radius encodes tree rank, node area encodes membership, and
          annular span encodes documented edge volume. No line asserts historical influence.
        </p>
      </header>

      <div className={styles.constellationControls} aria-label="Constellation controls">
        <label>
          Tree threshold
          <select value={minimum} onChange={(event) => setMinimum(Number(event.target.value))}>
            {THRESHOLDS.map((entry) => (
              <option key={entry.value} value={entry.value}>{entry.label}</option>
            ))}
          </select>
        </label>
        <label>
          Relation family
          <select value={family} onChange={(event) => setFamily(event.target.value as RelationFamily | "all")}>
            <option value="all">All evidence families</option>
            {(Object.keys(FAMILY_LABELS) as RelationFamily[]).map((value) => (
              <option key={value} value={value}>{FAMILY_LABELS[value]}</option>
            ))}
          </select>
        </label>
        <button type="button" aria-pressed={showLabels} onClick={() => setShowLabels((value) => !value)}>
          {showLabels ? "Hide labels" : "Show labels"}
        </button>
        <p>{visibleTrees.length} trees · {visibleRelations.length} relation types</p>
      </div>

      <div className={styles.constellationLayout}>
        <div className={styles.constellationViewport} tabIndex={0} aria-label="Pan the evidence constellation">
          <svg
            className={styles.constellationPlot}
            viewBox="0 0 1300 850"
            role="img"
            aria-labelledby="constellation-svg-title constellation-svg-desc"
          >
            <title id="constellation-svg-title">TRACE evidence constellation</title>
            <desc id="constellation-svg-desc">
              Thirty ranked research-tree aggregates surround the active-object total. A separate outer
              annulus shows exact counts for twenty documented relation types. Spokes are aggregate
              membership guides, not historical influence claims.
            </desc>
            <defs>
              <radialGradient id="constellation-core-wash" cx="45%" cy="42%" r="65%">
                <stop offset="0%" stopColor="#f57957" stopOpacity="0.88" />
                <stop offset="52%" stopColor="#2868d7" stopOpacity="0.42" />
                <stop offset="100%" stopColor="#2868d7" stopOpacity="0" />
              </radialGradient>
            </defs>

            <g className={styles.constellationScaffold} aria-hidden="true">
              {[88, 145, 245, 340, 382, 410].map((radius, index) => (
                <circle key={radius} cx={cx} cy={cy} r={radius} data-major={index === 1 || index === 2 || index === 3} />
              ))}
              {Array.from({ length: 24 }, (_, index) => {
                const inner = polarPoint(cx, cy, 72, index * 15);
                const outer = polarPoint(cx, cy, 410, index * 15);
                return <line key={index} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} />;
              })}
            </g>

            <g className={styles.constellationRelations}>
              {relationRecords.map(({ item, start, end, middle, record }) => {
                const labelPoint = polarPoint(cx, cy, 425, middle);
                return (
                  <g
                    key={item.label}
                    role="button"
                    tabIndex={0}
                    aria-label={`${item.label.replaceAll("_", " ")}: ${item.count.toLocaleString("en-US")} documented edges, ${FAMILY_LABELS[item.family]}`}
                    data-family={item.family}
                    data-focused={isFocused(item.label)}
                    data-muted={Boolean(focus.key) && !isFocused(item.label)}
                    onMouseEnter={() => setFocus(record)}
                    onFocus={() => setFocus(record)}
                    onClick={() => setFocus(record)}
                    onKeyDown={(event) => activate(event, record, setFocus)}
                  >
                    <path d={arcPath(cx, cy, 410, start, end)} />
                    {showLabels && end - start > 5.5 ? (
                      <text
                        x={labelPoint.x}
                        y={labelPoint.y}
                        textAnchor={labelPoint.x < cx ? "end" : "start"}
                      >
                        {item.label.replaceAll("_", " ")}
                      </text>
                    ) : null}
                  </g>
                );
              })}
            </g>

            <g className={styles.constellationTrees}>
              {treeRecords.map(({ item, point, radius, densityCount, record, absoluteRank }) => {
                const labelPoint = polarPoint(point.x, point.y, radius + 16, point.x < cx ? 270 : 90);
                return (
                  <g
                    key={item.tree}
                    role="button"
                    tabIndex={0}
                    aria-label={`${item.tree}, rank ${absoluteRank + 1}: ${item.count.toLocaleString("en-US")} active object memberships`}
                    data-focused={isFocused(item.tree)}
                    data-muted={Boolean(focus.key) && !isFocused(item.tree)}
                    onMouseEnter={() => setFocus(record)}
                    onFocus={() => setFocus(record)}
                    onClick={() => setFocus(record)}
                    onKeyDown={(event) => activate(event, record, setFocus)}
                  >
                    <line x1={cx} y1={cy} x2={point.x} y2={point.y} />
                    {Array.from({ length: densityCount }, (_, densityIndex) => {
                      const satellite = polarPoint(
                        point.x,
                        point.y,
                        radius + 7 + (densityIndex % 3) * 3,
                        (densityIndex / densityCount) * 360 + absoluteRank * 11,
                      );
                      return <circle key={densityIndex} cx={satellite.x} cy={satellite.y} r={1.3 + (densityIndex % 2) * 0.65} data-density="true" />;
                    })}
                    <circle cx={point.x} cy={point.y} r={radius + 5} data-halo="true" />
                    <circle cx={point.x} cy={point.y} r={radius} data-node="true" />
                    <text x={point.x} y={point.y + 2.5} textAnchor="middle" data-rank="true">
                      {String(absoluteRank + 1).padStart(2, "0")}
                    </text>
                    {showLabels ? (
                      <text
                        x={labelPoint.x}
                        y={labelPoint.y}
                        textAnchor={point.x < cx ? "end" : "start"}
                        data-label="true"
                      >
                        {item.tree}
                      </text>
                    ) : null}
                  </g>
                );
              })}
            </g>

            <g className={styles.constellationCore}>
              <circle cx={cx} cy={cy} r="76" fill="url(#constellation-core-wash)" />
              <circle cx={cx} cy={cy} r="54" />
              <text x={cx} y={cy - 18} textAnchor="middle">ACTIVE</text>
              <text x={cx} y={cy + 8} textAnchor="middle" data-count="true">
                {atlas.counts.activeObjects.toLocaleString("en-US")}
              </text>
              <text x={cx} y={cy + 28} textAnchor="middle">OBJECTS</text>
            </g>

            <g className={styles.constellationReadout} transform="translate(1010 116)">
              <rect width="250" height="500" />
              <text x="18" y="30" data-kicker="true">SELECTED EVIDENCE SCALE</text>
              <text x="18" y="76" data-title="true">
                {focus.kind === "tree" ? focus.item.tree : focus.item.label.replaceAll("_", " ")}
              </text>
              <text x="18" y="110" data-value="true">{focus.item.count.toLocaleString("en-US")}</text>
              <text x="18" y="130" data-unit="true">
                {focus.kind === "tree" ? "OBJECT MEMBERSHIPS" : "DOCUMENTED EDGES"}
              </text>
              <line x1="18" y1="154" x2="232" y2="154" />
              <text x="18" y="182" data-copy="true">
                {focus.kind === "tree" ? `RANK ${focus.rank} OF ${atlas.treeCounts.length}` : FAMILY_LABELS[focus.item.family].toUpperCase()}
              </text>
              <text x="18" y="205" data-copy="true">
                {focus.kind === "tree"
                  ? `${((focus.item.count / atlas.counts.activeObjects) * 100).toFixed(1)}% OF ACTIVE OBJECTS`
                  : `RANK ${focus.rank} OF ${atlas.relationTypes.length}`}
              </text>
              <text x="18" y="254" data-note="true">
                <tspan x="18" dy="0">{focus.kind === "tree" ? "The spoke means aggregate" : "The annular span means edge"}</tspan>
                <tspan x="18" dy="17">{focus.kind === "tree" ? "membership in one research tree." : "volume within the vocabulary."}</tspan>
                <tspan x="18" dy="17">It does not encode influence.</tspan>
              </text>
              <text x="18" y="340" data-kicker="true">RELATION FAMILY TOTALS</text>
              {(Object.keys(FAMILY_LABELS) as RelationFamily[]).map((value, index) => (
                <g key={value} transform={`translate(18 ${366 + index * 28})`} data-family={value}>
                  <circle cx="5" cy="-4" r="5" />
                  <text x="18" y="0" data-copy="true">{FAMILY_LABELS[value].toUpperCase()}</text>
                  <text x="214" y="0" textAnchor="end" data-copy="true">{familyTotals[value].toLocaleString("en-US")}</text>
                </g>
              ))}
            </g>
          </svg>
        </div>

        <ol className={styles.constellationMobileCards} aria-label="Tap to inspect major TRACE aggregates">
          {atlas.treeCounts.slice(0, 8).map((item, index) => {
            const record: FocusRecord = { kind: "tree", key: item.tree, item, rank: index + 1 };
            return (
              <li key={item.tree}>
                <button type="button" aria-pressed={isFocused(item.tree)} onClick={() => setFocus(record)}>
                  <span>Tree {String(index + 1).padStart(2, "0")}</span>
                  <strong>{item.tree}</strong>
                  <b>{item.count.toLocaleString("en-US")}</b>
                  <small>active object memberships</small>
                </button>
              </li>
            );
          })}
        </ol>
      </div>

      <details className={styles.constellationTable}>
        <summary>Exact tree and relation ledger</summary>
        <div>
          <table>
            <caption>Exact TRACE research-tree counts</caption>
            <thead><tr><th>Rank</th><th>Tree</th><th>Object memberships</th></tr></thead>
            <tbody>{atlas.treeCounts.map((item, index) => <tr key={item.tree}><td>{index + 1}</td><th>{item.tree}</th><td>{item.count.toLocaleString("en-US")}</td></tr>)}</tbody>
          </table>
          <table>
            <caption>Exact TRACE relation counts</caption>
            <thead><tr><th>Rank</th><th>Relation</th><th>Family</th><th>Edges</th></tr></thead>
            <tbody>{atlas.relationTypes.map((item, index) => <tr key={item.label}><td>{index + 1}</td><th>{item.label.replaceAll("_", " ")}</th><td>{FAMILY_LABELS[item.family]}</td><td>{item.count.toLocaleString("en-US")}</td></tr>)}</tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

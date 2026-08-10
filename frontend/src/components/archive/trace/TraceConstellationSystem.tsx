"use client";

import { useMemo, useState, type KeyboardEvent } from "react";
import styles from "./TraceExplorer.module.css";
import type { AtlasTreeCount, RelationFamily, TraceAtlas } from "./trace-types";

type Focus = { item: AtlasTreeCount; rank: number };
type DocumentedFamily = Exclude<RelationFamily, "historical_influence">;

const DOCUMENTED_FAMILY_ORDER: DocumentedFamily[] = [
  "source_provenance",
  "time_place",
  "medium_context",
];

const FAMILY_LABELS: Record<RelationFamily, string> = {
  source_provenance: "Source / provenance",
  time_place: "Time / place",
  medium_context: "Medium / context",
  historical_influence: "Historical influence — not plotted",
};

// These public labels name the dominant collection or explicit regional set behind
// each frozen v48 research tree. The internal TRTREE identifier remains visible as
// a secondary label and as the durable lookup key.
const TREE_LABELS: Record<string, string> = {
  TRTREE001: "Desain Grafis Indonesia",
  TRTREE004: "Malaysia Archive · seed",
  TRTREE005: "Malaysia Archive · collection",
  TRTREE010: "Pacific Community Library",
  TRTREE013: "Nasjonalmuseet records",
  TRTREE014: "V&A collection",
  TRTREE015: "Library of Congress",
  TRTREE016: "Global open-image records",
  TRTREE017: "Distributed open collections",
  TRTREE018: "Contributor-held records",
  TRTREE019: "Creator-contributed records",
  TRTREE020: "Art Institute · 1990–2025",
  TRTREE021: "Malaysia Archive · recent",
  TRTREE023: "Pacific Community · regional",
  TRTREE024: "Pacific Community · focus",
  TRTREE025: "Pacific Community · islands",
  TRTREE026: "Chile National Library",
  TRTREE027: "Chile Library · focused",
  TRTREE030: "Art Institute · historical",
  TRTREE032: "Art Institute · contemporary",
  TRTREE033: "Cooper Hewitt",
  TRTREE034: "Yale / Art Institute",
  TRTREE037: "Yale · contemporary design",
  TRTREE038: "Norway / Yale records",
  TRTREE039: "Digital Commonwealth · 1805",
  TRTREE040: "National Library of Norway",
  TRTREE041: "Library of Congress · early",
  TRTREE042: "Gallica · early",
  TRTREE043: "Gallica · focused",
  TRTREE048: "Art Institute · linked",
};

const RELATION_LABELS: Record<string, string> = {
  has_type: "Has type",
  associated_with_context: "Associated context",
  associated_with_place: "Associated place",
  documented_by: "Documented by",
  created_by: "Created by",
  has_material_or_technique: "Material / technique",
  associated_with_research_cluster: "Research cluster",
  associated_with_theme: "Associated theme",
  has_medium: "Has medium",
  part_of_collection: "Part of collection",
  part_of_series: "Part of series",
  circulated_in: "Circulated in",
  issued_by: "Issued by",
  classified_as: "Classified as",
  dated_to: "Dated to",
  associated_with_year: "Associated year",
  credited_to: "Credited to",
  part_of_campaign: "Part of campaign",
  uses_language: "Uses language",
  dated: "Dated",
};

const THRESHOLDS = [
  { value: 1, label: "All 30 trees" },
  { value: 25, label: "25 or more memberships" },
  { value: 100, label: "100 or more memberships" },
] as const;

const TREE_RADIUS = 340;
const TREE_SPAN_RADIUS = 390;
const TREE_LABEL_RADIUS = 438;
const TREE_GAP_DEGREES = 1.4;
const FAMILY_GAP_DEGREES = 8;

function treeLabel(tree: string) {
  return TREE_LABELS[tree] ?? "Research tree";
}

function shortTreeLabel(tree: string) {
  const label = treeLabel(tree).replace(/ · .+$/, "");
  return label.length > 18 ? `${label.slice(0, 17).trim()}…` : label;
}

function relationLabel(relation: string) {
  return RELATION_LABELS[relation] ?? relation.replaceAll("_", " ");
}

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return { x: cx + Math.cos(radians) * radius, y: cy + Math.sin(radians) * radius };
}

function arcPath(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarPoint(cx, cy, radius, startAngle);
  const end = polarPoint(cx, cy, radius, endAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;
  return `M${start.x.toFixed(2)},${start.y.toFixed(2)} A${radius},${radius} 0 ${largeArcFlag} 1 ${end.x.toFixed(2)},${end.y.toFixed(2)}`;
}

function annularSectorPath(
  cx: number,
  cy: number,
  innerRadius: number,
  outerRadius: number,
  startAngle: number,
  endAngle: number,
) {
  const outerStart = polarPoint(cx, cy, outerRadius, startAngle);
  const outerEnd = polarPoint(cx, cy, outerRadius, endAngle);
  const innerEnd = polarPoint(cx, cy, innerRadius, endAngle);
  const innerStart = polarPoint(cx, cy, innerRadius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;
  return [
    `M${outerStart.x.toFixed(2)},${outerStart.y.toFixed(2)}`,
    `A${outerRadius},${outerRadius} 0 ${largeArcFlag} 1 ${outerEnd.x.toFixed(2)},${outerEnd.y.toFixed(2)}`,
    `L${innerEnd.x.toFixed(2)},${innerEnd.y.toFixed(2)}`,
    `A${innerRadius},${innerRadius} 0 ${largeArcFlag} 0 ${innerStart.x.toFixed(2)},${innerStart.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

function radiusForArea(area: number) {
  return Math.sqrt(area / Math.PI);
}

function activate(event: KeyboardEvent<SVGGElement>, callback: () => void) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    callback();
  }
}

export default function TraceConstellationSystem({ atlas }: { atlas: TraceAtlas }) {
  const [minimum, setMinimum] = useState(1);
  const [focus, setFocus] = useState<Focus | null>(null);
  const [locked, setLocked] = useState(false);
  const maximumMembership = Math.max(...atlas.treeCounts.map((item) => item.count), 1);
  const slotDegrees = 360 / Math.max(atlas.treeCounts.length, 1);
  const cx = 700;
  const cy = 500;

  const visibleTrees = useMemo(
    () => atlas.treeCounts.filter((item) => item.count >= minimum),
    [atlas.treeCounts, minimum],
  );

  const familyTotals = useMemo(
    () => atlas.relationTypes.reduce<Record<RelationFamily, number>>(
      (totals, relation) => ({ ...totals, [relation.family]: totals[relation.family] + relation.count }),
      { source_provenance: 0, time_place: 0, medium_context: 0, historical_influence: 0 },
    ),
    [atlas.relationTypes],
  );

  const familyRecords = useMemo(() => {
    const observed = DOCUMENTED_FAMILY_ORDER
      .map((family) => ({ family, count: familyTotals[family] }))
      .filter((record) => record.count > 0);
    const total = observed.reduce((sum, record) => sum + record.count, 0);
    const maximum = Math.max(...observed.map((record) => record.count), 1);
    const available = 360 - observed.length * FAMILY_GAP_DEGREES;
    let cursor = 0;

    return observed.map((record) => {
      const span = total ? (record.count / total) * available : 0;
      const startAngle = cursor + FAMILY_GAP_DEGREES / 2;
      const endAngle = startAngle + span;
      cursor = endAngle + FAMILY_GAP_DEGREES / 2;
      const nodeArea = 210 + (record.count / maximum) * 620;
      return {
        ...record,
        startAngle,
        endAngle,
        middleAngle: startAngle + span / 2,
        nodeRadius: radiusForArea(nodeArea),
      };
    });
  }, [familyTotals]);

  // Layout is always calculated from the complete frozen tree list. The threshold
  // only controls which records render, so every remaining tree keeps its slot.
  const treeRecords = useMemo(
    () => atlas.treeCounts.map((item, index) => {
      const membershipRatio = item.count / maximumMembership;
      const logRatio = Math.log1p(item.count) / Math.log1p(maximumMembership);
      const angle = index * slotDegrees;
      const span = Math.max(
        1.2,
        Math.min(slotDegrees - TREE_GAP_DEGREES, 1.2 + logRatio * (slotDegrees - TREE_GAP_DEGREES - 1.2)),
      );
      const hub = polarPoint(cx, cy, TREE_RADIUS, angle);
      const labelRadius = TREE_LABEL_RADIUS + (index % 2) * 26;
      const label = polarPoint(cx, cy, labelRadius, angle);
      const labelRotation = angle > 90 && angle < 270 ? angle + 180 : angle;
      const nodeArea = 115 + membershipRatio * 1_150;
      return {
        item,
        rank: index + 1,
        angle,
        span,
        hub,
        label,
        labelRotation,
        nodeRadius: radiusForArea(nodeArea),
        trunkWidth: 0.8 + logRatio * 2.6,
        spanWidth: 1.2 + logRatio * 5.2,
      };
    }),
    [atlas.treeCounts, cx, cy, maximumMembership, slotDegrees],
  );

  function preview(next: Focus) {
    if (!locked) setFocus(next);
  }

  function releasePreview() {
    if (!locked) setFocus(null);
  }

  function choose(next: Focus) {
    if (locked && focus?.item.tree === next.item.tree) {
      setLocked(false);
      setFocus(null);
      return;
    }
    setFocus(next);
    setLocked(true);
  }

  function changeMinimum(nextMinimum: number) {
    setMinimum(nextMinimum);
    if (focus && focus.item.count < nextMinimum) {
      setFocus(null);
      setLocked(false);
    }
  }

  const focusedLabel = focus ? treeLabel(focus.item.tree) : "All research trees";
  const focusedValue = focus ? focus.item.count : atlas.counts.activeObjects;
  const focusedUnit = focus ? "active object memberships" : "active objects in the frozen layer";

  return (
    <section className={styles.constellationSystem} aria-labelledby="constellation-system-title">
      <section className={styles.mobileConstellation} aria-label="Mobile TRACE evidence trees">
        <header className={styles.mobileConstellationHeader}>
          <p>EVIDENCE / {atlas.treeCounts.length} RESEARCH TREES</p>
          <h2>{focus ? treeLabel(focus.item.tree) : "Choose one documented branch"}</h2>
        </header>

        <div
          className={styles.mobileConstellationDots}
          role="grid"
          aria-label="Research trees ordered by active object membership"
        >
          {atlas.treeCounts.map((item, index) => {
            const ratio = item.count / maximumMembership;
            const purity = ratio >= 0.35 ? 100 : ratio >= 0.08 ? 80 : ratio >= 0.02 ? 70 : 60;
            const selected = focus?.item.tree === item.tree && locked;
            return (
              <button
                key={item.tree}
                type="button"
                role="gridcell"
                data-purity={purity}
                aria-selected={selected}
                aria-label={`${treeLabel(item.tree)}: ${item.count.toLocaleString()} active object memberships`}
                onClick={() => choose({ item, rank: index + 1 })}
              />
            );
          })}
        </div>

        <article className={styles.mobileConstellationReadout} aria-live="polite" data-selected={Boolean(focus && locked)}>
          {focus && locked ? (
            <>
              <p>{focus.item.tree} · RESEARCH TREE</p>
              <h3>{treeLabel(focus.item.tree)}</h3>
              <strong>{focus.item.count.toLocaleString()}</strong>
              <span>{((focus.item.count / atlas.counts.activeObjects) * 100).toFixed(1)}% of active objects hold membership</span>
              <button type="button" onClick={() => { setLocked(false); setFocus(null); }} aria-label="Clear selected research tree">Clear</button>
            </>
          ) : (
            <>
              <p>DOCUMENTED MEMBERSHIP</p>
              <h3>Tap a point to inspect its research tree.</h3>
              <span>Purity steps 100 / 80 / 70 / 60 encode relative membership volume. No point asserts historical influence.</span>
            </>
          )}
        </article>
      </section>

      <header className={styles.constellationSystemHeader}>
        <div>
          <p>TRACE MODEL 02 / RADIAL EVIDENCE SYSTEM</p>
          <h2 id="constellation-system-title">Thirty stable research trees, sized by documented evidence.</h2>
        </div>
        <details className={styles.constellationSystemControls}>
          <summary>Scale / labels</summary>
          <label>
            Minimum memberships
            <select value={minimum} onChange={(event) => changeMinimum(Number(event.target.value))}>
              {THRESHOLDS.map((threshold) => (
                <option key={threshold.value} value={threshold.value}>{threshold.label}</option>
              ))}
            </select>
          </label>
          <p>
            Every tree owns a fixed angular lane. Hub area is linear by membership; outer span is
            log-scaled by membership. Inner sectors use exact documented relation-family totals.
          </p>
        </details>
      </header>

      <div className={styles.constellationSystemStage}>
        <svg className={styles.constellationSystemPlot} viewBox="0 0 1400 1000" role="img" aria-labelledby="radial-tree-title radial-tree-desc">
          <title id="radial-tree-title">Radial TRACE evidence hierarchy</title>
          <desc id="radial-tree-desc">
            Thirty fixed angular lanes show research-tree membership. Hub area and outer arc span
            derive from membership counts. Three inner sectors show exact documented relation-family
            volume. The diagram does not encode influence, and historical influence is not plotted.
          </desc>
          <defs>
            <radialGradient id="constellation-paper" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#fffaf0" /><stop offset="72%" stopColor="#f5eddc" /><stop offset="100%" stopColor="#e8deca" /></radialGradient>
            <filter id="tree-focus-glow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="6" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <rect width="1400" height="1000" fill="url(#constellation-paper)" />

          <g className={styles.constellationSystemGrid} aria-hidden="true">
            {[92, 166, 210, TREE_RADIUS, TREE_SPAN_RADIUS, TREE_LABEL_RADIUS].map((radius) => <circle key={radius} cx={cx} cy={cy} r={radius} />)}
            {atlas.treeCounts.map((item, index) => {
              const angle = index * slotDegrees;
              const start = polarPoint(cx, cy, 210, angle);
              const end = polarPoint(cx, cy, TREE_LABEL_RADIUS, angle);
              return <line key={item.tree} x1={start.x} y1={start.y} x2={end.x} y2={end.y} />;
            })}
          </g>

          <g className={styles.constellationRibbons} aria-label="Documented relation-family volume">
            {familyRecords.map((record) => (
              <path
                key={record.family}
                d={annularSectorPath(cx, cy, 92, 166, record.startAngle, record.endAngle)}
                data-family={record.family}
                data-edge-count={record.count}
              >
                <title>{FAMILY_LABELS[record.family]}: {record.count.toLocaleString()} documented edges</title>
              </path>
            ))}
          </g>

          <g className={styles.constellationFamilyNodes} aria-label="Observed relation families">
            {familyRecords.map((record) => {
              const point = polarPoint(cx, cy, 129, record.middleAngle);
              const labelPoint = polarPoint(cx, cy, 187, record.middleAngle);
              return (
                <g key={record.family} data-family={record.family} data-edge-count={record.count}>
                  <circle cx={point.x} cy={point.y} r={record.nodeRadius} />
                  <text x={labelPoint.x} y={labelPoint.y} textAnchor="middle">
                    <tspan x={labelPoint.x}>{FAMILY_LABELS[record.family]}</tspan>
                    <tspan x={labelPoint.x} dy="20">{record.count.toLocaleString()} edges</tspan>
                  </text>
                </g>
              );
            })}
          </g>

          <g className={styles.constellationBranches}>
            {treeRecords
              .filter((record) => record.item.count >= minimum)
              .map((record) => {
                const { item, rank, angle, span, hub, label, labelRotation, nodeRadius, trunkWidth, spanWidth } = record;
                const selected = focus?.item.tree === item.tree;
                const focusRecord = { item, rank };
                const trunkStart = polarPoint(cx, cy, 210, angle);
                return (
                  <g
                    key={item.tree}
                    role="button"
                    tabIndex={0}
                    data-selected={selected}
                    data-muted={locked && !selected}
                    data-tree={item.tree}
                    data-memberships={item.count}
                    data-major={rank <= 8}
                    aria-label={`${treeLabel(item.tree)}, ${item.tree}, rank ${rank}: ${item.count.toLocaleString()} active object memberships`}
                    onMouseEnter={() => preview(focusRecord)}
                    onMouseLeave={releasePreview}
                    onFocus={() => preview(focusRecord)}
                    onClick={() => choose(focusRecord)}
                    onKeyDown={(event) => activate(event, () => choose(focusRecord))}
                  >
                    <path
                      d={`M${trunkStart.x.toFixed(2)},${trunkStart.y.toFixed(2)} L${hub.x.toFixed(2)},${hub.y.toFixed(2)}`}
                      data-trunk="true"
                      style={{ strokeWidth: trunkWidth }}
                    >
                      <title>{item.count.toLocaleString()} memberships in {treeLabel(item.tree)}</title>
                    </path>
                    <path
                      d={arcPath(cx, cy, TREE_SPAN_RADIUS, angle - span / 2, angle + span / 2)}
                      data-span="membership"
                      style={{ strokeWidth: spanWidth }}
                    >
                      <title>Log-scaled membership span: {item.count.toLocaleString()}</title>
                    </path>
                    <circle cx={hub.x} cy={hub.y} r={nodeRadius} data-hub="true">
                      <title>Hub area represents {item.count.toLocaleString()} memberships</title>
                    </circle>
                    <text x={label.x} y={label.y} textAnchor="middle" transform={`rotate(${labelRotation} ${label.x} ${label.y})`} data-label="true">
                      <tspan x={label.x}>{shortTreeLabel(item.tree)}</tspan>
                      <tspan x={label.x} dy="20" opacity="0.68">{item.count.toLocaleString()}</tspan>
                    </text>
                  </g>
                );
              })}
          </g>

          <g className={styles.constellationCoreSystem}>
            <circle cx={cx} cy={cy} r="76" />
            <text x={cx} y={cy - 24} textAnchor="middle">ACTIVE</text>
            <text x={cx} y={cy + 7} textAnchor="middle" data-count="true">{atlas.counts.activeObjects.toLocaleString()}</text>
            <text x={cx} y={cy + 30} textAnchor="middle">OBJECTS</text>
            <text x={cx} y={cy + 49} textAnchor="middle">INFLUENCE NOT PLOTTED</text>
          </g>
        </svg>

        <aside className={styles.constellationSystemReadout} aria-live="polite" data-locked={locked}>
          <p>{locked ? "Locked selection" : focus ? "Current tree" : "Evidence overview"}</p>
          <span>{focus ? `Rank ${focus.rank} / ${atlas.treeCounts.length} · ${focus.item.tree}` : `${visibleTrees.length} / ${atlas.treeCounts.length} trees visible`}</span>
          <h3>{focusedLabel}</h3>
          <strong>{focusedValue.toLocaleString()}</strong>
          <small>{focusedUnit}</small>
          <div><i /><span>{focus ? `${((focus.item.count / atlas.counts.activeObjects) * 100).toFixed(1)}% of the active layer` : `${atlas.relationTypes.length} observed relation types`}</span></div>
          <p>
            {focus
              ? "The radial guide groups aggregate membership in this research tree. It states neither authorship, transmission, nor influence."
              : "Tree positions remain fixed when the threshold changes. Relation-family sectors report documented edge volume; no historical influence relation is drawn."}
          </p>
          {locked ? <button type="button" onClick={() => { setLocked(false); setFocus(null); }}>Release selection</button> : null}
        </aside>

        <ol className={styles.constellationTouchRail} aria-label="Tap to select major evidence trees">
          {atlas.treeCounts.slice(0, 10).map((item, index) => (
            <li key={item.tree}>
              <button type="button" aria-pressed={focus?.item.tree === item.tree} onClick={() => { setFocus({ item, rank: index + 1 }); setLocked(true); }}>
                <span>{item.tree}</span>
                <strong>{treeLabel(item.tree)}</strong>
                <b>{item.count.toLocaleString()}</b>
              </button>
            </li>
          ))}
        </ol>
      </div>

      <details className={styles.constellationLedger}>
        <summary>Exact tree and relation ledger</summary>
        <div>
          <table>
            <caption>TRACE research-tree membership counts</caption>
            <thead><tr><th>Rank</th><th>Research tree</th><th>Memberships</th></tr></thead>
            <tbody>{atlas.treeCounts.map((item, index) => <tr key={item.tree}><td>{index + 1}</td><th>{treeLabel(item.tree)}<small>{item.tree}</small></th><td>{item.count.toLocaleString()}</td></tr>)}</tbody>
          </table>
          <table>
            <caption>TRACE documented relation counts</caption>
            <thead><tr><th>Relation</th><th>Family</th><th>Edges</th></tr></thead>
            <tbody>{atlas.relationTypes.map((item) => <tr key={item.label}><th>{relationLabel(item.label)}<small>{item.label}</small></th><td>{FAMILY_LABELS[item.family]}</td><td>{item.count.toLocaleString()}</td></tr>)}</tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

"use client";

import { useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import styles from "./TraceExplorer.module.css";
import type { AtlasTreeCount, RelationFamily, TraceAtlas } from "./trace-types";

type Focus = { item: AtlasTreeCount; rank: number };

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
  historical_influence: "Historical influence",
};

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return { x: cx + Math.cos(radians) * radius, y: cy + Math.sin(radians) * radius };
}

function activate(event: KeyboardEvent<SVGGElement>, callback: () => void) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    callback();
  }
}

function ribbonPath(y: number, amplitude: number, phase: number) {
  const points = Array.from({ length: 13 }, (_, index) => {
    const x = 510 + index * 32;
    const wave = Math.sin(index * 0.92 + phase) * amplitude;
    const taper = Math.sin((index / 12) * Math.PI);
    return { x, top: y + wave - 12 * taper, bottom: y + wave + 12 * taper };
  });
  const top = points.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.top.toFixed(1)}`).join(" ");
  const bottom = [...points].reverse().map((point) => `L${point.x.toFixed(1)},${point.bottom.toFixed(1)}`).join(" ");
  return `${top} ${bottom} Z`;
}

export default function TraceConstellationSystem({ atlas }: { atlas: TraceAtlas }) {
  const [minimum, setMinimum] = useState(1);
  const [focus, setFocus] = useState<Focus>({ item: atlas.treeCounts[0], rank: 1 });
  const [locked, setLocked] = useState(false);
  const visibleTrees = useMemo(
    () => atlas.treeCounts.filter((item) => item.count >= minimum),
    [atlas.treeCounts, minimum],
  );
  const maximum = atlas.treeCounts[0]?.count ?? 1;
  const familyTotals = atlas.relationTypes.reduce<Record<RelationFamily, number>>(
    (totals, relation) => ({ ...totals, [relation.family]: totals[relation.family] + relation.count }),
    { source_provenance: 0, time_place: 0, medium_context: 0, historical_influence: 0 },
  );
  const familyMaximum = Math.max(...Object.values(familyTotals), 1);
  const cx = 700;
  const cy = 500;

  function preview(next: Focus) {
    if (!locked) setFocus(next);
  }

  function choose(next: Focus) {
    setFocus(next);
    setLocked((current) => current && focus.item.tree === next.item.tree ? false : true);
  }

  return (
    <section className={styles.constellationSystem} aria-labelledby="constellation-system-title">
      <header className={styles.constellationSystemHeader}>
        <div>
          <p>TRACE MODEL 02 / RADIAL EVIDENCE SYSTEM</p>
          <h2 id="constellation-system-title">Thirty research trees resolved into evidence branches.</h2>
        </div>
        <details className={styles.constellationSystemControls}>
          <summary>Scale / labels</summary>
          <label>
            Minimum memberships
            <select value={minimum} onChange={(event) => setMinimum(Number(event.target.value))}>
              <option value="1">All 30 trees</option>
              <option value="25">25 or more</option>
              <option value="100">100 or more</option>
            </select>
          </label>
          <p>Leaf circles are aggregate count packets. They are not individual objects or influence claims.</p>
        </details>
      </header>

      <div className={styles.constellationSystemStage}>
        <svg className={styles.constellationSystemPlot} viewBox="0 0 1400 1000" role="img" aria-labelledby="radial-tree-title radial-tree-desc">
          <title id="radial-tree-title">Radial TRACE evidence hierarchy</title>
          <desc id="radial-tree-desc">Thirty evidence trees form a numbered inner ring. Each hub branches into aggregate membership packets. Four central ribbons encode documented relation-family volume. Historical influence remains zero.</desc>
          <defs>
            <radialGradient id="constellation-paper" cx="50%" cy="50%" r="60%"><stop offset="0%" stopColor="#fffaf0" /><stop offset="72%" stopColor="#f5eddc" /><stop offset="100%" stopColor="#e8deca" /></radialGradient>
            <filter id="tree-focus-glow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="6" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <rect width="1400" height="1000" fill="url(#constellation-paper)" />
          <g className={styles.constellationSystemGrid} aria-hidden="true">
            {[132, 210, 270, 350, 430].map((radius) => <circle key={radius} cx={cx} cy={cy} r={radius} />)}
            {Array.from({ length: 36 }, (_, index) => {
              const start = polarPoint(cx, cy, 112, index * 10);
              const end = polarPoint(cx, cy, 458, index * 10);
              return <line key={index} x1={start.x} y1={start.y} x2={end.x} y2={end.y} />;
            })}
          </g>

          <g className={styles.constellationRibbons} aria-label="Documented relation-family volume">
            {FAMILY_ORDER.map((family, index) => {
              const ratio = familyTotals[family] / familyMaximum;
              return (
                <path
                  key={family}
                  d={ribbonPath(cy - 54 + index * 36, 8 + ratio * 28, index * 0.8)}
                  data-family={family}
                  data-empty={familyTotals[family] === 0}
                >
                  <title>{FAMILY_LABELS[family]}: {familyTotals[family].toLocaleString()} documented edges</title>
                </path>
              );
            })}
          </g>

          <g className={styles.constellationFamilyNodes}>
            {FAMILY_ORDER.map((family, index) => {
              const point = polarPoint(cx, cy, 118, index * 90 + 45);
              const radius = 11 + (familyTotals[family] / familyMaximum) * 16;
              return <g key={family} data-family={family}><circle cx={point.x} cy={point.y} r={radius} /><text x={point.x} y={point.y + radius + 16} textAnchor="middle">{FAMILY_LABELS[family]}</text></g>;
            })}
          </g>

          <g className={styles.constellationBranches}>
            {visibleTrees.map((item, visibleIndex) => {
              const rank = atlas.treeCounts.findIndex((tree) => tree.tree === item.tree) + 1;
              const angle = (visibleIndex / visibleTrees.length) * 360;
              const hub = polarPoint(cx, cy, 270, angle);
              const shoulder = polarPoint(cx, cy, 342, angle);
              const leafCount = Math.max(7, Math.min(17, Math.round(7 + (Math.log1p(item.count) / Math.log1p(maximum)) * 10)));
              const selected = focus.item.tree === item.tree;
              const record = { item, rank };
              return (
                <g
                  key={item.tree}
                  role="button"
                  tabIndex={0}
                  data-selected={selected}
                  data-muted={focus.item.tree !== item.tree}
                  aria-label={`${item.tree}, rank ${rank}: ${item.count.toLocaleString()} active object memberships`}
                  onMouseEnter={() => preview(record)}
                  onFocus={() => preview(record)}
                  onClick={() => choose(record)}
                  onKeyDown={(event) => activate(event, () => choose(record))}
                >
                  <path d={`M${polarPoint(cx, cy, 132, angle).x},${polarPoint(cx, cy, 132, angle).y} C${polarPoint(cx, cy, 190, angle).x},${polarPoint(cx, cy, 190, angle).y} ${hub.x},${hub.y} ${shoulder.x},${shoulder.y}`} data-trunk="true" />
                  <circle cx={hub.x} cy={hub.y} r={10 + (Math.log1p(item.count) / Math.log1p(maximum)) * 10} data-hub="true" />
                  <text x={hub.x} y={hub.y + 3} textAnchor="middle" data-rank="true">{rank}</text>
                  {Array.from({ length: leafCount }, (_, leafIndex) => {
                    const lane = leafIndex % 4;
                    const tier = Math.floor(leafIndex / 4);
                    const leafAngle = angle + (lane - 1.5) * (2.2 + tier * 0.25);
                    const leaf = polarPoint(cx, cy, 370 + tier * 26, leafAngle);
                    const packet = Math.max(1, Math.round(item.count / leafCount));
                    return (
                      <g key={leafIndex}>
                        <path d={`M${shoulder.x},${shoulder.y} Q${polarPoint(cx, cy, 360 + tier * 9, angle).x},${polarPoint(cx, cy, 360 + tier * 9, angle).y} ${leaf.x},${leaf.y}`} data-twig="true" />
                        <circle cx={leaf.x} cy={leaf.y} r={3.1 + (leafIndex % 3) * 0.9} data-leaf="true" style={{ "--leaf-order": leafIndex } as CSSProperties}>
                          <title>{item.tree} aggregate packet: approximately {packet.toLocaleString()} memberships</title>
                        </circle>
                      </g>
                    );
                  })}
                  <text x={polarPoint(cx, cy, 454, angle).x} y={polarPoint(cx, cy, 454, angle).y} textAnchor={Math.cos(((angle - 90) * Math.PI) / 180) < -0.1 ? "end" : Math.cos(((angle - 90) * Math.PI) / 180) > 0.1 ? "start" : "middle"} data-label="true">{item.tree}</text>
                </g>
              );
            })}
          </g>

          <g className={styles.constellationCoreSystem}>
            <circle cx={cx} cy={cy} r="76" />
            <text x={cx} y={cy - 18} textAnchor="middle">ACTIVE</text>
            <text x={cx} y={cy + 12} textAnchor="middle" data-count="true">{atlas.counts.activeObjects.toLocaleString()}</text>
            <text x={cx} y={cy + 34} textAnchor="middle">OBJECTS</text>
          </g>
        </svg>

        <aside className={styles.constellationSystemReadout} aria-live="polite" data-locked={locked}>
          <p>{locked ? "Locked selection" : "Current tree"}</p>
          <span>Rank {focus.rank} / {atlas.treeCounts.length}</span>
          <h3>{focus.item.tree}</h3>
          <strong>{focus.item.count.toLocaleString()}</strong>
          <small>active object memberships</small>
          <div><i /><span>{((focus.item.count / atlas.counts.activeObjects) * 100).toFixed(1)}% of the active layer</span></div>
          <p>Branches divide the aggregate into display packets. No branch states authorship, transmission, or influence.</p>
          {locked ? <button type="button" onClick={() => setLocked(false)}>Release selection</button> : null}
        </aside>

        <ol className={styles.constellationTouchRail} aria-label="Tap to select major evidence trees">
          {atlas.treeCounts.slice(0, 10).map((item, index) => (
            <li key={item.tree}><button type="button" aria-pressed={focus.item.tree === item.tree} onClick={() => { setFocus({ item, rank: index + 1 }); setLocked(true); }}><span>{String(index + 1).padStart(2, "0")}</span><strong>{item.tree}</strong><b>{item.count.toLocaleString()}</b></button></li>
          ))}
        </ol>
      </div>

      <details className={styles.constellationLedger}>
        <summary>Exact tree and relation ledger</summary>
        <div>
          <table><caption>TRACE research-tree membership counts</caption><thead><tr><th>Rank</th><th>Tree</th><th>Memberships</th></tr></thead><tbody>{atlas.treeCounts.map((item, index) => <tr key={item.tree}><td>{index + 1}</td><th>{item.tree}</th><td>{item.count.toLocaleString()}</td></tr>)}</tbody></table>
          <table><caption>TRACE documented relation counts</caption><thead><tr><th>Relation</th><th>Family</th><th>Edges</th></tr></thead><tbody>{atlas.relationTypes.map((item) => <tr key={item.label}><th>{item.label.replaceAll("_", " ")}</th><td>{FAMILY_LABELS[item.family]}</td><td>{item.count.toLocaleString()}</td></tr>)}</tbody></table>
        </div>
      </details>
    </section>
  );
}

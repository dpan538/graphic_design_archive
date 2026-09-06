import type { CSSProperties } from "react";
import Link from "next/link";
import {
  RELEASE,
  STATUS_EXITS,
  STATUS_INTRO,
  STATUS_OPEN,
  STATUS_STABLE,
  STATUS_TITLE,
} from "../../lib/content";
import { STATUS } from "../../lib/statusLayout";
import {
  BEFORE_1900,
  DRAW_CAPTION,
  DRAW_VH,
  HALF,
  HELD,
  IN_RANGE,
  LABELS_R,
  LENSES,
  PLACE_COLOR,
  PUBLIC,
  RB_AXIS_YEARS,
  RB_NB,
  RB_Y0,
  RB_Y1,
  TICKS,
  UNIT,
  VH,
  VW,
  shortNames,
  type LabelSlot,
} from "../../lib/statusRibbons";
import { RADIAL, S_H, STRIP_YEARS, TYPE_LEGEND, TYPE_OTHER, decades, stripCols } from "../../lib/statusFigures";
import styles from "./StatusSection.module.css";

type Props = {
  active: boolean;
  reducedMotion: boolean;
};

/* 04 · Research Status — one light ground. The mirrored ranked stream is
   GROWN over the first 1.5 viewport-heights of scroll: the axis draws
   itself, then the bands rise out of it one five-year slice at a time, the
   halation develops behind the growth front, the striae print, and the end
   labels light one by one. Three lens stations follow. Beside it the
   margin fills after half a viewport with a different table every 0.75,
   and every one of the 424 places rolls past underneath. The year strip
   grows across half a page; the reading has a page of its own. All v49. */

const cssVars = (o: Record<string, number | string>) => o as CSSProperties;
const fmt = (n: number) => n.toLocaleString("en-GB");
const pct = (y: number) => `${((y / VH) * 100).toFixed(2)}%`;
const r1 = (n: number) => Math.round(n * 10) / 10;
const X = (b: number) => r1((b * VW) / (RB_NB - 1));

/* ---- the figure's furniture ---- */
const tickRows = TICKS.flatMap((v) => [
  { v, y: HALF - v * UNIT, side: "public" as const },
  { v, y: HALF + v * UNIT, side: "held" as const },
]).filter((t) => t.y > 8 && t.y < VH - 8);

/* ---- the margin: what fills it, and when (viewport-heights) ---- */
const SLOTS = [
  { id: "region", a: 0.5, b: 1.45, name: `Records by place · ${STATUS.bands.length - 1} places and the rest` },
  { id: "sources", a: 1.4, b: 2.3, name: `Sources · top 25 of ${STATUS.meta.sources}` },
  { id: "types", a: 2.25, b: 3.05, name: `Object types · top 25 of ${STATUS.meta.types}` },
  { id: "rights", a: 3.0, b: 4.2, name: "Rights and dating" },
];
const RIGHTS_ROWS = [
  { label: "Source-viewer candidates", n: STATUS.meta.rights[0] },
  { label: "Open candidates (IMG03 metadata)", n: STATUS.meta.rights[1] },
  { label: "Rights review required", n: STATUS.meta.rights[2] },
  { label: "Thumbnail candidates", n: STATUS.meta.rights[3] },
  { label: "Other", n: STATUS.meta.rights[4] },
];
const DATING = (() => {
  let span = 0;
  let sum = 0;
  const comp = new Array<number>(5).fill(0);
  for (const o of STATUS.objects) {
    if (o[7] > 0) span += 1;
    sum += o[4];
    comp[Math.min(4, Math.floor(o[4] / 20))] += 1;
  }
  return { span, mean: Math.round(sum / STATUS.objects.length), comp };
})();
const maxBand = Math.max(...STATUS.bands.map((b) => b.total));
const bandNames = shortNames(STATUS.bands.map((b) => b.place));
const ledgerNames = shortNames(STATUS.ledger.map((l) => l.place));
const maxSource = STATUS.sources[0].count;
const maxType = STATUS.types[0].count;
const maxRights = Math.max(...RIGHTS_ROWS.map((r) => r.n));

/* The year strip and the wheel are computed once in ../../lib/statusFigures
   so the phone draws the same figures. */

/* Every ribbon, public then held, in one list; and one slice per bin. */
const ALL = [...PUBLIC.ribbons, ...HELD.ribbons];
/* The chart SVGs run 30% past the sheet top and bottom (viewBox −300…1300)
   so the overrunning bins stay INSIDE the SVG viewport: Chrome cuts a
   transformed slice's content at the viewport edge before scaling it, which
   showed as flat tops on the spikes while they grew. The figure box still
   crops what overruns. */
const OVER = 300;
const SLICES = Array.from({ length: RB_NB }, (_, b) => b);

function Labels({ slots }: { slots: LabelSlot[] }) {
  return (
    <div className={styles.labels} aria-hidden="true">
      <svg className={styles.leaders} viewBox={`0 0 100 ${VH}`} preserveAspectRatio="none">
        {slots.map((s, i) => (
          <line key={s.rb.key} x1={0} y1={s.anchor} x2={18} y2={s.y} stroke={s.rb.color} style={cssVars({ "--i": i })} />
        ))}
      </svg>
      {slots.map((s, i) => (
        <span
          key={s.rb.key}
          className={styles.label}
          data-group={s.rb.places ? "" : undefined}
          style={cssVars({ top: pct(s.y), color: s.rb.text, "--i": i })}
        >
          <span className={styles.labelName}>{s.rb.label}</span>
          <span className={styles.labelNum}>{fmt(s.rb.total)}</span>
        </span>
      ))}
    </div>
  );
}

export default function StatusSection({ reducedMotion }: Props) {
  return (
    <div className={styles.wrap} data-reduced={reducedMotion || undefined}>
      <div className={styles.pages}>
        {/* ================= plate 1 · the figure and its margin ================= */}
        <section className={styles.plate}>
          <header className={styles.head}>
            <span className={styles.headA}>04 · Research status · state of the archive · {RELEASE.version}</span>
            <span className={styles.headB}>
              {fmt(IN_RANGE)} records · {RB_Y0}–{RB_Y1}
            </span>
          </header>

          {/* The figure. Clipped here so the lens can overrun freely. */}
          <div className={styles.figure}>
            <div className={styles.chartRow} style={cssVars(Object.fromEntries(LENSES.flatMap((l, i) => [
              [`--k${i + 1}`, l.k],
              [`--x${i + 1}`, l.px],
              [`--y${i + 1}`, l.py],
              [`--t${i + 1}`, l.at],
            ])))}>
              <div className={styles.sheet}>
                {/* Layer 1 — the halation, developing a little behind the
                    growth front (a soft mask on this wrapper). */}
                <div className={styles.haloWrap} aria-hidden="true">
                  <svg viewBox={`0 ${-OVER} ${VW} ${VH + 2 * OVER}`} className={styles.chart} preserveAspectRatio="none">
                    <defs>
                      <filter id="rb-halo" x="-8%" y="-10%" width="116%" height="120%">
                        <feGaussianBlur stdDeviation="12" />
                      </filter>
                      <filter id="rb-halo-wide" x="-12%" y="-20%" width="124%" height="140%">
                        <feGaussianBlur stdDeviation="34" />
                      </filter>
                    </defs>
                    <g className={styles.haloWide}>
                      {ALL.map((r) => (
                        <path key={r.key} d={r.path} fill={r.color} />
                      ))}
                    </g>
                    <g className={styles.halo}>
                      {ALL.map((r) => (
                        <path key={r.key} d={r.path} fill={r.color} />
                      ))}
                    </g>
                  </svg>
                </div>
                {/* Layer 2 — the figure itself, GROWN from the axis. The band
                    set is defined once (in the chart SVG's defs) and drawn
                    26 times through <use>, each in its own small HTML box
                    clipped to one five-year bin. The boxes are what scale —
                    composited transforms, no SVG repaint per frame. */}
                <div className={styles.grow} aria-hidden="true">
                  {SLICES.map((b) => (
                    <div key={b} className={styles.sliceBox} style={cssVars({ "--b": b })}>
                      <svg viewBox={`0 ${-OVER} ${VW} ${VH + 2 * OVER}`} className={styles.sliceSvg} preserveAspectRatio="none">
                        <use href="#rb-bands" />
                      </svg>
                    </div>
                  ))}
                </div>
                {/* Layer 3 — grid, the axis drawing itself, the striae. */}
                <svg viewBox={`0 ${-OVER} ${VW} ${VH + 2 * OVER}`} className={styles.chart} preserveAspectRatio="none" aria-hidden="true">
                  <defs>
                    <pattern id="rb-striae" width="5" height="8" patternUnits="userSpaceOnUse">
                      <rect width="1.8" height="8" fill="#fff" />
                    </pattern>
                    <g id="rb-bands" className={styles.bandDefs}>
                      {ALL.map((r) => (
                        <path key={r.key} d={r.path} fill={r.color} />
                      ))}
                    </g>
                  </defs>
                  <g className={styles.gridLines}>
                    {tickRows.map((t) => (
                      <line key={`${t.side}${t.v}`} x1={0} x2={VW} y1={t.y} y2={t.y} />
                    ))}
                  </g>
                  <g className={styles.striae}>
                    {ALL.map((r) => (
                      <path key={r.key} d={r.path} />
                    ))}
                  </g>
                  <line className={styles.axisLine} x1={0} x2={VW} y1={HALF} y2={HALF} pathLength={1} />
                </svg>
                <div className={styles.ticksY} aria-hidden="true">
                  {tickRows.map((t) => (
                    <span key={`${t.side}${t.v}`} style={{ top: pct(t.y) }}>{fmt(t.v)}</span>
                  ))}
                  <span className={styles.tickZero} style={{ top: pct(HALF) }}>0</span>
                </div>
                <div className={styles.axisX} aria-hidden="true">
                  {RB_AXIS_YEARS.map((y, i) => (
                    <span key={y} style={cssVars({ "--i": i })}>{y}</span>
                  ))}
                </div>
              </div>
              <Labels slots={LABELS_R} />
            </div>
          </div>

          <footer className={styles.foot}>
            <div className={styles.captions}>
              {[
                { id: "the figure", a: 0.2, b: DRAW_VH + 0.05, text: DRAW_CAPTION },
                ...LENSES.map((l, i) => ({
                  id: l.id,
                  a: l.at + 0.05,
                  b: LENSES[i + 1]?.at ?? 3.9,
                  text: l.caption,
                })),
              ].map((c, i) => (
                <p key={c.id} className={styles.caption} style={cssVars({ "--a": c.a, "--b": c.b })}>
                  <span className={styles.captionIdx}>
                    {i === 0 ? "00" : `0${i}`} / 0{LENSES.length} · {c.id}
                  </span>
                  <span className={styles.captionText}>{c.text}</span>
                </p>
              ))}
            </div>
            <dl className={styles.legend}>
              <div><dt>Above the line</dt><dd>public · {fmt(PUBLIC.total)}</dd></div>
              <div><dt>Below the line</dt><dd>held · {fmt(HELD.total)}</dd></div>
              <div><dt>One ribbon</dt><dd>one place</dd></div>
              <div><dt>Thickness</dt><dd>per 5 years</dd></div>
              <div><dt>Colour</dt><dd>rank by total</dd></div>
              <div><dt>Before 1900</dt><dd>{fmt(BEFORE_1900)} · below</dd></div>
            </dl>
          </footer>

          {/* ---------------- the margin: a different table every 0.75 ---------------- */}
          <aside className={styles.aside}>
            <div className={styles.slots}>
              {SLOTS.map((s) => (
                <div key={s.id} className={styles.slot} style={cssVars({ "--a": s.a, "--b": s.b })}>
                  <p className={styles.slotName}>{s.name}</p>

                  {s.id === "region" && (
                    <div className={styles.rows} data-kind="region">
                      {STATUS.bands.map((b, i) => (
                        <span key={b.place} className={styles.row}>
                          <span className={styles.rowName} title={b.place}>{bandNames[i]}</span>
                          <span className={styles.rowBar}>
                            <i className={styles.barHeld} style={cssVars({ "--w": b.total / maxBand })} />
                            <i className={styles.barPub} style={cssVars({ "--w": b.public / maxBand, "--c": PLACE_COLOR.get(b.place) ?? "var(--ink)" })} />
                          </span>
                          <span className={styles.rowNum}>{fmt(b.total)}</span>
                          <span className={styles.rowSub} data-held={b.public === 0 ? "" : undefined}>
                            {b.public === 0 ? "held" : `${fmt(b.public)} public`}
                          </span>
                        </span>
                      ))}
                    </div>
                  )}

                  {s.id === "sources" && (
                    <div className={styles.rows}>
                      {STATUS.sources.map((r) => (
                        <span key={r.name} className={styles.row} data-two="">
                          <span className={styles.rowName}>{r.name}</span>
                          <span className={styles.rowBar}>
                            <i className={styles.barPub} style={cssVars({ "--w": r.count / maxSource })} />
                          </span>
                          <span className={styles.rowNum}>{fmt(r.count)}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {s.id === "types" && (
                    <div className={styles.rows}>
                      {STATUS.types.map((r) => (
                        <span key={r.name} className={styles.row} data-two="">
                          <span className={styles.rowName}>{r.name}</span>
                          <span className={styles.rowBar}>
                            <i className={styles.barPub} style={cssVars({ "--w": r.count / maxType })} />
                          </span>
                          <span className={styles.rowNum}>{fmt(r.count)}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {s.id === "rights" && (
                    <div className={styles.rightsBlock}>
                      <div className={styles.rows}>
                        {RIGHTS_ROWS.map((r) => (
                          <span key={r.label} className={styles.row} data-two="">
                            <span className={styles.rowName}>{r.label}</span>
                            <span className={styles.rowBar}>
                              <i className={r.label.startsWith("Rights review") ? styles.barRose : styles.barPub} style={cssVars({ "--w": r.n / maxRights })} />
                            </span>
                            <span className={styles.rowNum}>{fmt(r.n)}</span>
                          </span>
                        ))}
                      </div>
                      <dl className={styles.facts}>
                        <div><dt>Public / held</dt><dd>{fmt(RELEASE.eligible)} / {fmt(RELEASE.held)}</dd></div>
                        <div><dt>Dated across a span of years</dt><dd>{fmt(DATING.span)}</dd></div>
                        <div><dt>Mean completeness</dt><dd>{DATING.mean} / 100</dd></div>
                        <div><dt>Completeness ≥ 80</dt><dd>{fmt(DATING.comp[4])} of {fmt(STATUS.meta.objects)}</dd></div>
                      </dl>

                      {/* The wheel grows with its slot: spokes first, then
                          the blocks decade by decade from the hub. */}
                      <div className={styles.radial}>
                        <p className={styles.radialName}>Places × decades · 1900s → 2020s</p>
                        <div className={styles.radialRow}>
                          <svg viewBox="0 0 300 300" className={styles.radialSvg} aria-hidden="true">
                            <g className={styles.spokes}>
                              {RADIAL.spokes.map((sp) => (
                                <line key={sp.key} x1={sp.x1} y1={sp.y1} x2={sp.x2} y2={sp.y2} pathLength={1} />
                              ))}
                            </g>
                            <g className={styles.blocks}>
                              {RADIAL.blocks.map((b) => (
                                <path key={b.key} d={b.d} fill={b.fill} style={cssVars({ "--d": b.dec })} />
                              ))}
                            </g>
                          </svg>
                          <ul className={styles.radialLegend}>
                            {TYPE_LEGEND.map((t) => (
                              <li key={t.name} title={t.name}>
                                <i style={cssVars({ "--c": t.color })} />
                                <span>{t.short}</span>
                              </li>
                            ))}
                            <li>
                              <i style={cssVars({ "--c": TYPE_OTHER })} />
                              <span>other types</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Every place, in one scrolling wall. Totals and share published;
                no zero is printed — an empty bar says it. */}
            <div className={styles.wall}>
              <p className={styles.slotName}>Every place · {STATUS.ledger.length} · total and share published</p>
              <div className={styles.wallView}>
                <div className={styles.wallList}>
                  {STATUS.ledger.map((r, i) => (
                    <span key={r.place} className={styles.wallRow}>
                      <span className={styles.rowName} title={r.place}>{ledgerNames[i]}</span>
                      <span className={styles.rowNum}>{fmt(r.total)}</span>
                      <span className={styles.share}>
                        <i style={cssVars({ "--w": r.total ? r.public / r.total : 0, "--c": PLACE_COLOR.get(r.place) ?? "var(--ink)" })} />
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </section>

        {/* ================= plate 2 · the year strip, half a page ================= */}
        <section className={styles.pano}>
          <div className={styles.panoHead}>
            <span className={styles.panoTitle}>Every year · 1800–2026 · {fmt(STATUS.meta.objects)} records</span>
            <span className={styles.sub}>one column a year · blue — public · rose — held · depth of colour is records on a square-root scale</span>
          </div>
          <div className={styles.decades} aria-hidden="true">
            {decades.map((d, i) => (
              <span key={d.label} className={styles.decade} style={cssVars({ "--i": i, "--i0": d.i0, "--n": d.n })}>
                <b>{d.label}</b>
                <i>{fmt(d.total)}</i>
              </span>
            ))}
          </div>
          <figure className={styles.strip} aria-hidden="true">
            <svg viewBox={`0 0 ${stripCols.length} ${S_H}`} className={styles.stripSvg} preserveAspectRatio="none">
              {/* public on top, held beneath — the figure's own order */}
              <g className={styles.stripPub}>
                {stripCols.map((c) => (
                  <rect key={c.year} x={c.i + 0.08} y={0} width={0.84} height={c.hPub} style={cssVars({ "--i": c.i, "--k": c.k })} />
                ))}
              </g>
              <g className={styles.stripHeld}>
                {stripCols.map((c) => (
                  <rect key={c.year} x={c.i + 0.08} y={c.hPub} width={0.84} height={c.hHeld} style={cssVars({ "--i": c.i, "--k": c.k })} />
                ))}
              </g>
            </svg>
            <span className={styles.stripYears}>
              {STRIP_YEARS.map((y) => (
                <i key={y}>{y}</i>
              ))}
            </span>
          </figure>
        </section>

        {/* ================= the reading, a page of its own ================= */}
        <section className={styles.reading}>
          <h2 className={styles.title}>{STATUS_TITLE}</h2>
          <p className={styles.intro}>{STATUS_INTRO}</p>
          <dl className={styles.releaseRow}>
            <div><dt>Release</dt><dd>{RELEASE.version}</dd></div>
            <div><dt>Anchored</dt><dd>{RELEASE.date}</dd></div>
            <div><dt>Status</dt><dd>{RELEASE.status}</dd></div>
            <div><dt>Objects</dt><dd>{fmt(RELEASE.objects)}</dd></div>
            <div><dt>Public / held</dt><dd>{fmt(RELEASE.eligible)} / {fmt(RELEASE.held)}</dd></div>
          </dl>
          <div className={styles.lists}>
            <section className={styles.list}>
              <h3 className={styles.listHead}>Stable</h3>
              {STATUS_STABLE.map((r, i) => (
                <p key={r.term} className={styles.item} style={cssVars({ "--i": i })}>
                  <span className={styles.term}>{r.term}</span>
                  <span className={styles.line}>{r.line}</span>
                </p>
              ))}
            </section>
            <section className={styles.list}>
              <h3 className={styles.listHead}>Open</h3>
              {STATUS_OPEN.map((r, i) => (
                <p key={r.term} className={styles.item} style={cssVars({ "--i": i + 3 })}>
                  <span className={styles.term}>{r.term}</span>
                  <span className={styles.line}>{r.line}</span>
                </p>
              ))}
            </section>
          </div>
          <div className={styles.readingFoot}>
            <span className={styles.sub}>5,036 named creators · {STATUS.meta.sources} sources · {STATUS.ledger.length} places · {fmt(STATUS.meta.objects)} objects</span>
            <nav className={styles.exits}>
              {STATUS_EXITS.map((e) => (
                <Link key={e.href} href={e.href} className={styles.exit}>
                  {e.label}<span aria-hidden="true"> ↗</span>
                </Link>
              ))}
            </nav>
          </div>
        </section>
      </div>
    </div>
  );
}

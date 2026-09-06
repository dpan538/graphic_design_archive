import type { CSSProperties, ReactNode } from "react";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import TopButton from "@/components/site/mobile/TopButton";
import shell from "@/components/site/mobile/MobileShell.module.css";
import glyphs from "@/data/identity-glyphs.json";
import {
  IDENTITY_MARKS,
  IDENTITY_P1,
  IDENTITY_P2,
  IDENTITY_TAGLINE_SETTLED,
  RELEASE,
  STATUS_INTRO,
  STATUS_OPEN,
  STATUS_STABLE,
  STATUS_TITLE,
} from "../lib/content";
import { STATUS } from "../lib/statusLayout";
import { RADIAL, S_H, STRIP_YEARS, TYPE_LEGEND, TYPE_OTHER, stripCols } from "../lib/statusFigures";
import { BEFORE_1900, HALF, HELD, IN_RANGE, PUBLIC, RB_AXIS_YEARS, RB_NB, RB_Y0, RB_Y1, UNIT } from "../lib/statusRibbons";
import ContributionStage from "./ContributionStage";
import IdentityOpening from "./IdentityOpening";
import PinnedFigure from "./PinnedFigure";
import styles from "./HomeMobile.module.css";

/* Homepage, mobile (owner's brief, 2026-09-06): a simplification and a
   restructuring of the desktop page, in the phone's own files.
   01 one pinned page: black, the wordmark, the line in sky, the wipe to
      white and the two sentences, all on the scroll, before the page lets go;
   02 one pinned page — the core figures and the year chart, switching on
      scroll to the field, which grows in, with the paragraph and the
      tagline beneath it;
   03 (there is no Enter section on the phone — Index and Search are the
      bar's own controls, and the phone has no TRACE and no Source entry)
      three figures, each on a pinned page that grows with the scroll and
      lets go when the growth is complete — the ribbon sheet out of its
      axis, the wheel, the year strip — then the reading, with the ranked
      places and Stable and Open folded, and the Top control.
   Every number is v49; every figure is the desktop's own computation. */

const fmt = (n: number) => n.toLocaleString("en-GB");
const cssVars = (o: Record<string, number | string>) => o as CSSProperties;

/* ---- the identity sentence with its three key phrases marked, each lit on
   its own share of the opening's scroll (the desktop's IDENTITY_MARKS) ---- */
const HIGHLIGHT_FROM = 0.74;
const HIGHLIGHT_STEP = 0.06;
function markedLead(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let rest = text;
  let i = 0;
  for (const m of IDENTITY_MARKS) {
    const at = rest.indexOf(m.text);
    if (at < 0) continue;
    out.push(rest.slice(0, at));
    out.push(
      <mark key={m.id} className={styles.hl} data-i={i} style={cssVars({ "--from": (HIGHLIGHT_FROM + i * HIGHLIGHT_STEP).toFixed(2) })}>
        {m.text.replace(/-/g, "\u2011")}
      </mark>,
    );
    rest = rest.slice(at + m.text.length);
    i += 1;
  }
  out.push(rest);
  return out;
}

/* ---- the wordmark: the finished face, as outlines from the build script ---- */
type Face = { width: number; ink: number[]; capHeight: number; glyphs: { d: string; x: number }[] };
const SEED = (glyphs as unknown as { wordmark: { seed: Face } }).wordmark.seed;
const MARK_PAD = 40;
/* The box is read off the outlines, not the face's nominal cap height and
   baseline: the round letters overshoot both (the G by 15 above, 58 below),
   and a box cut at the nominal lines flattened them (owner, 2026-09-06). */
const MARK_BOX = (() => {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const g of SEED.glyphs) {
    const nums = (g.d.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
    for (let i = 0; i + 1 < nums.length; i += 2) {
      x0 = Math.min(x0, nums[i] + g.x); x1 = Math.max(x1, nums[i] + g.x);
      y0 = Math.min(y0, nums[i + 1]); y1 = Math.max(y1, nums[i + 1]);
    }
  }
  return { x: x0 - MARK_PAD, y: y0 - MARK_PAD, w: x1 - x0 + 2 * MARK_PAD, h: y1 - y0 + 2 * MARK_PAD };
})();

/* ---- the sheet on the phone: the same mirrored ranked stream, set as rows.
   Time runs down the page, one row per five-year bin; the axis is vertical,
   public records stack to its right and held records to its left, one block
   per place in the desktop's own stacking order and rank colour. Blocks, not
   curves: at a phone's width the desktop's bands wobble into noise, and a
   block keeps its edge at any size. ---- */
const SHEET_W = 1000;
const SHEET_H = 1000;
const ROW_H = SHEET_H / RB_NB;
const ROW_GAP = 3;
/* The two halves are unequal, so the axis is not centred: held runs to 750
   on the left, public to 1,250 on the right (owner, 2026-09-06), each span
   widened to the next 250 if a bin ever overran it. */
const STEP = 250;
const LEFT_SPAN = Math.max(750, Math.ceil(Math.max(...HELD.binTotals) / STEP) * STEP);
const RIGHT_SPAN = Math.max(1250, Math.ceil(Math.max(...PUBLIC.binTotals) / STEP) * STEP);
const KX = SHEET_W / (LEFT_SPAN + RIGHT_SPAN);
const AXIS_X = LEFT_SPAN * KX;
type Block = { key: string; x: number; w: number; fill: string };
const ROWS = Array.from({ length: RB_NB }, (_, b) => {
  const blocks: Block[] = [];
  for (const r of PUBLIC.ribbons) {
    const [top, bottom] = r.cols[b];
    const start = (HALF - bottom) / UNIT;
    const end = (HALF - top) / UNIT;
    if (end - start > 0) blocks.push({ key: r.key, x: AXIS_X + start * KX, w: (end - start) * KX, fill: r.color });
  }
  for (const r of HELD.ribbons) {
    const [top, bottom] = r.cols[b];
    const start = (top - HALF) / UNIT;
    const end = (bottom - HALF) / UNIT;
    if (end - start > 0) blocks.push({ key: r.key, x: AXIS_X - end * KX, w: (end - start) * KX, fill: r.color });
  }
  return { b, y: b * ROW_H + ROW_GAP / 2, h: ROW_H - ROW_GAP, blocks };
});
/* only 250 and 750 to the left, 250, 750 and 1,250 to the right, and 0 */
const SHEET_TICKS = [
  ...[250, 750].filter((v) => v <= LEFT_SPAN).map((v) => ({ v, x: AXIS_X - v * KX, side: "held" as const })),
  ...[250, 750, 1250].filter((v) => v <= RIGHT_SPAN).map((v) => ({ v, x: AXIS_X + v * KX, side: "public" as const })),
];
const YEAR_ROWS = RB_AXIS_YEARS.map((year) => ({ year, b: (year - RB_Y0) / 5 }));
const RANKED = [
  { id: "public", head: "Public, ranked", rows: PUBLIC.ribbons.filter((r) => !r.places).slice(0, 5) },
  { id: "held", head: "Held, ranked", rows: HELD.ribbons.filter((r) => !r.places).slice(0, 5) },
];

export default function HomeMobile() {
  return (
    <div className={`${shell.shell} ${styles.page}`}>
      <SiteNavMobile />

      <main className={styles.main}>
        {/* ================= 01 · Identity ================= */}
        <IdentityOpening
          tagline={IDENTITY_TAGLINE_SETTLED}
          lead={markedLead(IDENTITY_P1)}
          line={IDENTITY_P2}
          mark={
            <svg
              className={styles.wordmark}
              viewBox={`${MARK_BOX.x} ${MARK_BOX.y} ${MARK_BOX.w} ${MARK_BOX.h}`}
              role="img"
              aria-label="MGDA"
            >
              {SEED.glyphs.map((g, i) => (
                <path key={i} d={g.d} transform={`translate(${g.x} 0)`} fill="currentColor" />
              ))}
            </svg>
          }
        />

        {/* ================= 02 · Contribution ================= */}
        <ContributionStage />

        {/* ================= 03 · Research status ================= */}
        <section className={styles.status} aria-labelledby="status-title">
          {/* the ribbon sheet, grown out of its axis by the scroll */}
          <PinnedFigure className={styles.sheetWrap} height="200svh">
            <p className={styles.label}>03 · Research status · {RELEASE.version}</p>
            <p className={styles.figureHead}>
              {fmt(IN_RANGE)} records · {RB_Y0}–{RB_Y1}
            </p>
            <div className={styles.sheet} aria-hidden="true">
              <div className={styles.yearsY}>
                {YEAR_ROWS.map((r) => (
                  <span key={r.year} style={{ top: `${(((r.b + 0.5) / RB_NB) * 100).toFixed(2)}%` }}>{r.year}</span>
                ))}
              </div>
              <div className={styles.sheetBox}>
                <svg viewBox={`0 0 ${SHEET_W} ${SHEET_H}`} preserveAspectRatio="none" className={styles.sheetSvg} style={cssVars({ "--axis": `${((AXIS_X / SHEET_W) * 100).toFixed(2)}%` })}>
                  <g className={styles.gridLines}>
                    {SHEET_TICKS.map((t) => (
                      <line key={`${t.side}${t.v}`} x1={t.x} x2={t.x} y1={0} y2={SHEET_H} />
                    ))}
                  </g>
                  {ROWS.map((row) => (
                    <g key={row.b} className={styles.row} style={cssVars({ "--b": row.b })}>
                      {row.blocks.map((blk) => (
                        <rect key={blk.key} x={blk.x.toFixed(2)} y={row.y.toFixed(2)} width={blk.w.toFixed(2)} height={row.h.toFixed(2)} fill={blk.fill} shapeRendering="crispEdges" />
                      ))}
                    </g>
                  ))}
                  <line className={styles.axisLine} x1={AXIS_X} x2={AXIS_X} y1={0} y2={SHEET_H} pathLength={1} />
                </svg>
              </div>
              <div className={styles.countsX}>
                {SHEET_TICKS.map((t) => (
                  <span
                    key={`${t.side}${t.v}`}
                    data-edge={t.x <= 0 ? "start" : t.x >= SHEET_W ? "end" : undefined}
                    style={{ left: `${((t.x / SHEET_W) * 100).toFixed(2)}%` }}
                  >
                    {fmt(t.v)}
                  </span>
                ))}
                <span className={styles.tickZero} style={{ left: `${((AXIS_X / SHEET_W) * 100).toFixed(2)}%` }}>0</span>
              </div>
            </div>
            <dl className={styles.legend}>
              <div><dt>Right of axis</dt><dd>public · {fmt(PUBLIC.total)}</dd></div>
              <div><dt>Left of axis</dt><dd>held · {fmt(HELD.total)}</dd></div>
              <div><dt>One row</dt><dd>five years · one block one place · colour is rank by total</dd></div>
              <div><dt>Before 1900</dt><dd>{fmt(BEFORE_1900)} · on the strip below</dd></div>
            </dl>
          </PinnedFigure>

          {/* the wheel, spokes then blocks decade by decade, by the scroll */}
          <PinnedFigure className={styles.wheelWrap} height="190svh">
            <figure className={styles.wheel}>
              <figcaption className={styles.figureName}>
                Places × decades · 1900s → 2020s
                <span className={styles.figureSub}>the 60 largest places, one spoke each · colour is the decade's commonest object type</span>
              </figcaption>
              <svg viewBox="0 0 300 300" className={styles.wheelSvg} aria-hidden="true">
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
              <ul className={styles.wheelLegend}>
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
            </figure>
          </PinnedFigure>

          {/* the year strip, raised a column at a time, by the scroll */}
          <PinnedFigure className={styles.stripWrap} height="150svh">
            <figure className={styles.strip}>
              <figcaption className={styles.figureName}>
                Every year · 1800–2026 · {fmt(STATUS.meta.objects)} records
                <span className={styles.figureSub}>one column a year · blue is public · pink is held · depth of colour is records on a square-root scale</span>
              </figcaption>
              <div className={styles.plotBox}>
              <svg viewBox={`0 0 ${stripCols.length} ${S_H}`} className={styles.stripSvg} preserveAspectRatio="none" aria-hidden="true">
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
              </div>
              <span className={styles.stripYears} aria-hidden="true">
                {STRIP_YEARS.map((y) => (
                  <i key={y}>{y}</i>
                ))}
              </span>
            </figure>
          </PinnedFigure>

          {/* the reading */}
          <div className={styles.reading}>
            <h2 id="status-title" className={styles.title}>{STATUS_TITLE}</h2>
            <p className={styles.para}>{STATUS_INTRO}</p>
            <dl className={styles.release}>
              <div><dt>Release</dt><dd>{RELEASE.version} · {RELEASE.status}</dd></div>
              <div><dt>Anchored</dt><dd>{RELEASE.date}</dd></div>
              <div><dt>Objects</dt><dd>{fmt(RELEASE.objects)}</dd></div>
              <div><dt>Public · held</dt><dd>{fmt(RELEASE.eligible)} · {fmt(RELEASE.held)}</dd></div>
            </dl>
            <div className={styles.lists}>
              <details className={styles.fold}>
                <summary className={styles.summary}>
                  <span className={styles.listHead}>Ranked by place</span>
                  <span className={styles.summaryCount}>public · held</span>
                </summary>
                <div className={styles.ranked}>
                  {RANKED.map((list) => (
                    <section key={list.id} className={styles.rankedList}>
                      <h3 className={styles.rankedHead}>{list.head}</h3>
                      <ol className={styles.rankedRows}>
                        {list.rows.map((r) => (
                          <li key={r.key}>
                            <i style={cssVars({ "--c": r.color })} />
                            <span>{r.label}</span>
                            <b>{fmt(r.total)}</b>
                          </li>
                        ))}
                      </ol>
                    </section>
                  ))}
                </div>
              </details>
              {[
                { id: "stable", head: "Stable", rows: STATUS_STABLE },
                { id: "open", head: "Open", rows: STATUS_OPEN },
              ].map((list) => (
                <details key={list.id} className={styles.fold}>
                  <summary className={styles.summary}>
                    <span className={styles.listHead}>{list.head}</span>
                    <span className={styles.summaryCount}>{list.rows.length}</span>
                  </summary>
                  {list.rows.map((r) => (
                    <p key={r.term} className={styles.item}>
                      <span className={styles.term}>{r.term}</span>
                      <span className={styles.line}>{r.line}</span>
                    </p>
                  ))}
                </details>
              ))}
            </div>
          </div>
        </section>
      </main>
      <TopButton />
    </div>
  );
}

import type { RefObject } from "react";
import dynamic from "next/dynamic";
import {
  CONTRIBUTION_COLUMNS,
  CONTRIBUTION_INTRO,
  CONTRIBUTION_LEDGER,
  CONTRIBUTION_ROWS,
  FIELD_DETAIL,
  HISTO_TAGLINE,
  FIELD_TAGLINE,
  CONTRIBUTION_TITLE,
  CONTRIBUTION_YEAR,
  YEAR_TIERS,
  YEAR_TOTALS,
  YEAR_SCALE_MAX,
  YEAR_BINS_LABEL,
  FIELD_LABEL,
  HISTO_NOTES,
  FIELD_NOTES,
} from "../../lib/content";
import styles from "./ContributionSection.module.css";

const ContributionScene = dynamic(() => import("../../lib/ContributionScene"), { ssr: false });

type Props = {
  active: boolean;
  entered: boolean;
  progressRef: RefObject<number>;
  reducedMotion: boolean;
};

/* 1965 (849) is more than twice the next highest year, so the scale is set
   just above it rather than letting one bulk capture define the axis. */
const maxBin = YEAR_SCALE_MAX;

/* Break a two-clause line at its own punctuation. */
function splitAtPunctuation(line: string) {
  const at = line.search(/(?<=[.,])\s/);
  if (at < 0) return line;
  return (
    <>
      {line.slice(0, at)}
      <br />
      {line.slice(at + 1)}
    </>
  );
}

/* 02 · Contribution — a deliberate visual replication of the Coreaxis
   reference (HOMEPAGE_DESIGN_v1.md §4): explanatory white upper half over a
   blue lower half, concept diagram left, numbered table right. The lower
   half grows and the diagram builds as the section is scrolled. */
export default function ContributionSection({ active, progressRef, reducedMotion }: Props) {
  return (
    <div className={styles.wrap} data-reduced={reducedMotion || undefined}>
      {/* ---------------- Upper half — explanation ---------------- */}
      <div className={styles.upper}>
        <div className={styles.upperInner}>

          <h2 className={styles.title}>{CONTRIBUTION_TITLE}</h2>
          <p className={styles.intro}>{CONTRIBUTION_INTRO}</p>

          {/* The three figures ARE the three columns' markers — a separate
              ledger row above them repeated the same three-beat rhythm twice
              and ate the vertical space the lower half needed. */}
          <div className={styles.columns}>
            {CONTRIBUTION_COLUMNS.map((c, i) => (
              <section key={c.title} className={styles.column}>
                <p className={styles.figure}>{CONTRIBUTION_LEDGER[i].value}</p>
                <p className={styles.figureLabel}>{CONTRIBUTION_LEDGER[i].label}</p>
                <h3 className={styles.columnTitle}>
                  <span className={styles.bullet} aria-hidden="true" />
                  {c.title}
                </h3>
                <p className={styles.columnBody}>{c.body}</p>
              </section>
            ))}
          </div>
        </div>
      </div>

      {/* ---------------- Lower half — chart + table ---------------- */}
      <div className={styles.lower}>
        <div className={styles.lowerInner}>
          <figure className={styles.diagram}>
            {/* Stage one: a real 5-year histogram across the whole indexed
                span. It is cleared entirely before stage two begins. */}
            <div className={styles.histo}>
              <svg viewBox="0 0 460 200" preserveAspectRatio="none" className={styles.histoSvg} aria-hidden="true">
                {/* Two layers from one frozen release: every canonical
                    object, and the subset that is public. Largest first so the
                    public bar sits inside it — the unfilled height above each
                    solid bar is what remains held. */}
                {(["canonical", "public"] as const).map((tier, t) =>
                  YEAR_TIERS.map((row) => {
                    const year = row[0];
                    const count = row[t + 1];
                    const w = 460 / YEAR_TIERS.length;
                    const h = Math.min(count / maxBin, 1) * 176;
                    return (
                      <rect
                        key={`${tier}-${year}`}
                        className={styles.bin}
                        data-tier={tier}
                        x={(year - YEAR_TIERS[0][0]) * w + 0.14}
                        y={190 - h}
                        width={Math.max(w - 0.28, 0.5)}
                        height={h}
                        style={{
                          ["--i" as string]: +(
                            (year - YEAR_TIERS[0][0]) /
                            (YEAR_TIERS.length - 1)
                          ).toFixed(4),
                        }}
                      />
                    );
                  }),
                )}
              </svg>
              <div className={styles.histoAxis}>
                <span>{YEAR_TIERS[0][0]}</span>
                <span>
                  {YEAR_TOTALS.canonical.toLocaleString()} canonical ·{" "}
                  {YEAR_TOTALS.public.toLocaleString()} public
                </span>
                <span>{YEAR_TIERS[YEAR_TIERS.length - 1][0]}</span>
              </div>
            </div>

            {/* Stage two: drawn from nothing, not morphed from the bars. */}
            <div className={styles.sceneMount}>
              <ContributionScene
                progressRef={progressRef}
                active={active}
                staticFrame={reducedMotion}
              />
            </div>

            {/* The chart's own name sits at its top — the section heading
                belongs on the right, never here. */}
            {/* Each stage names itself. The field was inheriting the
                histogram's title, which described data it does not show. */}
            <p className={styles.chartName} data-stage="histo">{YEAR_BINS_LABEL}</p>
            <p className={styles.chartName} data-stage="field">{FIELD_LABEL}</p>

            {/* Annotations, so the field is readable rather than decorative. */}
            {/* Annotations for BOTH stages — the histogram was unexplained
                too, not just the field. */}
            <div className={styles.notes} data-stage="histo" aria-hidden="true">
              {HISTO_NOTES.map((n) => (
                <span key={n} className={styles.note}>{n}</span>
              ))}
            </div>
            <div className={styles.notes} data-stage="field" aria-hidden="true">
              {FIELD_NOTES.map((n) => (
                <span key={n} className={styles.note}>{n}</span>
              ))}
            </div>

          </figure>

          {/* ONE list of six, not two swapping stages. The headings are the
              section's spine and never change; each body comes up as the
              reader reaches it, and the closing paragraph lands last. That
              keeps the type and the reading identical at both ends of the
              scroll, which two different stage panels could not. */}
          <div className={styles.table}>
            <div className={styles.rows}>
              {CONTRIBUTION_ROWS.map((r, i) => (
                <div key={r.title} className={styles.tableRow}>
                  <span className={styles.rowNum}>{String(i + 1).padStart(2, "0")}</span>
                  <span className={styles.rowMain}>
                    <span className={styles.rowLabel}>{r.title}</span>
                    <span className={styles.rowBody} style={{ ["--r" as string]: i }}>
                      {r.body}
                    </span>
                  </span>
                </div>
              ))}
            </div>

            <p className={styles.fieldDetail}>{FIELD_DETAIL}</p>

            {/* The line belongs under the points it summarises, not above. */}
            {/* Broken at the punctuation rather than wherever the measure
                runs out — these are two-clause statements and a break mid-
                clause reads as an accident. */}
            {/* The year sits IN this band, not in a row of its own. Once the
                organisation name was dropped the footer became a near-empty
                strip whose dead space read as the statement above it being
                top-heavy — the box was centred, the composition was not. */}
            <div className={styles.tagline}>
              <span className={styles.headA}>{splitAtPunctuation(HISTO_TAGLINE)}</span>
              <span className={styles.headB}>{splitAtPunctuation(FIELD_TAGLINE)}</span>
              <span className={styles.footYear}>{CONTRIBUTION_YEAR}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

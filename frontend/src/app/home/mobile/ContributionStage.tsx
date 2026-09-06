"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  CONTRIBUTION_BODY,
  CONTRIBUTION_LEDGER,
  FIELD_LABEL,
  FIELD_TAGLINE,
  HISTO_NOTES,
  YEAR_BINS_LABEL,
  YEAR_TIERS,
  YEAR_TOTALS,
} from "../lib/content";
import styles from "./HomeMobile.module.css";
import { useStageProgress } from "./useStageProgress";

/* 02 · Contribution on the phone, after the desktop's own idea: the page
   pins on the year chart with the core figures beneath it, the scroll then moves only
   into the second chart — the desktop's field scene, drawn by the scroll
   from nothing to its finished frame, with the paragraph and the tagline on
   the same page beneath it — and the page lets go once the field is
   complete, into 03. */
const ContributionScene = dynamic(() => import("../lib/ContributionScene"), { ssr: false });
/* the stage's scroll: hold the first page, switch, then draw the field */
const SWITCH = 0.32;
const DRAW_FROM = 0.42;
const DRAW_TO = 0.94;
/* the scene's own drawing window (ContributionScene: seg(p, 0.4, 0.98)) */
const SCENE_FROM = 0.4;
const SCENE_TO = 0.98;
const first = YEAR_TIERS[0][0];
const last = YEAR_TIERS[YEAR_TIERS.length - 1][0];
const binW = 460 / YEAR_TIERS.length;
/* The one bulk-capture year is left off the phone's chart as an outlier
   (owner, 2026-09-06): at its scale every year before 1900 flattened to
   nothing. The scale is the next-highest year; the omission is printed. */
const PEAK = YEAR_TIERS.reduce((top, row) => (row[1] > top[1] ? row : top), YEAR_TIERS[0]);
const BINS = YEAR_TIERS.filter((row) => row !== PEAK);
const SCALE_MAX = Math.max(...BINS.map((row) => row[1]));
const OMITTED_NOTE = `${PEAK[0]} is left off — its ${PEAK[1].toLocaleString("en-GB")} records, one bulk capture, would flatten every other year`;
/* the tagline stands on two lines */
const [TAG_A, TAG_B] = FIELD_TAGLINE.includes(". ") ? [FIELD_TAGLINE.slice(0, FIELD_TAGLINE.indexOf(". ") + 1), FIELD_TAGLINE.slice(FIELD_TAGLINE.indexOf(". ") + 2)] : [FIELD_TAGLINE, ""];

export default function ContributionStage() {
  const ref = useRef<HTMLDivElement>(null);
  const [stage, setStage] = useState<"a" | "b">("a");
  const [near, setNear] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [reduced, setReduced] = useState(false);
  const progress = useRef(SCENE_FROM);

  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  const onProgress = useCallback((p: number, isNear: boolean) => {
    setNear(isNear);
    if (isNear) setMounted(true);
    setStage(p >= SWITCH ? "b" : "a");
    /* the field follows the scroll through its drawing window; the scene's
       loop repaints whenever this moves */
    const local = Math.min(1, Math.max(0, (p - DRAW_FROM) / (DRAW_TO - DRAW_FROM)));
    progress.current = SCENE_FROM + (SCENE_TO - SCENE_FROM) * local;
  }, []);
  useStageProgress(ref, onProgress);

  return (
    <div ref={ref} className={styles.contrib} data-stage={stage} data-reduced={reduced || undefined}>
      <div className={styles.contribStage}>
        <p className={styles.label}>02 · Contribution</p>

        <div className={styles.panelA} aria-hidden={stage !== "a"}>
          <figure className={styles.chart}>
            <figcaption className={styles.chartLabel}>{YEAR_BINS_LABEL}</figcaption>
            <div className={styles.histo}>
              <svg viewBox="0 0 460 200" preserveAspectRatio="none" className={styles.histoSvg} aria-hidden="true">
                {(["canonical", "public"] as const).map((tier, t) =>
                  BINS.map((row) => {
                    const h = Math.min(row[t + 1] / SCALE_MAX, 1) * 200;
                    return (
                      <rect
                        key={`${tier}-${row[0]}`}
                        className={styles.bin}
                        data-tier={tier}
                        x={(row[0] - first) * binW + 0.14}
                        y={200 - h}
                        width={Math.max(binW - 0.28, 0.5)}
                        height={h}
                      />
                    );
                  }),
                )}
              </svg>
              <div className={styles.axis}>
                <span>{first}</span>
                <span>
                  {YEAR_TOTALS.canonical.toLocaleString("en-GB")} canonical · {YEAR_TOTALS.public.toLocaleString("en-GB")} public
                </span>
                <span>{last}</span>
              </div>
            </div>
            <ul className={styles.notes}>
              {HISTO_NOTES.map((n, i) => (
                <li key={n} data-glyph={i === 0 ? "pair" : "held"}>{n}</li>
              ))}
              <li data-glyph="omitted">{OMITTED_NOTE}</li>
            </ul>
          </figure>
          <dl className={styles.ledger}>
            {CONTRIBUTION_LEDGER.map((l) => (
              <div key={l.label}>
                <dt>{l.value}</dt>
                <dd>{l.label}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className={styles.panelB} aria-hidden={stage !== "b"}>
          <figure className={styles.chart}>
            <figcaption className={styles.chartLabel}>
              {FIELD_LABEL}
              <span className={styles.chartSub}>marks are published records · stems are records still held, taller is further from publishable</span>
            </figcaption>
            <div className={styles.fieldMount}>
              {mounted ? <ContributionScene progressRef={progress} active={near && stage === "b"} staticFrame={reduced} fitWidth /> : null}
            </div>
          </figure>
          <p className={styles.stagePara}>{CONTRIBUTION_BODY}</p>
          <p className={styles.stageTagline}>
            {TAG_A}
            {TAG_B ? (
              <>
                <br />
                {TAG_B}
              </>
            ) : null}
          </p>
        </div>
      </div>
    </div>
  );
}

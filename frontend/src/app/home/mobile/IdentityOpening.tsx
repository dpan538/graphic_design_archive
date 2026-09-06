"use client";

import { useCallback, useRef, type ReactNode } from "react";
import styles from "./HomeMobile.module.css";
import { useStageProgress } from "./useStageProgress";

/* 01 · Identity on the phone (owner, 2026-09-06): one pinned page, and
   everything of Identity happens inside it, in the desktop closing's
   colours — black, the wordmark in paper, the settled line in sky, broken
   before "for". As the reader scrolls, the line comes on; then a paper
   sheet rises from the foot and the page is white; then the two sentences
   appear on the white; then, still on the scroll, the three key phrases
   are lit one after another; then the page lets go, and Contribution
   follows as the first continuous page. Progress is written to --p; the
   rest is CSS. */
const TAG_AT = 0.16;

export default function IdentityOpening({ mark, tagline, lead, line }: { mark: ReactNode; tagline: string; lead: ReactNode; line: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const onProgress = useCallback((p: number) => {
    const node = ref.current;
    if (!node) return;
    node.style.setProperty("--p", p.toFixed(3));
    node.dataset.stage = p >= TAG_AT ? "tag" : "mark";
  }, []);
  useStageProgress(ref, onProgress);
  const [tagA, tagB] = tagline.includes(" for ") ? tagline.split(" for ") : [tagline, ""];
  return (
    <div ref={ref} className={styles.opening} data-stage="mark">
      <div className={styles.openingStage}>
        <div className={styles.mark}>{mark}</div>
        <p className={styles.openingTag}>
          {tagA}
          {tagB ? (
            <>
              <br />
              for {tagB}
            </>
          ) : null}
        </p>
        <div className={styles.wipe} aria-hidden="true" />
        <div className={styles.describe}>
          <p className={styles.describeLead}>{lead}</p>
          <p className={styles.describeLine}>{line}</p>
        </div>
      </div>
    </div>
  );
}

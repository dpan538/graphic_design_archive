"use client";

import { useCallback, useRef, type ReactNode } from "react";
import styles from "./HomeMobile.module.css";
import { useStageProgress } from "./useStageProgress";

/* A figure on a pinned page (owner, 2026-09-06): the page pins when the
   figure arrives, the figure grows with the scroll, and the page lets go
   once the growth is complete. Progress is written to --p; the stylesheet
   derives the growth (--g) and each figure's own drawing from it. Without
   JavaScript --p is unset and the finished figure stands. */
export default function PinnedFigure({ children, className, height = "190svh" }: { children: ReactNode; className?: string; height?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const onProgress = useCallback((p: number) => {
    ref.current?.style.setProperty("--p", p.toFixed(3));
  }, []);
  useStageProgress(ref, onProgress);
  return (
    <div ref={ref} className={`${styles.pin} ${className ?? ""}`} style={{ height }}>
      <div className={styles.pinStage}>{children}</div>
    </div>
  );
}

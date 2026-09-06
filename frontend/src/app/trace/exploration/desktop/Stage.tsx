"use client";

import { useRef } from "react";
import type { ExplorationViewDto } from "@/features/trace-v49/exploration-view/types";
import { LOADING, STAGE_LABEL, STATUS } from "../lib/content";
import styles from "./Stage.module.css";
import StageCursor from "./StageCursor";

/* the view (§7i): the picture the server drew, inline and full-frame,
   centred on the canvas ground, flat — no shadow, and nothing in the
   picture changes on hover or click; a status line beneath. What answers
   the pointer is the CURSOR alone (StageCursor): over a term's motif, an
   association's shape or the picture's edge the drawn cursor changes its
   form, never the picture. No region outline ever shows. Nothing on it is
   a control. */

export interface StageProps {
  readonly view: ExplorationViewDto;
  readonly pending: string | null;
  readonly notice: string | null;
}

export default function Stage({ view, pending, notice }: StageProps) {
  const busy = pending !== null && pending !== "EXPORT";
  const stageRef = useRef<HTMLDivElement>(null);
  return (
    <div ref={stageRef} className={styles.stage} role="img" aria-label={`${STAGE_LABEL} ${view.scene.altText}`} aria-busy={busy || undefined} data-template={view.presentation.template_id}>
      <div className={styles.sheet} data-busy={busy ? "true" : "false"}>
        <div className={styles.picture} dangerouslySetInnerHTML={{ __html: view.svg }} />
      </div>
      <StageCursor stageRef={stageRef} />
      <p className={styles.status} aria-live="polite">
        {busy ? LOADING : STATUS(view.starting_point.label, view.map.nodes.length, view.map.associations.length)}
      </p>
      {notice ? <p className={styles.notice} role="status">{notice}</p> : null}
    </div>
  );
}

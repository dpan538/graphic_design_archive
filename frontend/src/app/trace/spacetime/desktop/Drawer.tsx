"use client";

import type { ReactNode } from "react";
import { DRAWER_CLOSE, MATCHING, RANKING_TITLE } from "../lib/content";
import styles from "./Drawer.module.css";

/* 04 · 05 — the one drawer under the map (§7h): the matching records or
   the place ranking, one at a time, chosen by two tabs; closed until
   asked for, so the map keeps its size. */

export type DrawerTab = "records" | "table";

export interface DrawerProps {
  readonly open: DrawerTab;
  readonly recordsAvailable: boolean;
  readonly recordCount: number | null;
  readonly geographyCount: number;
  readonly onTab: (tab: DrawerTab) => void;
  readonly onClose: () => void;
  readonly children: ReactNode;
}

export default function Drawer({ open, recordsAvailable, recordCount, geographyCount, onTab, onClose, children }: DrawerProps) {
  return (
    <section id="spacetime-drawer" className={styles.drawer} tabIndex={-1}>
      <div className={styles.tabs} role="tablist">
        {recordsAvailable ? (
          <button type="button" role="tab" aria-selected={open === "records"} className={styles.tab} onClick={() => onTab("records")}>
            {MATCHING}{recordCount !== null ? <span className={`${styles.tabCount} tnum`}>{recordCount.toLocaleString("en-US")}</span> : null}
          </button>
        ) : null}
        <button type="button" role="tab" aria-selected={open === "table"} className={styles.tab} onClick={() => onTab("table")}>
          {RANKING_TITLE}<span className={`${styles.tabCount} tnum`}>{geographyCount}</span>
        </button>
        <button type="button" className={styles.close} onClick={onClose}>{DRAWER_CLOSE}</button>
      </div>
      <div className={styles.body} role="tabpanel">{children}</div>
    </section>
  );
}

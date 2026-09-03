"use client";

import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import type { ObjectRecord as Rec } from "../lib/fixture";
import type { LayoutId } from "../lib/record";
import ObjectRecord from "./ObjectRecord";
import styles from "./ObjectDesktop.module.css";

/* Ticket-stub archive tag — a CSS barcode + record number + a stamped year. */
function RecordTag({ rec }: { rec: Rec }) {
  return (
    <span className={styles.recTag} aria-hidden="true">
      <span className={styles.recBars} />
      <span className={styles.recNo}>{rec.surfaceId}</span>
      <span className={styles.recStamp}>{rec.year ?? ""}</span>
    </span>
  );
}

/* The desktop object page over a real record. The five layout treatments
   from the design round remain selectable with ?layout=1..5 for review;
   the page otherwise reads in the first. */
export default function ObjectDesktop({ rec, recordOnly = false }: { rec: Rec; recordOnly?: boolean }) {
  const [layout, setLayout] = useState<LayoutId>(1);

  useEffect(() => {
    const l = Number(new URLSearchParams(window.location.search).get("layout"));
    if (l >= 1 && l <= 5) setLayout(l as LayoutId);
  }, []);

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav />

      <div className={styles.backbar}>
        <div className={styles.backLeft}>
          <button
            type="button"
            className={styles.backTile}
            aria-label="Back to where you came from"
            onClick={() => {
              if (typeof window !== "undefined" && window.history.length > 1) {
                window.history.back();
              } else {
                window.location.href = "/directory";
              }
            }}
          >
            <ArrowLeft size={26} strokeWidth={3} aria-hidden="true" />
          </button>
          <span className={styles.crumb}>
            Index · Search &nbsp;→&nbsp; <b>{recordOnly ? "Archive record" : "Object record"}</b>
          </span>
        </div>
        <RecordTag rec={rec} />
      </div>

      <main id="main">
        <ObjectRecord rec={rec} layout={layout} recordOnly={recordOnly} />
      </main>
    </div>
  );
}

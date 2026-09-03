"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, ArrowUp } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import type { ObjectRecord as Rec } from "../lib/fixture";
import MobileRecord from "./MobileRecord";
import styles from "./ObjectMobile.module.css";

/* Mobile path (§4a) — its own tree. Nav is MGDA · Index · About; the record is a
   single-column read with non-essential blocks folded and a back-to-top control. */
export default function ObjectMobile({ rec, recordOnly = false }: { rec: Rec; recordOnly?: boolean }) {
  const [showTop, setShowTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 560);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav variant="mobile" />

      <div className={styles.backbar}>
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
          <ArrowLeft size={22} strokeWidth={3} aria-hidden="true" />
        </button>
        <span className={styles.crumb}>Object record</span>
      </div>

      <main id="main">
        <MobileRecord rec={rec} recordOnly={recordOnly} />
      </main>

      <button
        type="button"
        className={styles.toTop}
        data-show={showTop || undefined}
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      >
        <ArrowUp size={18} strokeWidth={3} aria-hidden="true" />
        Top
      </button>
    </div>
  );
}

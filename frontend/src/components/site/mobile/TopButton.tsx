"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";
import styles from "./TopButton.module.css";

/* The phone's one back-to-top control (owner, 2026-09-06): fixed at the
   foot, right, shown once the reader is down the page. The same component
   on About, Index and the homepage. */
export default function TopButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 640);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <button
      type="button"
      className={styles.toTop}
      data-show={show || undefined}
      onClick={() => {
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
      }}
    >
      <ArrowUp size={18} strokeWidth={3} aria-hidden="true" />
      Top
    </button>
  );
}

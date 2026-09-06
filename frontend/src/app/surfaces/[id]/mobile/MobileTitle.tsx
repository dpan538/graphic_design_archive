"use client";

import { useState } from "react";
import styles from "./MobileTitle.module.css";

/* The record's title on the phone (owner 2026-09-06): a long title — a
   broadside's whole first page, at times — stands folded to three lines by
   default, with one 44 px control to read it in full; a short title stands
   whole. The h1 always carries the full text for assistive technology. */
const FOLD_AT = 72;

export default function MobileTitle({ title }: { title: string }) {
  const long = title.length > FOLD_AT;
  const [open, setOpen] = useState(false);
  return (
    <div className={styles.wrap}>
      <h1 className={styles.title} data-folded={long && !open ? "true" : undefined}>{title}</h1>
      {long ? (
        <button type="button" className={styles.toggle} aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {open ? "Shorter title" : "Full title"}
        </button>
      ) : null}
    </div>
  );
}

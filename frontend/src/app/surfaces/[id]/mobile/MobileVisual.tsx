"use client";

import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { altString, type Rec } from "../lib/record";
import styles from "./MobileVisual.module.css";

/* Layer 1, mobile — the same modes as the desktop layer (§3d): the image
   from the visual registry with its attribution, or a sentence and one
   clear "View at source" action; never an empty frame. Alt text folds
   behind "+". */
export default function MobileVisual({ rec }: { rec: Rec }) {
  const [open, setOpen] = useState(false);
  const v = rec.visual;
  const alt = altString(rec);

  if (v.mode === "displayable" && v.imageUrl) {
    return (
      <div className={styles.vb}>
        <span className={styles.label}>Visual record</span>
        <figure className={styles.figure}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className={styles.image} src={v.imageUrl} alt={alt} loading="lazy" decoding="async" />
          <figcaption className={styles.caption}>
            {v.attribution ? <span>{v.attribution}</span> : null}
            {v.licence ? <span>{v.licence}</span> : null}
            {v.sourceUrl ? (
              <a className={styles.srcLink} href={v.sourceUrl} target="_blank" rel="noreferrer">
                Original source <ArrowUpRight size={14} strokeWidth={3} aria-hidden="true" />
              </a>
            ) : null}
          </figcaption>
        </figure>
      </div>
    );
  }

  const lead =
    v.mode === "source-viewer"
      ? "The visual is viewable at the holding institution."
      : v.mode === "link"
        ? "A source record page exists; no visual is delivered."
        : "Citation only; no visual is delivered.";

  return (
    <div className={styles.vb}>
      <span className={styles.label}>Visual record</span>
      <p className={styles.lead}>{lead} No image is displayed in MGDA for this object in the current release.</p>
      {v.sourceUrl ? (
        <a className={styles.action} href={v.sourceUrl} target="_blank" rel="noreferrer">
          {v.mode === "source-viewer" ? "View at source" : "Open the source record"}
          <ArrowUpRight size={18} strokeWidth={3} aria-hidden="true" />
        </a>
      ) : null}
      <dl className={styles.info}>
        <div>
          <dt>Alt text</dt>
          <dd>
            <span className={styles.clamp} data-open={open || undefined}>
              {alt}
              <span className={styles.hint}> — from catalogue fields, for readers and machines; not an interpretive caption.</span>
            </span>
            <button type="button" className={styles.more} aria-expanded={open} onClick={() => setOpen((x) => !x)}>
              {open ? "– less" : "… +"}
            </button>
          </dd>
        </div>
      </dl>
    </div>
  );
}

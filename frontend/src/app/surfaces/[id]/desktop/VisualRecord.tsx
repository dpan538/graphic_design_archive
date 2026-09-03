import { ArrowUpRight } from "lucide-react";
import { altString, type Rec } from "../lib/record";
import styles from "./VisualRecord.module.css";

/* Layer 1 — the visual record, in one of the modes of §3d:
   A  displayable     the image, rendered from the visual registry's URL, with
                      its attribution, its licence and the original source;
   B  source-viewer   no image box of any kind — a plain sentence and one
                      clear action, "View at source";
      link / citation the same block with the source record page, or none.
   Record-only pages do not render this layer (ObjectRecord). Nothing here
   binds an <img> to archive metadata; the image URL is the registry's. */
export default function VisualRecord({ rec }: { rec: Rec }) {
  const v = rec.visual;
  const alt = altString(rec);

  if (v.mode === "displayable" && v.imageUrl) {
    return (
      <section className={styles.vb}>
        <span className={styles.vbLabel}>Visual record</span>
        <figure className={styles.vbFigure}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className={styles.vbImage} src={v.imageUrl} alt={alt} loading="lazy" decoding="async" />
          <figcaption className={styles.vbCaption}>
            {v.attribution ? <span>{v.attribution}</span> : null}
            {v.licence ? <span>{v.licence}</span> : null}
            {v.sourceUrl ? (
              <a className={styles.srcLink} href={v.sourceUrl} target="_blank" rel="noreferrer">
                Original source <ArrowUpRight size={14} strokeWidth={3} aria-hidden="true" />
              </a>
            ) : null}
          </figcaption>
        </figure>
      </section>
    );
  }

  const lead =
    v.mode === "source-viewer"
      ? "The visual is viewable at the holding institution."
      : v.mode === "link"
        ? "A source record page exists; no visual is delivered."
        : "Citation only; no visual is delivered.";

  return (
    <section className={styles.vb}>
      <span className={styles.vbLabel}>Visual record</span>
      <div className={styles.vbBody}>
        <p className={styles.vbLead}>
          {lead} No image is displayed in MGDA for this object in the current release.
        </p>
        {v.sourceUrl ? (
          <a className={styles.srcAction} href={v.sourceUrl} target="_blank" rel="noreferrer">
            {v.mode === "source-viewer" ? "View at source" : "Open the source record"}
            <ArrowUpRight size={18} strokeWidth={3} aria-hidden="true" />
            <span className={styles.srcHost}>{v.sourceLabel}</span>
          </a>
        ) : null}
        <dl className={styles.vbInfo}>
          <div>
            <dt>Alt text</dt>
            <dd>
              {alt}
              <span className={styles.vbHint}> — from catalogue fields, for readers and machines; not an interpretive caption.</span>
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

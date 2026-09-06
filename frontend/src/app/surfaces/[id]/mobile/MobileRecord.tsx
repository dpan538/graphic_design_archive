import type { Rec } from "../lib/record";
import MobileTitle from "./MobileTitle";
import MobileVisual from "./MobileVisual";
import MobileMeta from "./MobileMeta";
import MobileDescription from "./MobileDescription";
import MobileProvenance from "./MobileProvenance";
import styles from "./MobileRecord.module.css";

function LayerHead({ n, name, tone }: { n: string; name: string; tone: string }) {
  return (
    <div className={styles.layerHead} style={{ ["--lc" as string]: `var(--l-${tone})` }}>
      <span className={styles.layerNum}>{n}</span>
      <span className={styles.layerName}>{name}</span>
    </div>
  );
}

/* Single-column mobile read (§4a). Layer order matches desktop: visual record →
   identity → catalogue metadata → description → source / citation / provenance. */
export default function MobileRecord({ rec, recordOnly = false }: { rec: Rec; recordOnly?: boolean }) {
  const desc = recordOnly ? null : rec.description;

  return (
    <div className={styles.record}>
      <header className={styles.head}>
        <span className={styles.eyebrow}>{recordOnly ? "Archive record" : "MGDA record"}</span>
        <MobileTitle title={rec.title} />
        <p className={styles.identLine}>
          {[rec.surfaceId, rec.typeLabel, rec.displayDate, rec.placeLabel]
            .filter(Boolean)
            .join("  ·  ")}
        </p>
        {recordOnly ? (
          <p className={styles.recordNotice}>
            This record is retained for catalogue and provenance purposes. No reader-facing visual or
            descriptive object content is currently available, and it is not listed in the Index.
          </p>
        ) : null}
      </header>

      {recordOnly ? null : (
        <section className={styles.sec}>
          <MobileVisual rec={rec} />
        </section>
      )}

      <section className={styles.sec}>
        <LayerHead n="03" name="Catalogue metadata" tone="meta" />
        <MobileMeta rec={rec} />
      </section>

      {desc ? (
        <section className={styles.sec}>
          <LayerHead n="04" name="Description" tone="desc" />
          <MobileDescription text={desc} />
        </section>
      ) : null}

      <section className={styles.sec}>
        <LayerHead n="05" name="Source · Citation · Provenance" tone="src" />
        <MobileProvenance rec={rec} />
      </section>
    </div>
  );
}

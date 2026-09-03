import { rowsFor, type Rec } from "../lib/record";
import styles from "./CatalogueMetadata.module.css";

/* Layer 3 — identity fields as a grid. Column count comes from content-fit
   (fitLayout.ts) via `cols`; the first column is always the wider one. Empty
   fields are omitted, not shown as "Not recorded". */
export function MetaPairs({ rec, cols }: { rec: Rec; cols: number }) {
  const { identity } = rowsFor(rec);
  return (
    <div className={styles.meta} data-cols={cols}>
      {identity.map(([label, value]) =>
        value ? (
          <div key={label}>
            <span className={styles.metaLabel}>{label}</span>
            <span className={styles.metaValue}>{value}</span>
          </div>
        ) : null,
      )}
    </div>
  );
}

/* Classification (theme / movement) — always shown; "Not recorded" when empty,
   since a reader needs to know the archive holds no value rather than guess. */
export function Classification({ rec, cols }: { rec: Rec; cols: number }) {
  const { classification } = rowsFor(rec);
  return (
    <div className={styles.classif} data-cols={cols}>
      {classification.map(([label, value]) => (
        <div key={label}>
          <span className={styles.metaLabel}>{label}</span>
          <span className={styles.metaValue} data-empty={!value ? "true" : undefined}>
            {value || "Not recorded"}
          </span>
        </div>
      ))}
    </div>
  );
}

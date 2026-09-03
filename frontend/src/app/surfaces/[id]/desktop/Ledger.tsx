import type { Row } from "../lib/record";
import styles from "./Ledger.module.css";

/* Compact whole-record ledger — every field as a `label | value` row, grouped.
   Used by layouts 2 and 3. */
export default function Ledger({
  groups,
}: {
  groups: { title: string; rows: Row[] }[];
}) {
  return (
    <div className={styles.ledgerGrid}>
      {groups.map((g) => (
        <div key={g.title} className={styles.lgroupWrap}>
          <p className={styles.lgroup}>{g.title}</p>
          {g.rows.map(([l, v]) => (
            <dl key={l} className={styles.lrow}>
              <dt>{l}</dt>
              <dd data-empty={!v ? "true" : undefined}>{v || "Not recorded"}</dd>
            </dl>
          ))}
        </div>
      ))}
    </div>
  );
}

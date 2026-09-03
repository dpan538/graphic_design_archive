import { rowsFor, type Rec } from "../lib/record";
import styles from "./MobileMeta.module.css";

/* Layer 3, mobile — identity + classification as one stacked list, no columns. */
export default function MobileMeta({ rec }: { rec: Rec }) {
  const { identity, classification } = rowsFor(rec);
  const rows: [string, string][] = [
    ...identity.filter((r): r is [string, string] => Boolean(r[1])),
    ...classification.map(([l, v]): [string, string] => [l, v ?? "Not recorded"]),
  ];
  return (
    <dl className={styles.list}>
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd data-empty={value === "Not recorded" ? "true" : undefined}>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

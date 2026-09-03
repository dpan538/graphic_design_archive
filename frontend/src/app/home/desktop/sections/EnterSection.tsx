import Link from "next/link";
import { ENTER_TITLE, ENTRIES } from "../../lib/content";
import styles from "./EnterSection.module.css";

/* 03 · Enter the Archive — three stacked cards over the section's own ground.
   Each card is full-pane width and anchored to the bottom at a decreasing
   height (0.8 / 0.6 / 0.4), so the stack reads as three bands: the taller a
   card, the further back it sits. No ordinals — Index, Search and TRACE are
   peers, and numbering them would invent a sequence. */
export default function EnterSection() {
  return (
    <div className={styles.wrap}>
      <h2 className={styles.title}>{ENTER_TITLE}</h2>

      <div className={styles.stack}>
        {ENTRIES.map((e) => (
          <Link
            key={e.name}
            href={e.href}
            className={styles.card}
            data-card={e.name.toLowerCase()}
          >
            <span className={styles.cardInner}>
              <span className={styles.cardHead}>
                <span className={styles.cardName}>{e.name}</span>
                <span className={styles.cardVerb}>{e.verb}</span>
                {e.note ? <span className={styles.cardNote}>{e.note}</span> : null}
              </span>
              <span className={styles.cardBody}>
                <span className={styles.cardWhen}>{e.when}</span>
                <span className={styles.cardLine}>{e.line}</span>
              </span>
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

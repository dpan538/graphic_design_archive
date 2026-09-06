import Link from "next/link";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import shell from "@/components/site/mobile/MobileShell.module.css";
import {
  CONTRIBUTION_BODY,
  CONTRIBUTION_LEDGER,
  CONTRIBUTION_SINCE,
  ENTRIES,
  IDENTITY,
  RESEARCH_STATUS,
} from "../lib/content";
import styles from "./HomeMobile.module.css";

/* Homepage, mobile (§7e) — the same four sections, stacked, big bold type on the
   flat grey ground, no grid choreography. */
export default function HomeMobile() {
  return (
    <div className={`${shell.shell} ${styles.page}`}>
      <SiteNavMobile />

      <main className={styles.main}>
        <section className={styles.identity}>
          <p className={styles.kicker}>Modern Graphic Design Archive</p>
          <p className={styles.identityText}>{IDENTITY}</p>
        </section>

        <section className={styles.block}>
          <p className={styles.label}>02 · Contribution</p>
          <p className={styles.since}>{CONTRIBUTION_SINCE}</p>
          <dl className={styles.ledger}>
            {CONTRIBUTION_LEDGER.map((l) => (
              <div key={l.label}>
                <dt>{l.value}</dt>
                <dd>{l.label}</dd>
              </div>
            ))}
          </dl>
          <p className={styles.body}>{CONTRIBUTION_BODY}</p>
        </section>

        <section className={styles.block}>
          <p className={styles.label}>03 · Enter the archive</p>
          {/* Mobile is still frozen on its existing build; this follows the
              data only. The ordinals are gone product-wide — Index, Search and
              TRACE are peers, and numbering them implied a sequence. */}
          <ul className={styles.entries} role="list">
            {ENTRIES.map((e) => (
              <li key={e.name}>
                <Link href={e.href} className={styles.entry}>
                  <span className={styles.entryHead}>
                    <span className={styles.entryName}>{e.name}</span>
                  </span>
                  <span className={styles.entryLine}>
                    {e.verb}
                    {e.note ? <em className={styles.entryNote}> — {e.note}</em> : null}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className={styles.block}>
          <p className={styles.label}>04 · Research status</p>
          <p className={styles.statusText}>{RESEARCH_STATUS}</p>
        </section>
      </main>
    </div>
  );
}

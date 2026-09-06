import SiteNav from "@/components/site/SiteNav";
import Dock from "../../_shared/Dock";
import { FAILURE_NOTE, FAILURE_TITLE, KICKER, NAME, STATEMENT } from "../lib/content";
import styles from "./SpacetimeFailure.module.css";

/* 08 — the fail-closed page (§7h): the same shell, the view's name,
   the reader's failure message, the note that nothing was sent. No
   geometry, no atlas, no records. */

export default function SpacetimeFailure({ message }: Readonly<{ message: string }>) {
  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNav active="trace" revealTone="light" />
      <Dock active="spacetime" />
      <main id="main" className={styles.main}>
        <div className={styles.left}>
          <p className={styles.kicker}>{KICKER}</p>
          <h1 className={styles.name}>{NAME}</h1>
          <p className={styles.statement}>{STATEMENT}</p>
        </div>
        <section className={styles.failure} aria-labelledby="spacetime-failure-heading">
          <h2 id="spacetime-failure-heading" className={styles.title}>{FAILURE_TITLE}</h2>
          <p role="alert" className={styles.message}>{message}</p>
          <p className={styles.note}>{FAILURE_NOTE}</p>
        </section>
      </main>
    </div>
  );
}

import SiteNav from "@/components/site/SiteNav";
import type { GovernedContextExampleOption, GovernedContextSampleOption } from "@/features/trace-v49/context/governed/types";
import { FAILURE_NOTE, FAILURE_TITLE, RETRY } from "../lib/content";
import Dock from "./Dock";
import PageHeader from "./PageHeader";
import styles from "./ContextFailure.module.css";

/* 08 — the fail-closed page (§7g): the same shell, the header with the
   change-object forms open and the requested ID kept for correction,
   the reader's own failure code and message, and one way forward — the
   same governed request again. No dataset is mounted, no composition is
   read or written; nothing stands in for the canvas. */

export interface ContextFailureProps {
  readonly code: string;
  readonly message: string;
  readonly requestedId: string;
  readonly examples: readonly GovernedContextExampleOption[];
  readonly qaSamples: readonly GovernedContextSampleOption[] | null;
  readonly cohort: string;
  readonly retryHref: string | null;
}

export default function ContextFailure({ code, message, requestedId, examples, qaSamples, cohort, retryHref }: ContextFailureProps) {
  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNav active="trace" revealTone="light" />
      <Dock active="context" />
      <main id="main" className={styles.main}>
        <div className={styles.left}>
          <PageHeader selected={null} requestedId={requestedId} examples={examples} qaSamples={qaSamples} cohort={cohort} changeOpen />
        </div>
        <section className={styles.failure} aria-labelledby="context-failure-heading">
          <p className={`${styles.code} tnum`}>{code}</p>
          <h2 id="context-failure-heading" className={styles.title}>{FAILURE_TITLE}</h2>
          <p role="alert" className={styles.message}>{message}</p>
          <p className={styles.note}>{FAILURE_NOTE}</p>
          {retryHref ? <a className={styles.retry} href={retryHref}>{RETRY}</a> : null}
        </section>
      </main>
    </div>
  );
}

import Link from "next/link";
import type { GovernedContextExampleOption, GovernedContextSampleOption } from "@/features/trace-v49/context/governed/types";
import { KICKER, NAME, SELECTED_OBJECT, STATEMENT } from "../lib/content";
import ObjectChooser from "./ObjectChooser";
import styles from "./PageHeader.module.css";

/* 01 — the rail's head (§7g): the view's name under its TRACE kicker,
   the owner's one-sentence statement, and the selected object as a
   compact summary — its title and stable ID only; the object itself
   stands once, on the canvas. Under it the object chooser: a search by
   title or ID, the worked examples, the exact record ID behind a fold —
   folded while an object is selected, open on the landing and the
   failure page. The deterministic samples are a QA fold, development or
   ?qa=1 only. */

export interface SelectedObjectSummary {
  readonly title: string;
  readonly stableId: string;
}

export interface PageHeaderProps {
  readonly selected: SelectedObjectSummary | null;
  readonly requestedId: string;
  readonly examples: readonly GovernedContextExampleOption[];
  readonly qaSamples: readonly GovernedContextSampleOption[] | null;
  readonly cohort: string;
  readonly changeOpen?: boolean;
}

export default function PageHeader({ selected, requestedId, examples, qaSamples, cohort, changeOpen = false }: PageHeaderProps) {
  return (
    <header className={styles.header}>
      <p className={styles.kicker}>
        <Link href="/trace">{KICKER}</Link>
      </p>
      <h1 className={styles.name}>{NAME}</h1>
      <p className={styles.statement}>{STATEMENT}</p>

      {selected ? (
        <section className={styles.object} aria-labelledby="selected-object-heading">
          <h2 id="selected-object-heading" className={styles.label}>{SELECTED_OBJECT}</h2>
          <p className={styles.title} title={selected.title}>{selected.title.trim() || selected.stableId}</p>
          <p className={`${styles.id} tnum`}>{selected.stableId}</p>
        </section>
      ) : null}

      <ObjectChooser
        examples={examples}
        qaSamples={qaSamples}
        cohort={cohort}
        requestedId={requestedId}
        open={changeOpen}
        standalone={selected === null}
      />
    </header>
  );
}

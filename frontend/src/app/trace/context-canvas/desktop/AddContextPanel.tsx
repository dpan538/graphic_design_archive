import type { PresentedDimension } from "../lib/presentation";
import {
  ADD_CONTEXT_NOTE,
  ADD_CONTEXT_TITLE,
  ADD_TERM,
  BACK_TO_INSPECTOR,
  NO_ADDITIONAL,
  ROW_ADD,
} from "../lib/content";
import styles from "./AddContextPanel.module.css";

/* 04b — ADD CONTEXT (§7g): the right panel in its second mode, opened by
   the dock's "+": the governed context this object carries that is not
   on the canvas, grouped Medium · Theme · Movement — "No additional
   context" where there is none — each with one explicit Add. Nothing
   can be searched for, typed or made: only representations the server
   already governs for this object. Adding puts the term in its field,
   selects and focuses it, and hands the panel back to the inspector. */

export interface AddContextPanelProps {
  readonly dimensions: readonly PresentedDimension[];
  readonly locked: boolean;
  readonly onAdd: (entityId: string) => void;
  readonly onBack: () => void;
}

export default function AddContextPanel({ dimensions, locked, onAdd, onBack }: AddContextPanelProps) {
  return (
    <aside id="context-panel" className={styles.panel} aria-labelledby="context-add-heading">
      <h2 id="context-add-heading" className={styles.label}>{ADD_CONTEXT_TITLE}</h2>
      <p className={styles.note}>{ADD_CONTEXT_NOTE}</p>
      {dimensions.map((dimension) => {
        const available = dimension.items.filter((item) => !item.visible);
        return (
          <section key={dimension.kind} className={styles.group} data-kind={dimension.kind} aria-labelledby={`context-add-${dimension.kind}`}>
            <h3 id={`context-add-${dimension.kind}`} className={styles.kind}>
              <span className={styles.dot} aria-hidden="true" />
              {dimension.word}
            </h3>
            {available.length === 0 ? (
              <p className={styles.none}>{NO_ADDITIONAL}</p>
            ) : (
              <ul role="list" className={styles.list}>
                {available.map((item) => (
                  <li key={item.entityId} className={styles.item}>
                    <span className={styles.itemLabel}>{item.label}</span>
                    <button
                      type="button"
                      className={styles.add}
                      disabled={locked}
                      aria-label={ADD_TERM(item.label)}
                      onClick={() => onAdd(item.entityId)}
                    >
                      {ROW_ADD}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}
      <p className={styles.actions}>
        <button type="button" className={styles.back} onClick={onBack}>{BACK_TO_INSPECTOR}</button>
      </p>
    </aside>
  );
}

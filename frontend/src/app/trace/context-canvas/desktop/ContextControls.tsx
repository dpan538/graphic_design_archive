import { useState, type ChangeEvent } from "react";
import {
  ADD_TERM,
  AVAILABLE_TITLE,
  DIMENSIONS_TITLE,
  FOCUS_KIND,
  FOCUS_LABEL,
  FOCUS_NONE,
  FOCUS_ON,
  HIDE_AVAILABLE,
  LAYOUTS,
  LAYOUT_LABEL,
  LAYOUT_NOTE,
  NOT_RECORDED,
  ON_CANVAS_OF,
  OPEN_ROWS,
  OPEN_ROWS_NOTE,
  ROW_ADD,
  SHOW_AVAILABLE,
  type ContextKind,
  type LayoutPreset,
} from "../lib/content";
import styles from "./ContextControls.module.css";

/* 02 — the rail's controls (§7g): the canvas layout — four presets over
   the same governed contexts, nothing else changes — and, in Focus, a
   compact selector for the dimension read in full; then the three
   dimensions of context, each a line saying what the selected object
   carries of that kind — "N/T on canvas", or "Not recorded"
   — and, only while M > 0, a "+" that opens that dimension's list of
   AVAILABLE context with an Add per term: the primary way to add
   context. Adding places an already-governed representation on the
   canvas (never a new term); the rows' Add can also be dragged. The
   line itself brings the field into view. Not filters: nothing here
   narrows the archive; everything is about the one object. */

export interface AvailableTerm {
  readonly entityId: string;
  readonly label: string;
}

export interface DimensionControl {
  readonly kind: ContextKind;
  readonly word: string;
  readonly visibleCount: number;
  readonly total: number;
  readonly available: readonly AvailableTerm[];
}

export interface ContextControlsProps {
  readonly layout: LayoutPreset;
  readonly focusKind: ContextKind;
  readonly locked: boolean;
  readonly dimensions: readonly DimensionControl[];
  readonly onLayoutChange: (layout: LayoutPreset) => void;
  readonly onFocusKind: (kind: ContextKind) => void;
  readonly onDimension: (kind: ContextKind) => void;
  readonly onAdd: (entityId: string) => void;
  readonly onOpenRows: () => void;
}

export default function ContextControls({
  layout,
  focusKind,
  locked,
  dimensions,
  onLayoutChange,
  onFocusKind,
  onDimension,
  onAdd,
  onOpenRows,
}: ContextControlsProps) {
  const [openKind, setOpenKind] = useState<ContextKind | null>(null);
  function handleLayout(event: ChangeEvent<HTMLSelectElement>) {
    onLayoutChange(event.target.value as LayoutPreset);
  }
  return (
    <section className={styles.controls} aria-label="Context controls">
      <div className={styles.template}>
        <label htmlFor="context-canvas-layout" className={styles.label}>{LAYOUT_LABEL}</label>
        <select id="context-canvas-layout" className={styles.select} value={layout} disabled={locked} onChange={handleLayout}>
          {LAYOUTS.map((item) => (
            <option key={item.id} value={item.id}>{item.label}</option>
          ))}
        </select>
        <p className={styles.note}>{LAYOUTS.find((item) => item.id === layout)?.brief} {LAYOUT_NOTE}</p>
        {layout === "focus" ? (
          <div className={styles.focusRow} role="group" aria-label={FOCUS_LABEL}>
            <span className={styles.focusWord}>{FOCUS_LABEL}</span>
            {dimensions.map((item) => (
              <button
                key={item.kind}
                type="button"
                className={styles.focusOption}
                data-kind={item.kind}
                aria-pressed={item.kind === focusKind}
                disabled={locked || item.total === 0}
                aria-label={item.total === 0 ? FOCUS_NONE(item.word) : FOCUS_ON(item.word)}
                onClick={() => onFocusKind(item.kind)}
              >
                {item.word}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <div className={styles.dimensions}>
        <h2 className={styles.label}>{DIMENSIONS_TITLE}</h2>
        <ul role="list" className={styles.list}>
          {dimensions.map((item) => {
            const none = item.total === 0;
            const availableCount = item.available.length;
            /* "n/total on canvas": what stands, out of what the object carries */
            const status = none ? NOT_RECORDED : ON_CANVAS_OF(item.visibleCount, item.total);
            const open = openKind === item.kind && availableCount > 0;
            const listId = `context-available-${item.kind}`;
            return (
              <li key={item.kind} className={styles.dimension} data-kind={item.kind} data-none={none || undefined}>
                <div className={styles.dimensionLine}>
                  <button
                    type="button"
                    className={styles.focus}
                    disabled={locked || item.visibleCount === 0}
                    aria-label={`${item.word}: ${status}. ${FOCUS_KIND(item.word)}`}
                    onClick={() => onDimension(item.kind)}
                  >
                    <span className={styles.dot} aria-hidden="true" />
                    <span className={styles.word}>{item.word}</span>
                    <span className={styles.status}>{status}</span>
                  </button>
                  {availableCount > 0 ? (
                    <button
                      type="button"
                      className={styles.plus}
                      disabled={locked}
                      aria-expanded={open}
                      aria-controls={listId}
                      aria-label={open ? HIDE_AVAILABLE(item.word) : SHOW_AVAILABLE(item.word, availableCount)}
                      onClick={() => setOpenKind(open ? null : item.kind)}
                    >
                      {open ? "−" : "+"}
                    </button>
                  ) : null}
                </div>
                {open ? (
                  <div id={listId} className={styles.available} role="group" aria-label={AVAILABLE_TITLE(item.word)}>
                    <p className={styles.availableTitle}>{AVAILABLE_TITLE(item.word)}</p>
                    <ul role="list" className={styles.availableList}>
                      {item.available.map((term) => (
                        <li key={term.entityId} className={styles.availableItem}>
                          <span className={styles.availableLabel}>{term.label}</span>
                          <button
                            type="button"
                            className={styles.add}
                            disabled={locked}
                            aria-label={ADD_TERM(term.label)}
                            onClick={() => onAdd(term.entityId)}
                          >
                            {ROW_ADD}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      </div>

      <button type="button" className={styles.rows} onClick={onOpenRows}>
        <span className={styles.rowsWord}>{OPEN_ROWS}</span>
        <span className={styles.rowsNote}>{OPEN_ROWS_NOTE}</span>
      </button>
    </section>
  );
}

import { useEffect, useRef, type PointerEvent, type SyntheticEvent } from "react";
import type { PresentedDimension } from "../lib/presentation";
import {
  COPY_CONTEXT,
  GO_TO_CHIP,
  NOT_RECORDED,
  ON_CANVAS,
  ROW_ADD,
  ROW_REMOVE,
  ROWS_NOTE,
  ROWS_TITLE,
  SET_ASIDE,
} from "../lib/content";
import styles from "./ContextRows.module.css";

/* 05 — the accessible equivalent (§7g): the canvas as rows, in a panel
   folded under the canvas — the canvas stays the page's body; the rows
   are its equivalent, not its rival. Three columns, one per dimension,
   "Not recorded" where the object carries none; kept in step with the
   canvas both ways: a row selected selects its chip and brings it into
   view, a chip selected marks its row and scrolls it into view; "Go to
   chip" moves keyboard focus onto the chip. Each row carries the
   existing add / remove action for its representation on its own line;
   the Add control can also be dragged onto the canvas. "Copy context"
   puts the same presentation on the clipboard as tables. The rows read
   the presentation model the canvas and the clipboard read — one
   description, three renderings. */

export interface ContextRowsProps {
  readonly groups: readonly PresentedDimension[];
  readonly open: boolean;
  readonly selectedEntityId: string | null;
  readonly locked: boolean;
  readonly onToggle: (open: boolean) => void;
  readonly onSelect: (entityId: string) => void;
  readonly onGoToChip: (entityId: string) => void;
  readonly onAdd: (entityId: string) => void;
  readonly onRemove: (entityId: string) => void;
  readonly onCopy: () => void;
  readonly onDragStart: (entityId: string, pointerId: number, clientX: number, clientY: number) => void;
  readonly onDragMove: (clientX: number, clientY: number) => void;
  readonly onDragEnd: (entityId: string, pointerId: number, clientX: number, clientY: number) => void;
  readonly onDragCancel: () => void;
}

export default function ContextRows({
  groups,
  open,
  selectedEntityId,
  locked,
  onToggle,
  onSelect,
  onGoToChip,
  onAdd,
  onRemove,
  onCopy,
  onDragStart,
  onDragMove,
  onDragEnd,
  onDragCancel,
}: ContextRowsProps) {
  const panel = useRef<HTMLDetailsElement>(null);

  /* a chip selected on the canvas brings its row into view — within the
     rows' own scroller only, once the layout has settled, and only as far
     as needed; the column heads stay in view when the row already is */
  useEffect(() => {
    if (!selectedEntityId || !panel.current || !open) return;
    const details = panel.current;
    let frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => {
        const row = details.querySelector<HTMLElement>(`[data-entity-id="${CSS.escape(selectedEntityId)}"]`);
        const scroller = row?.closest<HTMLElement>(`.${styles.rows}`);
        if (!row || !scroller) return;
        const r = row.getBoundingClientRect();
        const c = scroller.getBoundingClientRect();
        if (r.bottom > c.bottom) scroller.scrollTop += Math.min(r.bottom - c.bottom, Math.max(0, r.top - c.top));
        if (r.top < c.top) scroller.scrollTop -= c.top - r.top;
      });
    });
    return () => cancelAnimationFrame(frame);
  }, [open, selectedEntityId]);

  function beginDrag(event: PointerEvent<HTMLButtonElement>, entityId: string) {
    if (locked || event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    onDragStart(entityId, event.pointerId, event.clientX, event.clientY);
  }

  return (
    <details
      id="context-rows"
      className={styles.panel}
      ref={panel}
      open={open}
      onToggle={(event: SyntheticEvent<HTMLDetailsElement>) => onToggle(event.currentTarget.open)}
    >
      <summary id="context-rows-summary" className={styles.summary}>
        <span className={styles.label}>{ROWS_TITLE}</span>
        <span className={styles.note}>{ROWS_NOTE}</span>
      </summary>

      <div className={styles.rows}>
        <div className={styles.head}>
          <button type="button" className={styles.copy} onClick={onCopy}>{COPY_CONTEXT}</button>
        </div>
        {groups.map((group) => (
          <section key={group.kind} className={styles.group} aria-labelledby={`context-rows-${group.kind}`}>
            <h3 id={`context-rows-${group.kind}`} className={styles.kind} data-kind={group.kind}>
              <span className={styles.dot} aria-hidden="true" />
              {group.word}
            </h3>
            {group.items.length === 0 ? (
              <p className={styles.none}>{NOT_RECORDED}</p>
            ) : (
              <ul className={styles.items} role="list">
                {group.items.map((item) => {
                  const selected = item.entityId === selectedEntityId;
                  return (
                    <li
                      key={item.entityId}
                      className={styles.item}
                      data-entity-id={item.entityId}
                      data-selected={selected ? "true" : "false"}
                      data-visible={item.visible ? "true" : "false"}
                    >
                      <button
                        type="button"
                        className={styles.select}
                        aria-pressed={selected}
                        aria-label={`${item.label}. ${group.word} context (${item.representation.connectionLabel}), ${item.visible ? ON_CANVAS : SET_ASIDE}. ${item.representation.explanation.accessibilityWording}`}
                        onClick={() => onSelect(item.entityId)}
                      >
                        <span className={styles.itemLabel}>{item.label}</span>
                        <span className={styles.itemState}>{item.visible ? ON_CANVAS : SET_ASIDE}</span>
                      </button>
                      <span className={styles.itemActions}>
                        {selected && item.visible ? (
                          <button type="button" className={styles.small} onClick={() => onGoToChip(item.entityId)}>
                            {GO_TO_CHIP}
                          </button>
                        ) : null}
                        {item.visible ? (
                          <button
                            type="button"
                            className={styles.small}
                            disabled={locked}
                            aria-label={`${ROW_REMOVE} ${item.label} from the canvas`}
                            onClick={() => onRemove(item.entityId)}
                          >
                            {ROW_REMOVE}
                          </button>
                        ) : (
                          <button
                            type="button"
                            className={`${styles.small} ${styles.add}`}
                            disabled={locked}
                            aria-label={`${ROW_ADD} ${item.label} to the canvas. Drag it onto the canvas, or press Enter.`}
                            onClick={() => onAdd(item.entityId)}
                            onPointerDown={(event) => beginDrag(event, item.entityId)}
                            onPointerMove={(event) => {
                              if (event.currentTarget.hasPointerCapture(event.pointerId)) onDragMove(event.clientX, event.clientY);
                            }}
                            onPointerUp={(event) => {
                              if (event.currentTarget.hasPointerCapture(event.pointerId)) {
                                onDragEnd(item.entityId, event.pointerId, event.clientX, event.clientY);
                                event.currentTarget.releasePointerCapture(event.pointerId);
                              }
                            }}
                            onPointerCancel={onDragCancel}
                          >
                            {ROW_ADD}
                          </button>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        ))}
      </div>
    </details>
  );
}

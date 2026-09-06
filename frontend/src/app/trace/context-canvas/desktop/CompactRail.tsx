import { NOT_RECORDED, ON_CANVAS_OF, RAIL_EXPAND, type ContextKind } from "../lib/content";
import styles from "./CompactRail.module.css";

/* 02 — the rail, compact (§7g): for canvas-focus work — the object's
   title, the three dimensions as indicators (dot, word, status), and
   the control that expands the rail again. Nothing else. */

export interface CompactDimension {
  readonly kind: ContextKind;
  readonly word: string;
  readonly visibleCount: number;
  readonly total: number;
}

export interface CompactRailProps {
  readonly title: string;
  readonly stableId: string;
  readonly dimensions: readonly CompactDimension[];
  readonly onExpand: () => void;
  readonly onFocusKind: (kind: ContextKind) => void;
}

export default function CompactRail({ title, stableId, dimensions, onExpand, onFocusKind }: CompactRailProps) {
  return (
    <div className={styles.compact}>
      <button type="button" className={styles.expand} aria-label={RAIL_EXPAND} onClick={onExpand}>›</button>
      <p className={styles.title} title={title}>{title.trim() || stableId}</p>
      <ul role="list" className={styles.list}>
        {dimensions.map((item) => {
          const none = item.total === 0;
          const status = none ? NOT_RECORDED : ON_CANVAS_OF(item.visibleCount, item.total);
          return (
            <li key={item.kind} data-kind={item.kind} data-none={none || undefined}>
              <button
                type="button"
                className={styles.indicator}
                disabled={item.visibleCount === 0}
                aria-label={`${item.word}: ${status}`}
                onClick={() => onFocusKind(item.kind)}
              >
                <span className={styles.dot} aria-hidden="true" />
                <span className={styles.word}>{item.word}</span>
                <span className={styles.status}>{status}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

import { useMemo, type PointerEvent } from "react";
import type { TracePublicDataRef } from "../../domain";
import { contextCanvasEntityId } from "./types";
import styles from "./ContextCanvas.module.css";

interface ContextEntityPaletteProps {
  readonly entities: readonly TracePublicDataRef[];
  readonly collapsed: boolean;
  readonly disabled: boolean;
  readonly onToggleCollapsed: () => void;
  readonly onAdd: (entityId: string) => void;
  readonly onDragStart: (entityId: string, pointerId: number, clientX: number, clientY: number) => void;
  readonly onDragMove: (clientX: number, clientY: number) => void;
  readonly onDragEnd: (entityId: string, pointerId: number, clientX: number, clientY: number) => void;
  readonly onDragCancel: () => void;
}

export function ContextEntityPalette({
  entities,
  collapsed,
  disabled,
  onToggleCollapsed,
  onAdd,
  onDragStart,
  onDragMove,
  onDragEnd,
  onDragCancel,
}: ContextEntityPaletteProps) {
  const groups = useMemo(() => {
    const grouped = new Map<string, TracePublicDataRef[]>();
    for (const entity of entities) {
      const values = grouped.get(entity.kind) ?? [];
      values.push(entity);
      grouped.set(entity.kind, values);
    }
    return [...grouped.entries()]
      .sort(([left], [right]) => left.localeCompare(right, "en"))
      .map(([kind, values]) => [
        kind,
        values.sort((left, right) =>
          (left.label || left.stableId).localeCompare(right.label || right.stableId, "en")),
      ] as const);
  }, [entities]);

  function beginDrag(event: PointerEvent<HTMLButtonElement>, entityId: string) {
    if (disabled || event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    onDragStart(entityId, event.pointerId, event.clientX, event.clientY);
  }

  return (
    <aside className={`${styles.palette} ${collapsed ? styles.panelCollapsed : ""}`} aria-label="Available context entities">
      <div className={styles.panelHeader}>
        <div>
          <h2>Entity palette</h2>
          {!collapsed ? <p>{entities.length} available</p> : null}
        </div>
        <button
          type="button"
          className={styles.compactButton}
          aria-expanded={!collapsed}
          aria-controls="context-entity-palette-content"
          onClick={onToggleCollapsed}
        >
          {collapsed ? "Expand palette" : "Collapse palette"}
        </button>
      </div>
      {!collapsed ? (
        <div id="context-entity-palette-content" className={styles.paletteContent}>
          <p className={styles.helpText}>Add entities only. Known connections appear automatically.</p>
          {groups.length === 0 ? (
            <p className={styles.emptyState}>Every available entity is on the canvas.</p>
          ) : groups.map(([kind, values]) => (
            <section key={kind} className={styles.paletteGroup} aria-labelledby={`palette-group-${kind}`}>
              <h3 id={`palette-group-${kind}`}>{kind.replaceAll("_", " ")}</h3>
              <ul>
                {values.map((entity) => {
                  const entityId = contextCanvasEntityId(entity);
                  const displayLabel = entity.label?.trim() || entity.stableId;
                  return (
                    <li key={entityId} className={styles.paletteItem}>
                      <div>
                        <span className={styles.paletteLabel}>{displayLabel}</span>
                        <span className={styles.paletteId}>{entity.stableId}</span>
                      </div>
                      <div className={styles.paletteActions}>
                        <button
                          type="button"
                          className={styles.dragHandle}
                          disabled={disabled}
                          aria-label={`Drag ${displayLabel} to canvas; press Enter or Space to add`}
                          aria-keyshortcuts="Enter Space"
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              onAdd(entityId);
                            }
                          }}
                          onPointerDown={(event) => beginDrag(event, entityId)}
                          onPointerMove={(event) => {
                            if (event.currentTarget.hasPointerCapture(event.pointerId)) {
                              onDragMove(event.clientX, event.clientY);
                            }
                          }}
                          onPointerUp={(event) => {
                            if (event.currentTarget.hasPointerCapture(event.pointerId)) {
                              onDragEnd(entityId, event.pointerId, event.clientX, event.clientY);
                              event.currentTarget.releasePointerCapture(event.pointerId);
                            }
                          }}
                          onPointerCancel={onDragCancel}
                        >
                          Drag
                        </button>
                        <button
                          type="button"
                          className={styles.addButton}
                          disabled={disabled}
                          onClick={() => onAdd(entityId)}
                        >
                          Add to canvas
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      ) : null}
    </aside>
  );
}

import type { KeyboardEvent, PointerEvent } from "react";
import { contextCanvasConnectionLabel } from "./connections";
import {
  CONTEXT_CANVAS_CONNECTION_LABEL_DISPLAY_UNIT_LIMIT,
  fitContextCanvasDisplayLabel,
} from "./display-label";
import type { ContextCanvasConnectionGeometry } from "./types";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasConnectionsProps {
  readonly geometry: readonly ContextCanvasConnectionGeometry[];
  readonly selectedConnectionId: string | null;
  readonly onSelect: (connectionId: string) => void;
}

export function ContextCanvasConnections({
  geometry,
  selectedConnectionId,
  onSelect,
}: ContextCanvasConnectionsProps) {
  function selectFromKeyboard(
    event: KeyboardEvent<SVGGElement>,
    connectionId: string,
  ) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onSelect(connectionId);
  }

  function selectFromPointer(
    event: PointerEvent<SVGGElement>,
    connectionId: string,
  ) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.focus();
    onSelect(connectionId);
  }

  return (
    <g aria-label="Context connections">
      {geometry.map((item) => {
        const selected = selectedConnectionId === item.connection.id;
        const connectionLabel = contextCanvasConnectionLabel(item.connection);
        const displayLabel = fitContextCanvasDisplayLabel(
          connectionLabel,
          CONTEXT_CANVAS_CONNECTION_LABEL_DISPLAY_UNIT_LIMIT,
        );
        return (
          <g
            key={item.connection.id}
            className={`${styles.connection} ${styles[`connection_${item.connection.connectionKind}`]} ${selected ? styles.connectionSelected : ""}`}
            role="button"
            tabIndex={0}
            aria-pressed={selected}
            aria-label={item.accessibleLabel}
            data-selected={selected ? "true" : "false"}
            onPointerDown={(event) => selectFromPointer(event, item.connection.id)}
            onKeyDown={(event) => selectFromKeyboard(event, item.connection.id)}
          >
            <title>{item.accessibleLabel}</title>
            <path className={styles.connectionHitArea} d={item.path} />
            <path
              className={styles.connectionPath}
              d={item.path}
              markerEnd={item.connection.connectionKind === "context_representation"
                ? undefined
                : "url(#context-canvas-arrow)"}
            />
            <text className={styles.connectionLabel} x={item.labelX} y={item.labelY}>
              {displayLabel.displayText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

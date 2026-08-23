import type { KeyboardEvent, PointerEvent } from "react";
import {
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  contextCanvasNodeDomId,
  type ContextCanvasPosition,
  type ContextCanvasVisibleNode,
} from "./types";
import {
  CONTEXT_CANVAS_NODE_ID_DISPLAY_UNIT_LIMIT,
  contextCanvasFullLabel,
  fitContextCanvasDisplayLabel,
} from "./display-label";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasNodeProps {
  readonly node: ContextCanvasVisibleNode;
  readonly selected: boolean;
  readonly onPointerDown: (event: PointerEvent<SVGGElement>, nodeId: string) => void;
  readonly onSelect: (nodeId: string) => void;
  readonly onMoveBy: (nodeId: string, delta: ContextCanvasPosition) => void;
}

export function ContextCanvasNode({
  node,
  selected,
  onPointerDown,
  onSelect,
  onMoveBy,
}: ContextCanvasNodeProps) {
  const fullLabel = contextCanvasFullLabel(node.ref);
  const displayLabel = fitContextCanvasDisplayLabel(fullLabel);
  const displayId = fitContextCanvasDisplayLabel(
    node.ref.stableId,
    CONTEXT_CANVAS_NODE_ID_DISPLAY_UNIT_LIMIT,
  );
  const publicKind = node.representation?.explanation.publicName || node.ref.kind;
  const accessibleDescription = node.representation
    ? `${node.representation.explanation.accessibilityWording} Publication state: ${node.representation.publicationState}. Source basis: ${node.representation.explanation.sourceBasis}.`
    : `${node.ref.kind}${node.isRoot ? ", selected root object" : ""}`;
  const nodeTitle = node.representation
    ? `${fullLabel} (${publicKind}). ${node.representation.explanation.accessibilityWording}`
    : `${fullLabel} (${node.ref.kind})`;

  function handleKeyDown(event: KeyboardEvent<SVGGElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(node.id);
      return;
    }
    const step = event.shiftKey ? 1 : 10;
    const delta = event.key === "ArrowUp" ? { x: 0, y: -step }
      : event.key === "ArrowDown" ? { x: 0, y: step }
      : event.key === "ArrowLeft" ? { x: -step, y: 0 }
      : event.key === "ArrowRight" ? { x: step, y: 0 }
      : null;
    if (delta) {
      event.preventDefault();
      onMoveBy(node.id, delta);
    }
  }

  return (
    <g
      id={contextCanvasNodeDomId(node.id)}
      className={`${styles.node} ${node.representation?.publicationState === "qualified" ? styles.nodeQualified : ""} ${selected ? styles.nodeSelected : ""}`}
      data-selected={selected ? "true" : "false"}
      transform={`translate(${node.position.x} ${node.position.y})`}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`${fullLabel}. ${accessibleDescription} Use arrow keys to move 10 units; hold Shift for 1-unit precision.`}
      onPointerDown={(event) => {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.focus();
        event.currentTarget.setPointerCapture(event.pointerId);
        onPointerDown(event, node.id);
      }}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(node.id);
      }}
      onKeyDown={handleKeyDown}
    >
      <title>{nodeTitle}</title>
      <rect
        className={styles.nodeBody}
        width={CONTEXT_CANVAS_NODE_WIDTH}
        height={CONTEXT_CANVAS_NODE_HEIGHT}
        rx={8}
      />
      <circle className={styles.nodePort} cx={0} cy={CONTEXT_CANVAS_NODE_HEIGHT / 2} r={5} aria-hidden="true" />
      <circle className={styles.nodePort} cx={CONTEXT_CANVAS_NODE_WIDTH} cy={CONTEXT_CANVAS_NODE_HEIGHT / 2} r={5} aria-hidden="true" />
      <text className={styles.nodeLabel} x={16} y={30}>{displayLabel.displayText}</text>
      <text className={styles.nodeKind} x={16} y={57}>{publicKind}</text>
      <text className={styles.nodeId} x={16} y={81}>{displayId.displayText}</text>
    </g>
  );
}

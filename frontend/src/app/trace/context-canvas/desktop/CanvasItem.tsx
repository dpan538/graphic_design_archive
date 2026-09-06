import type { KeyboardEvent, PointerEvent } from "react";
import {
  contextCanvasNodeDomId,
  type ContextCanvasPosition,
  type ContextCanvasVisibleNode,
} from "@/features/trace-v49/context/canvas/types";
import { itemSize } from "../lib/arrange";
import { SELECTED_OBJECT, kindWord } from "../lib/content";
import styles from "./CanvasItem.module.css";

/* 03 — one item on the canvas (§7g). Two forms, one behaviour. The
   OBJECT: the focal element, once — a coral plate with the title, the
   stable ID and the year · type beneath, no more (it is not an object
   page). A CHIP: a lightweight contextual representation — the governed
   label and nothing internal; the dimension's word is the field's label
   around it and the chip's accessible name. HTML, so the text wraps and clamps and the item is a
   real control: Enter or Space selects, the arrow keys move it (Shift
   for one unit), the pointer drags it. No image, ever. */

export interface ObjectIdentity {
  readonly stableId: string;
  readonly dateDisplay?: string;
  readonly objectType?: string;
}

export interface CanvasItemProps {
  readonly node: ContextCanvasVisibleNode;
  readonly selected: boolean;
  readonly identity: ObjectIdentity;
  readonly onPointerDown: (event: PointerEvent<HTMLDivElement>, nodeId: string) => void;
  readonly onSelect: (nodeId: string) => void;
  readonly onMoveBy: (nodeId: string, delta: ContextCanvasPosition) => void;
  readonly onHover: (nodeId: string | null) => void;
}

export default function CanvasItem({
  node,
  selected,
  identity,
  onPointerDown,
  onSelect,
  onMoveBy,
  onHover,
}: CanvasItemProps) {
  const size = itemSize(node.isRoot);
  const representation = node.representation;
  const label = node.ref.label?.trim() || node.ref.stableId;
  const accessibleName = representation
    ? `${label}. ${kindWord(representation.kind)} context. ${representation.explanation.accessibilityWording} Use the arrow keys to move it; hold Shift for one-unit steps.`
    : `${label}. ${SELECTED_OBJECT}, the centre of this canvas. Use the arrow keys to move it; hold Shift for one-unit steps.`;
  const meta = node.isRoot
    ? [identity.dateDisplay, identity.objectType].filter((v) => v && v.trim()).join(" · ")
    : "";

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
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

  const shared = {
    id: contextCanvasNodeDomId(node.id),
    "data-card": "true",
    "data-selected": selected ? "true" : "false",
    role: "button",
    tabIndex: 0,
    "aria-pressed": selected,
    "aria-label": accessibleName,
    title: label,
    style: { left: node.position.x, top: node.position.y, width: size.width, height: size.height },
    onPointerDown: (event: PointerEvent<HTMLDivElement>) => {
      if (event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      event.currentTarget.focus({ preventScroll: true });
      event.currentTarget.setPointerCapture(event.pointerId);
      onPointerDown(event, node.id);
    },
    onClick: (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();
      onSelect(node.id);
    },
    onKeyDown: handleKeyDown,
    onPointerEnter: () => onHover(node.id),
    onPointerLeave: () => onHover(null),
    onFocus: () => onHover(node.id),
    onBlur: () => onHover(null),
  } as const;

  if (node.isRoot) {
    return (
      <div {...shared} className={styles.object}>
        <span className={styles.objectKicker}>{SELECTED_OBJECT}</span>
        <span className={styles.objectTitle}>{label}</span>
        <span className={`${styles.objectId} tnum`}>{identity.stableId}</span>
        {meta ? <span className={styles.objectMeta}>{meta}</span> : null}
      </div>
    );
  }

  return (
    <div {...shared} className={styles.chip} data-kind={representation?.kind ?? "context"}>
      <span className={styles.chipLabel}>{label}</span>
    </div>
  );
}

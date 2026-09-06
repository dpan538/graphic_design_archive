import {
  useEffect,
  useState,
  type KeyboardEvent,
  type PointerEvent,
  type RefObject,
} from "react";
import type {
  ContextCanvasPosition,
  ContextCanvasSelection,
  ContextCanvasViewport,
  ContextCanvasViewportSize,
  ContextCanvasVisibleNode,
} from "@/features/trace-v49/context/canvas/types";
import type { Connector, Field } from "../lib/arrange";
import {
  EMPTY_CANVAS_NOTE,
  EMPTY_CONTEXT,
  FIELD_AVAILABLE,
  FIELD_SET_ASIDE,
  NOT_RECORDED,
  STAGE_LABEL,
  kindWord,
  type LayoutPreset,
} from "../lib/content";
import CanvasItem, { type ObjectIdentity } from "./CanvasItem";
import styles from "./Stage.module.css";

/* 03 — the spatial canvas (§7g): one pannable, zoomable ground, the
   page's main body. The selected object stands once; its contexts stand
   in three labelled FIELDS — Medium, Theme, Movement — thin outlines in
   the dimension's accent with a small accent bar and the word inside.
   A field with nothing in it is a COMPACT marker, one line: the word
   and "Not recorded" or "n set aside" — never a large empty region; a
   field with more of its kind still available says so ("+ n available",
   the rail's control adds them). The WIRES: governed Context V1's one
   connection class, the object to a representation, drawn as an
   orthogonal 1 px neutral line with the registry's wording ON it —
   "classified as", "themed as", "curated within" — interrupting the line
   on a paper knockout, no arrowhead, no weight, stronger and in the
   dimension's accent only while a chip of the wire is hovered or
   selected (focus, never strength); never between two terms, never for
   a dimension not recorded, never as a field's subtitle. Distance means nothing. The one claim boundary stands as the
   canvas's footer. Interaction is the existing model: drag the ground
   to pan, drag an item to move it, the wheel zooms about the pointer,
   Escape clears the selection or cancels a drag. While the canvas is
   still initialising nothing is drawn but the caption. A synthetic
   fixture announces itself in a banner. */

export interface StageProps {
  readonly containerRef: RefObject<HTMLDivElement | null>;
  readonly nodes: readonly ContextCanvasVisibleNode[];
  readonly fields: readonly Field[];
  readonly connectors: readonly Connector[];
  readonly preset: LayoutPreset;
  readonly viewport: ContextCanvasViewport;
  readonly interaction: string;
  readonly selection: ContextCanvasSelection;
  readonly identity: ObjectIdentity;
  readonly empty: boolean;
  readonly loading: boolean;
  readonly loadingText: string;
  readonly exporting: boolean;
  readonly claim: string;
  readonly banner: string | null;
  readonly onSizeChange: (size: ContextCanvasViewportSize) => void;
  readonly onWheel: (deltaY: number, point: ContextCanvasPosition) => void;
  readonly onBackgroundPointerDown: (event: PointerEvent<HTMLDivElement>) => void;
  readonly onNodePointerDown: (event: PointerEvent<HTMLDivElement>, nodeId: string) => void;
  readonly onPointerMove: (event: PointerEvent<HTMLDivElement>) => void;
  readonly onPointerEnd: (event: PointerEvent<HTMLDivElement>) => void;
  readonly onPointerCancel: (event: PointerEvent<HTMLDivElement>) => void;
  readonly onEscape: () => void;
  readonly onSelect: (nodeId: string) => void;
  readonly onMoveBy: (nodeId: string, delta: ContextCanvasPosition) => void;
}

export default function Stage({
  containerRef,
  nodes,
  fields,
  connectors,
  preset,
  viewport,
  interaction,
  selection,
  identity,
  empty,
  loading,
  loadingText,
  exporting,
  claim,
  banner,
  onSizeChange,
  onWheel,
  onBackgroundPointerDown,
  onNodePointerDown,
  onPointerMove,
  onPointerEnd,
  onPointerCancel,
  onEscape,
  onSelect,
  onMoveBy,
}: StageProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const selectedId = selection?.kind === "node" ? selection.id : null;

  /* the stage's size, for fitting */
  useEffect(() => {
    const element = containerRef.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const publish = () => {
      const rect = element.getBoundingClientRect();
      onSizeChange({ width: rect.width, height: rect.height });
    };
    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(element);
    return () => observer.disconnect();
  }, [containerRef, onSizeChange]);

  /* the wheel zooms about the pointer — a native, non-passive listener,
     since React's own wheel handler cannot prevent the page's scroll */
  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const handler = (event: WheelEvent) => {
      event.preventDefault();
      const rect = element.getBoundingClientRect();
      onWheel(event.deltaY, { x: event.clientX - rect.left, y: event.clientY - rect.top });
    };
    element.addEventListener("wheel", handler, { passive: false });
    return () => element.removeEventListener("wheel", handler);
  }, [containerRef, onWheel]);

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    const target = event.target as HTMLElement;
    if (target.closest("[data-card]") || target.closest("[data-chrome]")) return;
    onBackgroundPointerDown(event);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Escape") return;
    event.preventDefault();
    onEscape();
  }

  return (
    <div
      id="context-stage"
      ref={containerRef}
      className={styles.stage}
      role="application"
      tabIndex={0}
      aria-label={STAGE_LABEL}
      aria-describedby="context-rows"
      aria-busy={loading || exporting || undefined}
      data-interaction={interaction}
      data-preset={preset}
      onPointerDown={handlePointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerEnd}
      onPointerCancel={onPointerCancel}
      onKeyDown={handleKeyDown}
    >
      <div
        className={styles.world}
        style={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})` }}
      >
        {loading ? null : fields.map((field) => (
          <div
            key={field.kind}
            className={styles.field}
            data-kind={field.kind}
            data-state={field.state}
            data-compact={field.compact ? "true" : "false"}
            style={{ left: field.box.x, top: field.box.y, width: field.box.width, height: field.box.height }}
            aria-hidden="true"
          >
            <span className={styles.fieldHead}>
              <span className={styles.fieldWord}>{kindWord(field.kind)}</span>
              {field.state === "not_recorded" ? <span className={styles.fieldNote}>{NOT_RECORDED}</span> : null}
              {field.state === "set_aside" ? <span className={styles.fieldNote}>{FIELD_SET_ASIDE(field.total)}</span> : null}
              {field.state === "filled" && field.total > field.visible ? (
                <span className={styles.fieldHint}>{FIELD_AVAILABLE(field.total - field.visible)}</span>
              ) : null}
            </span>
          </div>
        ))}
        {loading ? null : (
          <svg className={styles.wires} aria-hidden="true">
            {connectors.map((c) => {
              const active = c.chipIds.some((id) => id === selectedId || id === hoverId);
              return (
                <polyline
                  key={c.id}
                  points={c.points.map((p) => `${p.x},${p.y}`).join(" ")}
                  data-kind={c.kind}
                  data-active={active ? "true" : "false"}
                />
              );
            })}
          </svg>
        )}
        {loading ? null : connectors.map((c) => {
          const active = c.chipIds.some((id) => id === selectedId || id === hoverId);
          return (
            <span
              key={`${c.id}:label`}
              className={styles.wireLabel}
              data-kind={c.kind}
              data-vertical={c.labelVertical ? "true" : "false"}
              data-active={active ? "true" : "false"}
              style={{ left: c.labelAt.x, top: c.labelAt.y }}
              aria-hidden="true"
            >
              {c.label}
            </span>
          );
        })}
        {loading ? null : nodes.map((node) => (
          <CanvasItem
            key={node.id}
            node={node}
            selected={selection?.kind === "node" && selection.id === node.id}
            identity={identity}
            onPointerDown={onNodePointerDown}
            onSelect={onSelect}
            onMoveBy={onMoveBy}
            onHover={setHoverId}
          />
        ))}
      </div>

      {banner ? (
        <p className={styles.banner} data-chrome="true" role="note">{banner}</p>
      ) : null}

      {loading ? (
        <div className={styles.caption} data-chrome="true">
          <p className={styles.captionLead}>{loadingText}</p>
        </div>
      ) : empty ? (
        <div className={styles.caption} data-chrome="true">
          <p className={styles.captionLead}>{EMPTY_CONTEXT}</p>
          <p className={styles.captionNote}>{EMPTY_CANVAS_NOTE}</p>
        </div>
      ) : null}

      <p className={styles.claim} data-chrome="true">{claim}</p>
    </div>
  );
}

"use client";

import { useEffect, useRef, type RefObject } from "react";
import styles from "./StageCursor.module.css";

/* the stage's cursor (§7i): the system pointer is hidden over the stage and
   a small drawn cursor follows it — a ring and a dot. What is under the
   pointer changes only the cursor, never the picture: over a term's motif
   the ring opens and four corners appear in the motif's ink; over an
   association's shape it becomes a crosshair; near the picture's edge it
   contracts; while the button is down it shrinks. Three rules keep it from
   flickering: a GEOMETRIC DEADZONE — a term or association counts only
   inside its own region (the invisible region rects the picture carries),
   not on a stray primitive; a STABILITY GATE — a new reading must hold for
   STABLE_MS before the cursor changes; and a CROSSFADE — the parts fade out
   and in (CSS) rather than jump. Position is set on the animation frame,
   with a short ease unless motion is reduced. The element takes no pointer
   events and is hidden from assistive technology. Fine pointers only. */

type CursorState = "empty" | "term" | "association" | "edge" | "pressed";

interface StageCursorProps {
  readonly stageRef: RefObject<HTMLDivElement | null>;
}

const EDGE = 36;
const STABLE_MS = 70;
const DEFAULT_INK = "";

function inkOf(element: Element): string {
  const fill = element.getAttribute("fill") ?? "";
  if (/^#[0-9a-f]{3,8}$/i.test(fill)) return fill;
  const stroke = element.getAttribute("stroke") ?? "";
  if (/^#[0-9a-f]{3,8}$/i.test(stroke)) return stroke;
  return DEFAULT_INK;
}

function withinAny(regions: readonly DOMRect[], x: number, y: number): boolean {
  return regions.some((box) => x >= box.left && x <= box.right && y >= box.top && y <= box.bottom);
}

export default function StageCursor({ stageRef }: StageCursorProps) {
  const cursorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stage = stageRef.current;
    const cursor = cursorRef.current;
    if (!stage || !cursor) return;
    if (typeof window.matchMedia !== "function" || !window.matchMedia("(pointer: fine)").matches) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    stage.dataset.cursor = "drawn";
    let x = -100;
    let y = -100;
    let shownX = -100;
    let shownY = -100;
    let frame = 0;
    let pressed = false;
    let hovered: CursorState = "empty";
    let ink = DEFAULT_INK;
    /* the stability gate: the reading that is waiting, and since when */
    let pendingState: CursorState = "empty";
    let pendingInk = DEFAULT_INK;
    let pendingSince = 0;
    let settle = 0;

    const paint = () => {
      frame = 0;
      const ease = reduced ? 1 : 0.45;
      shownX += (x - shownX) * ease;
      shownY += (y - shownY) * ease;
      cursor.style.transform = `translate3d(${shownX}px, ${shownY}px, 0) translate(-50%, -50%)`;
      if (!reduced && (Math.abs(x - shownX) > 0.3 || Math.abs(y - shownY) > 0.3)) frame = window.requestAnimationFrame(paint);
    };
    const schedule = () => { if (!frame) frame = window.requestAnimationFrame(paint); };
    const apply = () => {
      const state: CursorState = pressed ? "pressed" : hovered;
      if (cursor.dataset.state !== state) cursor.dataset.state = state;
      cursor.style.setProperty("--cursor-ink", ink || "var(--t-fg)");
    };
    const read = (clientX: number, clientY: number): { state: CursorState; ink: string } => {
      const picture = stage.querySelector("svg");
      if (!picture) return { state: "empty", ink: DEFAULT_INK };
      const box = picture.getBoundingClientRect();
      const inside = clientX >= box.left && clientX <= box.right && clientY >= box.top && clientY <= box.bottom;
      if (!inside) return { state: "empty", ink: DEFAULT_INK };
      const nearEdge = clientX - box.left < EDGE || box.right - clientX < EDGE || clientY - box.top < EDGE || box.bottom - clientY < EDGE;
      /* the deadzone: only inside a term's or an association's own region does its primitive count */
      const termRegions = [...picture.querySelectorAll('[data-layer="terms"] rect')].map((rect) => rect.getBoundingClientRect());
      const associationRegions = [...picture.querySelectorAll('[data-layer="associations"] rect')].map((rect) => rect.getBoundingClientRect());
      const under = document.elementsFromPoint(clientX, clientY);
      const association = withinAny(associationRegions, clientX, clientY) ? under.find((element) => element.getAttribute("data-role") === "association") : undefined;
      const term = withinAny(termRegions, clientX, clientY) ? under.find((element) => element.getAttribute("data-role") === "term") : undefined;
      if (association) return { state: "association", ink: DEFAULT_INK };
      if (term) return { state: "term", ink: inkOf(term) };
      if (nearEdge) return { state: "edge", ink: DEFAULT_INK };
      return { state: "empty", ink: DEFAULT_INK };
    };
    /* the gate: a reading becomes the cursor's state only after it has held for STABLE_MS */
    const settleNow = () => {
      settle = 0;
      hovered = pendingState;
      ink = pendingInk;
      apply();
    };
    const consider = (reading: { state: CursorState; ink: string }, now: number) => {
      if (reading.state !== pendingState || reading.ink !== pendingInk) {
        pendingState = reading.state;
        pendingInk = reading.ink;
        pendingSince = now;
        if (settle) window.clearTimeout(settle);
        settle = window.setTimeout(settleNow, STABLE_MS);
        return;
      }
      if (now - pendingSince >= STABLE_MS && (hovered !== pendingState || ink !== pendingInk)) settleNow();
    };

    const onMove = (event: PointerEvent) => {
      x = event.clientX;
      y = event.clientY;
      cursor.dataset.visible = "true";
      consider(read(event.clientX, event.clientY), event.timeStamp);
      schedule();
    };
    const onLeave = () => { cursor.dataset.visible = "false"; if (settle) window.clearTimeout(settle); settle = 0; pendingState = "empty"; pendingInk = DEFAULT_INK; hovered = "empty"; ink = DEFAULT_INK; apply(); };
    const onDown = () => { pressed = true; apply(); };
    const onUp = () => { pressed = false; apply(); };
    stage.addEventListener("pointermove", onMove);
    stage.addEventListener("pointerleave", onLeave);
    stage.addEventListener("pointerdown", onDown);
    window.addEventListener("pointerup", onUp);
    return () => {
      stage.removeEventListener("pointermove", onMove);
      stage.removeEventListener("pointerleave", onLeave);
      stage.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      if (frame) window.cancelAnimationFrame(frame);
      if (settle) window.clearTimeout(settle);
      delete stage.dataset.cursor;
    };
  }, [stageRef]);

  return (
    <div ref={cursorRef} className={styles.cursor} data-state="empty" data-visible="false" aria-hidden="true">
      <svg width="44" height="44" viewBox="0 0 44 44" focusable="false">
        <circle className={styles.ring} cx="22" cy="22" r="9" />
        <circle className={styles.dot} cx="22" cy="22" r="2.2" />
        <g className={styles.corners}>
          <path d="M8 14V8h6" />
          <path d="M30 8h6v6" />
          <path d="M36 30v6h-6" />
          <path d="M14 36H8v-6" />
        </g>
        <g className={styles.cross}>
          <path d="M22 4v10M22 30v10M4 22h10M30 22h10" />
        </g>
        <g className={styles.edge}>
          <path d="M10 16l6 6-6 6M34 16l-6 6 6 6" />
        </g>
      </svg>
    </div>
  );
}

"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { WAYS } from "../lib/content";
import { ContextGlyph, ExplorationGlyph } from "../desktop/icons";
import styles from "./Dock.module.css";

/* The entries, carried over from the landing (§7f) — the released views
   only; a deferred view (Spacetime, 2026-09-05) has no control: a fixed column
   of the nav's 60 px controls at the right, vertically centred, with the
   nav's own hover reveal; the current view's control is inverted, as the
   nav marks its active item. The views have no order, so no numbers.
   Below them, past a rule, a view's LOCAL TOOLS — not further
   functions: each a 60 px control in the same measure, revealed by its
   own words, pressed while its panel is open, disabled when it has
   nothing to do. Shared by every TRACE view; each view supplies its
   tools and their words. */

const GLYPHS = { context: ContextGlyph, exploration: ExplorationGlyph } as const;
const ENTRIES = WAYS.filter((w) => !w.deferred);
const STEP = 74;
const RULE = 29;

export function PanelGlyph({ open }: { open: boolean }) {
  return (
    <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" />
      <path d="M15 5v14" />
      {open ? <rect x="15" y="5" width="6" height="14" fill="currentColor" stroke="none" /> : null}
    </svg>
  );
}

export function PlusGlyph() {
  return (
    <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function TableGlyph({ open }: { open: boolean }) {
  return (
    <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" />
      <path d="M3 10h18M3 15h18M9 5v14" />
      {open ? <rect x="3" y="5" width="6" height="5" fill="currentColor" stroke="none" /> : null}
    </svg>
  );
}

export interface DockTool {
  readonly id: string;
  /* the words revealed beside the control: while open / while closed */
  readonly revealOpen: string;
  readonly revealClosed: string;
  readonly open: boolean;
  readonly disabled?: boolean;
  readonly controls?: string;
  readonly onClick: () => void;
  readonly glyph: ReactNode;
}

export interface DockProps {
  /* the current view; a deferred view's key matches no entry and marks nothing */
  readonly active: "context" | "spacetime" | "exploration";
  readonly tools?: readonly DockTool[];
  readonly toolsLabel?: string;
}

export default function Dock({ active, tools = [], toolsLabel = "View tools" }: DockProps) {
  const [revealed, setRevealed] = useState<number | null>(null);
  const hover = (i: number) => ({
    onMouseEnter: () => setRevealed(i),
    onMouseLeave: () => setRevealed((c) => (c === i ? null : c)),
    onFocus: () => setRevealed(i),
    onBlur: () => setRevealed((c) => (c === i ? null : c)),
  });
  const revealText = revealed === null
    ? ""
    : revealed < ENTRIES.length
      ? ENTRIES[revealed].name
      : (() => {
        const tool = tools[revealed - ENTRIES.length];
        return tool ? (tool.open ? tool.revealOpen : tool.revealClosed) : "";
      })();
  const revealTop = revealed === null
    ? 0
    : revealed < ENTRIES.length
      ? revealed * STEP + 30
      : ENTRIES.length * STEP + RULE + (revealed - ENTRIES.length) * STEP + 30;
  return (
    <nav className={styles.dock} aria-label="TRACE functions">
      <ol role="list">
        {ENTRIES.map((w, i) => {
          const Glyph = GLYPHS[w.key as keyof typeof GLYPHS];
          const current = w.key === active;
          return (
            <li key={w.key}>
              <Link
                href={w.href}
                className={styles.item}
                aria-label={w.name}
                aria-current={current ? "page" : undefined}
                data-active={current || undefined}
                {...hover(i)}
              >
                <Glyph />
              </Link>
            </li>
          );
        })}
      </ol>
      {tools.length > 0 ? (
        <div className={styles.tools} role="group" aria-label={toolsLabel}>
          <span className={styles.rule} aria-hidden="true" />
          {tools.map((tool, index) => (
            <button
              key={tool.id}
              type="button"
              className={styles.item}
              aria-label={tool.open ? tool.revealOpen : tool.revealClosed}
              aria-disabled={tool.disabled || undefined}
              aria-expanded={tool.open}
              aria-controls={tool.controls}
              data-active={tool.open || undefined}
              onClick={() => { if (!tool.disabled) tool.onClick(); }}
              {...hover(ENTRIES.length + index)}
            >
              {tool.glyph}
            </button>
          ))}
        </div>
      ) : null}
      <span
        className={styles.reveal}
        data-shown={revealed !== null}
        style={{ top: `${revealTop}px` }}
        aria-hidden="true"
      >
        {revealText}
      </span>
    </nav>
  );
}

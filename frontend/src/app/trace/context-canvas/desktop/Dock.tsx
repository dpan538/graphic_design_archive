"use client";

import SharedDock, { PanelGlyph, PlusGlyph, type DockTool } from "../../_shared/Dock";
import { ADD_CONTEXT, ADD_CONTEXT_NONE, INSPECTOR_CLOSE, INSPECTOR_OPEN } from "../lib/content";

/* The canvas's dock (§7g): the shared TRACE dock with the page's two
   LOCAL TOOLS — the inspector's toggle and the global ADD CONTEXT "+",
   disabled and revealed as "No context to add" when the object has
   nothing governed left to add. */

export interface DockProps {
  readonly active: "context" | "spacetime" | "exploration";
  readonly inspector?: Readonly<{ open: boolean; onToggle: () => void }>;
  readonly add?: Readonly<{ available: number; open: boolean; onOpen: () => void }>;
}

export default function Dock({ active, inspector, add }: DockProps) {
  const tools: DockTool[] = [];
  if (inspector) {
    tools.push({
      id: "inspector",
      revealOpen: INSPECTOR_CLOSE,
      revealClosed: INSPECTOR_OPEN,
      open: inspector.open,
      controls: "context-panel",
      onClick: inspector.onToggle,
      glyph: <PanelGlyph open={inspector.open} />,
    });
  }
  if (add) {
    const label = add.available > 0 ? `${ADD_CONTEXT} (${add.available})` : ADD_CONTEXT_NONE;
    tools.push({
      id: "add",
      revealOpen: label,
      revealClosed: label,
      open: add.open,
      disabled: add.available === 0,
      controls: "context-panel",
      onClick: add.onOpen,
      glyph: <PlusGlyph />,
    });
  }
  return <SharedDock active={active} tools={tools} toolsLabel="Canvas tools" />;
}

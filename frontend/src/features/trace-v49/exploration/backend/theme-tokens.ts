import type { ExplorationThemeTokenSet } from "./types.ts";

export interface ExplorationThemeTokens {
  readonly id: ExplorationThemeTokenSet;
  readonly background: string;
  readonly panel: string;
  readonly ink: string;
  readonly mutedInk: string;
  readonly connector: string;
  readonly nodeFill: string;
  readonly nodeStroke: string;
  readonly divider: string;
  readonly fontFamily: string;
}

export const EXPLORATION_THEME_TOKENS: Readonly<Record<ExplorationThemeTokenSet, ExplorationThemeTokens>> = Object.freeze({
  "neutral-v1": Object.freeze({
    id: "neutral-v1", background: "#f3f1ec", panel: "#fbfaf7", ink: "#202426", mutedInk: "#62686b",
    connector: "#5f696d", nodeFill: "#ffffff", nodeStroke: "#2f3639", divider: "#c8ccca",
    fontFamily: "Arial, Helvetica, sans-serif",
  }),
  "neutral-contrast-v1": Object.freeze({
    id: "neutral-contrast-v1", background: "#ffffff", panel: "#ffffff", ink: "#111111", mutedInk: "#3f3f3f",
    connector: "#111111", nodeFill: "#ffffff", nodeStroke: "#111111", divider: "#777777",
    fontFamily: "Arial, Helvetica, sans-serif",
  }),
});

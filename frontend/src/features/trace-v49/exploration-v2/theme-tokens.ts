import type { ExplorationV2Theme } from "./types.ts";

export interface ExplorationV2ThemeTokens {
  readonly id: ExplorationV2Theme;
  readonly background: string;
  readonly panel: string;
  readonly ink: string;
  readonly mutedInk: string;
  readonly connector: string;
  readonly nodeFill: string;
  readonly expandedNodeFill: string;
  readonly nodeStroke: string;
  readonly focusStroke: string;
  readonly divider: string;
  readonly fontFamily: string;
  readonly treeFontFamily: string;
}

export const EXPLORATION_V2_THEME_TOKENS: Readonly<Record<ExplorationV2Theme, ExplorationV2ThemeTokens>> = Object.freeze({
  "neutral-v1": Object.freeze({
    id: "neutral-v1",
    background: "#f3f1ec",
    panel: "#fbfaf7",
    ink: "#202426",
    mutedInk: "#62686b",
    connector: "#5f696d",
    nodeFill: "#ffffff",
    expandedNodeFill: "#e8ecea",
    nodeStroke: "#2f3639",
    focusStroke: "#111719",
    divider: "#c8ccca",
    fontFamily: "Arial, Helvetica, sans-serif",
    treeFontFamily: "Menlo, Monaco, monospace",
  }),
  "neutral-contrast-v1": Object.freeze({
    id: "neutral-contrast-v1",
    background: "#ffffff",
    panel: "#ffffff",
    ink: "#111111",
    mutedInk: "#3f3f3f",
    connector: "#111111",
    nodeFill: "#ffffff",
    expandedNodeFill: "#eeeeee",
    nodeStroke: "#111111",
    focusStroke: "#000000",
    divider: "#777777",
    fontFamily: "Arial, Helvetica, sans-serif",
    treeFontFamily: "Menlo, Monaco, monospace",
  }),
});

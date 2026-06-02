export type MainSheetLayoutId =
  | "MS01.protocol-ledger"
  | "MS02.evidence-dossier"
  | "MS03.split-bulletin"
  | "MS04.grid-register";

export type MainSheetLayoutPriority = "primary" | "standard" | "support";

export type MainSheetLayoutSpec = {
  label: string;
  priority: MainSheetLayoutPriority;
  frozen: true;
  weight: number;
  role: string;
};

export const MAIN_SHEET_LAYOUTS: Record<MainSheetLayoutId, MainSheetLayoutSpec> = {
  "MS01.protocol-ledger": {
    label: "Protocol ledger",
    priority: "standard",
    frozen: true,
    weight: 2,
    role: "Dense control sheet with heavy register logic, dot leaders, compact image evidence, source rows, and folder rows.",
  },
  "MS02.evidence-dossier": {
    label: "Evidence dossier",
    priority: "primary",
    frozen: true,
    weight: 3.5,
    role: "Primary dramatic evidence sheet with large archival score, strong serif identity, image plate, and source-return context.",
  },
  "MS03.split-bulletin": {
    label: "Split bulletin",
    priority: "primary",
    frozen: true,
    weight: 3.5,
    role: "Primary high-contrast bulletin with black identity field, strong title block, image/source panel, and object dimensions.",
  },
  "MS04.grid-register": {
    label: "Grid register",
    priority: "support",
    frozen: true,
    weight: 1,
    role: "Support register with restrained red construction grid, source metadata, rights block, and classification register.",
  },
};

export const MAIN_SHEET_LAYOUT_ORDER: MainSheetLayoutId[] = [
  "MS01.protocol-ledger",
  "MS02.evidence-dossier",
  "MS03.split-bulletin",
  "MS04.grid-register",
];

export const MAIN_SHEET_LAYOUT_WEIGHT_TOTAL = MAIN_SHEET_LAYOUT_ORDER.reduce(
  (total, layoutId) => total + MAIN_SHEET_LAYOUTS[layoutId].weight,
  0,
);

export function mainSheetLayoutShare(layoutId: MainSheetLayoutId): number {
  return MAIN_SHEET_LAYOUTS[layoutId].weight / MAIN_SHEET_LAYOUT_WEIGHT_TOTAL;
}

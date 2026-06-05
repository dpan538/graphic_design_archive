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

type MainSheetSurfaceLike = {
  surfaceId: string;
  title?: string;
  completenessScore?: number;
  sourceDescription?: string;
  sourceNotes?: string;
  descriptionSummary?: string;
  readingTextLength?: number;
  image?: {
    state?: string;
    url?: string | null;
  };
  folders?: unknown[];
  tables?: Array<{ rows?: unknown[] }>;
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

function stableHash(value: string): number {
  let hash = 2166136261;
  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function textLength(surface: MainSheetSurfaceLike): number {
  return (
    surface.readingTextLength ??
    [
      surface.descriptionSummary,
      surface.sourceDescription,
      surface.sourceNotes,
    ]
      .filter(Boolean)
      .join(" ").length
  );
}

function tableRowCount(surface: MainSheetSurfaceLike): number {
  return (surface.tables ?? []).reduce(
    (total, table) => total + (table.rows?.length ?? 0),
    0,
  );
}

function firstDifferent(
  candidates: MainSheetLayoutId[],
  previous?: MainSheetLayoutId | null,
): MainSheetLayoutId {
  return candidates.find((candidate) => candidate !== previous) ?? candidates[0];
}

/**
 * Deterministic main-sheet layout selector.
 *
 * The four visual assets are not distributed evenly. MS02 and MS03 carry most
 * strong main sheets, MS01 carries dense control ledgers, and MS04 remains a
 * quieter register used sparingly. The caller may pass the previous layout to
 * prevent same-layout repetition inside a folder sequence.
 */
export function selectMainSheetLayout(
  surface: MainSheetSurfaceLike,
  previous?: MainSheetLayoutId | null,
): MainSheetLayoutId {
  const hash = stableHash(surface.surfaceId);
  const imageState = surface.image?.state ?? "IMG00";
  const hasRenderableImage =
    Boolean(surface.image?.url) &&
    (imageState === "IMG01" || imageState === "IMG02" || imageState === "IMG03");
  const rows = tableRowCount(surface);
  const folders = surface.folders?.length ?? 0;
  const length = textLength(surface);
  const completeness = surface.completenessScore ?? 0;

  if (imageState === "IMG00") {
    return firstDifferent(
      rows >= 24 && hash % 3 === 0
        ? ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS04.grid-register"]
        : ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS03.split-bulletin"],
      previous,
    );
  }

  if (rows >= 34 || folders >= 6) {
    return firstDifferent(
      hasRenderableImage
        ? hash % 12 === 0
          ? ["MS04.grid-register", "MS01.protocol-ledger", "MS02.evidence-dossier"]
          : hash % 5 === 0
            ? ["MS03.split-bulletin", "MS01.protocol-ledger", "MS02.evidence-dossier"]
            : hash % 2 === 0
              ? ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS03.split-bulletin"]
              : ["MS02.evidence-dossier", "MS01.protocol-ledger", "MS03.split-bulletin"]
        : ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS03.split-bulletin"],
      previous,
    );
  }

  if (hasRenderableImage && (hash % 3 === 0 || length < 650)) {
    return firstDifferent(
      hash % 4 === 0
        ? ["MS03.split-bulletin", "MS01.protocol-ledger", "MS02.evidence-dossier"]
        : ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS03.split-bulletin"],
      previous,
    );
  }

  if (length >= 850 || completeness >= 92) {
    return firstDifferent(
      hash % 2 === 0
        ? ["MS02.evidence-dossier", "MS01.protocol-ledger", "MS03.split-bulletin"]
        : ["MS01.protocol-ledger", "MS02.evidence-dossier", "MS03.split-bulletin"],
      previous,
    );
  }

  const weightedCycle: MainSheetLayoutId[] = [
    "MS01.protocol-ledger",
    "MS02.evidence-dossier",
    "MS01.protocol-ledger",
    "MS02.evidence-dossier",
    "MS01.protocol-ledger",
    "MS02.evidence-dossier",
    "MS03.split-bulletin",
    "MS01.protocol-ledger",
    "MS02.evidence-dossier",
    "MS04.grid-register",
    "MS03.split-bulletin",
  ];
  const first = weightedCycle[hash % weightedCycle.length];
  return firstDifferent(
    [
      first,
      first === "MS02.evidence-dossier"
        ? "MS01.protocol-ledger"
        : first === "MS01.protocol-ledger"
          ? "MS02.evidence-dossier"
        : "MS02.evidence-dossier",
      "MS03.split-bulletin",
      "MS04.grid-register",
    ],
    previous,
  );
}

export type SubSheetLayoutId =
  | "SS01.schedule-index"
  | "SS02.redline-cv"
  | "SS03.day-column"
  | "SS04.resume-dossier";

export type SubSheetLayoutSpec = {
  label: string;
  relativeWeight: 0.9;
  role: string;
};

export const SUB_SHEET_LAYOUTS: Record<SubSheetLayoutId, SubSheetLayoutSpec> = {
  "SS01.schedule-index": {
    label: "Schedule index",
    relativeWeight: 0.9,
    role: "Dense typographic sub sheet for records with enough metadata to read as a time/index stack.",
  },
  "SS02.redline-cv": {
    label: "Redline CV",
    relativeWeight: 0.9,
    role: "Structured dossier with red rule fields, cropped evidence, and source/classification blocks.",
  },
  "SS03.day-column": {
    label: "Day column",
    relativeWeight: 0.9,
    role: "Vertical event-index sheet with oversized chronology, source fragments, and a modest evidence stamp.",
  },
  "SS04.resume-dossier": {
    label: "Resume dossier",
    relativeWeight: 0.9,
    role: "Resume-like archival summary for a single object, balancing large identity with compact evidence fields.",
  },
};

export const SUB_SHEET_LAYOUT_ORDER: SubSheetLayoutId[] = [
  "SS01.schedule-index",
  "SS02.redline-cv",
  "SS03.day-column",
  "SS04.resume-dossier",
];

/**
 * Type definitions for the public archive box mock payload.
 *
 * These match `data/public_surface_mock_v0.json` exactly and are the binding
 * frontend contract. Later generated payloads
 * (`generated/public_surfaces_v1.json`) must remain shape-compatible with the
 * top-level keys: meta, folderTypes, folders, surfaces.
 */

export type FolderTypeKey = "region" | "theme" | "medium" | "movement";

/** Image-presence state. Controls image display only, never sheet size. */
export type ImageState = "IMG00" | "IMG01" | "IMG02" | "IMG03" | "IMG04";

/** Surface kind. Drives which template/component renders. */
export type SurfaceKind = "sheet" | "card" | "fallback_stub";

/** Template identifiers carried by the payload (do not infer in the frontend). */
export type TemplateId =
  | "sheet.main.v0"
  | "sheet.img00.v0"
  | "sheet.text.v0"
  | "card.sparse.v0"
  | "stub.fallback.v0"
  | (string & {});

/** The six fixed table kinds. */
export type TableKind =
  | "SOURCE"
  | "NORMALIZED"
  | "RIGHTS"
  | "CLASSIFICATION"
  | "RELATIONS"
  | "CITATIONS";

export interface ArchiveMeta {
  generatedAt: string;
  status: "mock" | string;
  note: string;
}

export interface FolderType {
  type: FolderTypeKey;
  label: string;
  /** Folder-type color token. Used only on tab / edge / label. */
  color: string;
  scopeNote: string;
}

export interface FolderAuthorityRefs {
  regionIds?: string[];
  geoIds?: string[];
  themeKeys?: string[];
  mediaIds?: string[];
  movementIds?: string[];
  regionalMovementIds?: string[];
}

export interface Folder {
  folderId: string;
  type: FolderTypeKey;
  slug: string;
  title: string;
  dateStart: number | null;
  dateEnd: number | null;
  scopeNote: string;
  surfaceIds: string[];
  relatedFolderIds: string[];
  authorityRefs?: FolderAuthorityRefs;
}

/** Compact folder membership reference carried on a surface. */
export interface SurfaceFolderRef {
  folderId: string;
  type: FolderTypeKey;
  title: string;
}

export interface SurfaceImage {
  state: ImageState;
  hasImageFrame: boolean;
  /** Remote image URL. Only render an actual image when present (IMG01/02/03). */
  url: string | null;
  credit: string | null;
  licenseLabel: string | null;
}

export interface SurfaceRights {
  state: string;
  displayPolicy: string;
  label: string;
}

export interface SurfaceReviewGates {
  sourceUrl: boolean;
  rightsReviewed: boolean;
  dateKnown: boolean;
  classificationKnown: boolean;
}

/** A table row is a tuple of [label, value]. */
export type TableRow = [string, string];

export interface SurfaceTable {
  kind: TableKind;
  rows: TableRow[];
}

/** Optional hint that lets the generator pin a specific layout. */
export type LayoutHint =
  | "main"
  | "text"
  | "plate"
  | "dual"
  | "compound"
  | "support_packet"
  | "merge_candidate";

export interface Surface {
  surfaceId: string;
  sourceRecordId: string;
  surfaceType: SurfaceKind;
  templateId: TemplateId;
  /** May still contain legacy HN* segments — display as-is. */
  provisionalDisplayNumber: string;
  seqLabel: string;
  historicalNodeIds: string[];
  movementIds: string[];
  title: string;
  creator: string;
  dateText: string;
  dateStart: number | null;
  dateEnd: number | null;
  placeText: string;
  objectType: string;
  medium: string;
  sourceName: string;
  sourceUrl: string;
  accessDate: string;
  descriptionSummary?: string;
  sourceDescription?: string;
  sourceNotes?: string;
  sourceSubjects?: string;
  readingTextLength?: number;
  historicalContextNote?: string;
  classificationRationale?: string;
  uncertaintyNote?: string;
  citationBasis?: string;
  completenessScore: number;
  surfaceDisposition?: string;
  publicationRole?: string;
  publicationGate?: Record<string, unknown>;
  reviewGates: SurfaceReviewGates;
  image: SurfaceImage;
  /** Optional additional image bays (used by the dual-plate / compound layouts). */
  images?: SurfaceImage[];
  rights: SurfaceRights;
  folders: SurfaceFolderRef[];
  tables: SurfaceTable[];
  /** Optional layout pin; falls back to deterministic selection by content. */
  layoutHint?: LayoutHint;
  /** Optional child records for the compound layout (L05). */
  compoundChildren?: CompoundChild[];
}

/** A weak record cell shown inside a compound sheet (L05). */
export interface CompoundChild {
  title: string;
  dateText: string;
  sourceName: string;
  sourceUrl: string;
  imageState: ImageState;
  note: string;
}

export interface PublicSurfaceMock {
  meta: ArchiveMeta;
  folderTypes: FolderType[];
  folders: Folder[];
  surfaces: Surface[];
  researchDossiers?: ResearchDossier[];
  appendices?: ResearchAppendix[];
  readingNotes?: ReadingNoteRecord[];
  bookmarks?: ResearchBookmark[];
  registrationCards?: RegistrationCard[];
}

export type DossierPageType =
  | "main_sheet"
  | "subsheet"
  | "text_page"
  | "appendix"
  | "card"
  | "slip"
  | "bookmark"
  | "child_source_record";

export interface DossierPageRef {
  pageId: string;
  pageType: DossierPageType;
  surfaceId: string;
  displayNumber?: string;
  title?: string;
  imageState?: ImageState;
  layoutId?: string | null;
  exportable: boolean;
  rightsState?: string;
  sourceName?: string;
  sourceUrl?: string;
  appendixReasons?: string[];
}

export interface ResearchDossier {
  dossierId: string;
  anchorSurfaceId: string;
  anchorType: "main_sheet" | "subsheet" | "card";
  sourceScope:
    | "single_anchor_record"
    | "compound_or_series_cluster"
    | "support_packet"
    | "card_record"
    | (string & {});
  title: string;
  dateStart: number | null;
  dateEnd: number | null;
  folderIds: string[];
  pageCount: number;
  pageSequence: DossierPageRef[];
  exportPolicy: {
    selectablePages: boolean;
    pdfAllowed: boolean;
    stampEveryPage: boolean;
    includeRightsPage: boolean;
    localImageCopyAllowed: boolean;
  };
  groupingBasis: string;
}

export interface ResearchAppendix {
  appendixId: string;
  surfaceId: string;
  title: string;
  displayNumber: string;
  layoutId: string;
  reasons: string[];
  tableRows: number;
}

export interface ReadingNoteRecord {
  readingNoteId: string;
  noteScope: "folder" | "surface" | (string & {});
  folderId?: string;
  surfaceId?: string;
  type?: FolderTypeKey;
  title: string;
  displayNumber?: string;
  dateStart: number | null;
  dateEnd: number | null;
  surfaceCount?: number;
  sourceName?: string;
  sourceUrl?: string;
  imageState?: ImageState;
  readingLength?: number;
  scopeNote: string;
  displayRule: string;
}

export interface ResearchBookmark {
  bookmarkId: string;
  surfaceId?: string;
  folderId?: string;
  type?: FolderTypeKey;
  title: string;
  dateStart?: number | null;
  dateEnd?: number | null;
  imageState?: ImageState;
  reason?: string;
  displayRule: string;
}

export interface RegistrationCard {
  registrationId: string;
  folderId: string;
  type: FolderTypeKey;
  title: string;
  memberPages: {
    surfaceId: string;
    displayNumber?: string;
    title?: string;
  }[];
  displayRule: string;
}

/* Context Canvas — every string on the page (FRONTEND_DESIGN_DECISION.md §7g).
   The name, question and boundary are the landing's own words for this
   view (trace/lib/content.ts WAYS) so the two pages never drift; the
   header statement is the owner's sentence; every other string restates
   what the governed Context projection already says. Nothing here names a
   provider, counts a probability, or asserts a relation between records. */

import { WAYS } from "../../lib/content";

const way = WAYS.find((w) => w.key === "context");
if (!way) throw new Error("Context Canvas: the landing's WAYS entry for Context is missing.");

export const KICKER = "TRACE";
export const NAME = way.name;
export const STATEMENT = "See how one archive object is positioned within project-curated context.";
export const QUESTION = way.question;
export const BOUNDARY = way.boundary;
export const CONTEXT_ROLE = "Project-curated context";

/* the three dimensions of context — the governed vocabulary's own order;
   the words are the owner's, the data's public labels ("Medium / format",
   "Theme", "Movement context") appear in the inspector */
export type ContextKind = "medium" | "theme" | "movement_context";
export const KINDS: readonly Readonly<{ kind: ContextKind; word: string }>[] = Object.freeze([
  Object.freeze({ kind: "medium", word: "Medium" }),
  Object.freeze({ kind: "theme", word: "Theme" }),
  Object.freeze({ kind: "movement_context", word: "Movement" }),
]);
export const kindWord = (kind: ContextKind): string => KINDS.find((k) => k.kind === kind)?.word ?? kind;

export const SELECTED_OBJECT = "Selected object";
export const NOT_RECORDED = "Not recorded";
export const SET_ASIDE = "set aside";
export const ON_CANVAS = "on canvas";
/* the rail's count: how many of the object's governed contexts of this
   kind stand on the canvas, out of how many it carries */
export const ON_CANVAS_OF = (visible: number, total: number) => `${visible}/${total} ${ON_CANVAS}`;
/* a drag that ends where an item cannot stand is put back, and says why */
export const DROP_OUTSIDE = (label: string, word: string) => `"${label}" stays in ${word}: a context takes a place in its own field.`;
export const DROP_SWAPPED = (label: string, other: string, word: string) => `"${label}" and "${other}" changed places in ${word}.`;
export const DROP_OBJECT = "The object stays where its fields are laid out around it; drag the ground to pan.";
/* the canonical sentence for a valid empty dataset (TERMINOLOGY_AND_UI_COPY.md) */
export const EMPTY_CONTEXT = "No governed Context representations are available for this record.";
export const EMPTY_CANVAS_NOTE = "The selected object stays on the canvas; no context is inferred from Search, Spacetime, object metadata or Exploration.";
export const LOADING = (stableId: string) => `Loading governed context for ${stableId}.`;

/* 01 — choosing the object (§7g): a reader-facing search by title or
   public record ID, a few worked examples picked from the data by fixed
   criteria, and the exact public record ID behind a fold; the
   projection's twelve deterministic samples are a QA tool, shown in
   development or with ?qa=1 only, never as a reader's choice */
export const CHANGE_OBJECT = "Change the selected object";
export const CHOOSE_TITLE = "Choose an object";
export const SEARCH_LABEL = "Search by title or ID";
export const SEARCH_PLACEHOLDER = "Title, or SURF-…";
export const SEARCH_HINT = "Two letters of a title, or a public record ID.";
export const SEARCH_SEARCHING = "Searching…";
export const SEARCH_NONE = (query: string) => `No reader-facing object matches "${query}". A record-only object opens by its exact ID.`;
export const SEARCH_RESULTS = (n: number) => `${n} match${n === 1 ? "" : "es"}`;
export const SEARCH_FAILED = "The search did not answer; try again, or open a record ID.";
export const CONTEXTS_COUNT = (n: number) => `${n} context${n === 1 ? "" : "s"}`;
export const RECORD_ONLY = "record-only";
export const EXAMPLES_TITLE = "Start with an example";
export const EXAMPLE_ROLE: Readonly<Record<string, string>> = Object.freeze({
  three_contexts: "One context of each kind",
  medium_theme: "Medium and Theme; Movement not recorded",
  two_themes: "Two Themes",
  two_movements: "Two Movements: the most context any object carries",
  other_language: "A title in another language",
});
export const OPEN_BY_ID = "Open by record ID";
export const RECORD_ID_LABEL = "Public record ID";
export const RECORD_ID_PLACEHOLDER = "SURF-…";
export const LOAD_RECORD = "Open record";
export const RECORD_ID_NOTE = "Any of the governed public records, including record-only ones.";
export const QA_TITLE = "QA samples";
export const QA_NOTE = (n: string, total: string) => `${n} of ${total} governed public records, evenly spaced by stable public ID. For deterministic testing; not a representative sample.`;

/* 02 — the rail's controls */
/* the canvas layouts — presets over the one governed composition template
   ("context-overview" stays the contract's name; the reader never sees
   the word template) */
export const LAYOUT_LABEL = "Canvas layout";
export const LAYOUT_NOTE = "Layout only: the same governed contexts, arranged differently.";
export type LayoutPreset = "overview" | "focus" | "columns" | "dense";
export const LAYOUTS: readonly Readonly<{ id: LayoutPreset; label: string; brief: string }>[] = Object.freeze([
  Object.freeze({ id: "overview", label: "Overview", brief: "The object at the centre, the three dimensions around it." }),
  Object.freeze({ id: "focus", label: "Focus", brief: "One dimension read in full; the other two kept compact." }),
  Object.freeze({ id: "columns", label: "Columns", brief: "The object above three equal columns, for comparison." }),
  Object.freeze({ id: "dense", label: "Dense", brief: "Three bands, for objects with many terms." }),
]);
export const FOCUS_LABEL = "Focus";
export const DIMENSIONS_TITLE = "Context";
export const FOCUS_KIND = (word: string) => `Bring the ${word} field into view`;
export const ADD_KIND = (word: string) => `Add the set-aside ${word} context back to the canvas`;
export const AVAILABLE = "available";
export const AVAILABLE_TITLE = (word: string) => `Available ${word}`;
export const SHOW_AVAILABLE = (word: string, n: number) => `Show ${n} available ${word} context${n === 1 ? "" : "s"}`;
export const HIDE_AVAILABLE = (word: string) => `Hide the available ${word} contexts`;
export const ADD_TERM = (label: string) => `Add ${label} to the canvas`;
export const FIELD_AVAILABLE = (n: number) => `+ ${n} ${AVAILABLE}`;
/* the dock's local tools: the inspector and the global add */
export const ADD_CONTEXT = "Add context";
export const ADD_CONTEXT_NONE = "No context to add";
export const ADD_CONTEXT_TITLE = "Add context";
export const ADD_CONTEXT_NOTE = "Governed context for this object that is not on the canvas yet.";
export const NO_ADDITIONAL = "No additional context";
export const BACK_TO_INSPECTOR = "Back to the inspector";
export const FOCUS_ON = (word: string) => `Read ${word} in full`;
export const FOCUS_NONE = (word: string) => `${word}: not recorded for this object`;
export const OPEN_ROWS = "Context rows";
export const OPEN_ROWS_NOTE = "The canvas as rows, and as text.";

/* 03 — the stage and its toolbar */
export const STAGE_LABEL = "Context Canvas. The selected object in the centre; its project-curated contexts around it in three fields — Medium, Theme, Movement. Drag a chip to move it, drag the ground to pan, use the wheel to zoom.";
export const ZOOM_IN = "Zoom in";
export const ZOOM_OUT = "Zoom out";
export const FIT = "Fit";
export const ARRANGE = "Arrange";
export const UNDO = "Undo";
export const REDO = "Redo";
export const RESET_CANVAS = "Reset";
export const RESET_CANVAS_LABEL = "Reset the canvas to its template";
export const EXPORT_PNG = "Export PNG";
export const CARD_KICKER = "Context map";
export const CARD_SITE = "mgdarchive.com";
export const CARD_RECORD = "Research record";
export const CARD_WORDMARK = ["Modern Graphic Design", "Archive"] as const;
export const EXPORTING = "Exporting…";
export const FIELD_SET_ASIDE = (n: number) => `${n} ${SET_ASIDE}`;
export const CANVAS_CLAIM = BOUNDARY;
export const STRESS_BANNER = "Synthetic stress fixture — layout testing only; not a production record and not a claim that any archive object carries this composition.";

/* 04 — the inspector */
export const INSPECTOR_TITLE = "Inspector";
export const INSPECTOR_OPEN = "Inspector";
export const INSPECTOR_CLOSE = "Close inspector";
export const RAIL_COLLAPSE = "Collapse the rail";
export const RAIL_EXPAND = "Expand the rail";
export const WHY_HERE = "Why this is here";
export const PROVENANCE = "Provenance";
export const ABOUT_DIMENSION = "About this dimension";
export const INSPECTOR_IDLE = "Select a context on the canvas to read what it is, why it is present and where it comes from.";
export const INSPECTOR_ROOT_NOTE = "The starting point of this canvas. Its contexts describe how the archive files it, not what happened to it.";
export const OPEN_OBJECT = "Open the object record";
export const WHY_APPEARS = "Why it appears";
export const SOURCE_BASIS = "Source basis";
export const NOT_ESTABLISHED = "What it does not establish";
export const RELEASE = "Release";
export const PROJECTION = "Projection";
export const INTEGRITY = "Integrity";
export const COPY_HASH = "Copy full";
export const COPY_TECHNICAL = "Copy technical provenance";
export const COPIED_HASH = "Copied the full hash.";
export const COPIED_TECHNICAL = "Copied the technical provenance.";
export const COVERAGE = (count: string, cohort: string) => `${count} of ${cohort} public records carry this classification.`;
export const TECHNICAL = "Technical provenance";
export const ADD = "Add to canvas";
export const REMOVE = "Remove from canvas";

/* 05 — the accessible equivalent */
export const ROWS_TITLE = "Context rows";
export const ROWS_NOTE = "The same content as the canvas; a row selected is a chip selected.";
export const COPY_CONTEXT = "Copy context";
export const COPIED = "Copied the context as a table.";
export const COPY_UNAVAILABLE = "Copying is not available in this browser; the rows carry the same content.";
export const ARCHIVE_NAME = "Modern Graphic Design Archive";
export const ROW_ADD = "Add";
export const ROW_REMOVE = "Remove";
export const GO_TO_CHIP = "Go to chip";

/* 08 — failures (the codes are the governed reader's own) */
export const FAILURE_TITLE = "Context unavailable";
export const FAILURE_NOTE = "No Canvas dataset was mounted and no local composition was read or written.";
export const RETRY = "Retry the same request";
export const INVALID_RECORD_ID_MESSAGE = "The record parameter is not a valid public stable ID.";

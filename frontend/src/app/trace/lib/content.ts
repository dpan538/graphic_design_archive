/* TRACE landing page copy — final wording set by the owner (FRONTEND_DESIGN_DECISION.md §7f).
   The page answers four things only: what TRACE is; what each view is for
   (two released — Context Canvas, Exploration — and Spacetime, a research
   direction under review that keeps its place in the sequence but has no
   entry); how they relate; how the computed results may and may not be
   read. No recents, no trending, no recommendations, no AI-generated
   questions, no marketing CTA, no System suggests on the landing. */

export const TRACE_TITLE = "TRACE";
export const TRACE_LINE = "Two research views. One governed archive.";
export const TRACE_LEAD =
  "TRACE examines the public archive through contextual, spatial and associative structures without treating computational representation as historical certainty.";

/* the views — no order among them, so no numbers. A DEFERRED view keeps
   its screen in the sequence and its note, states its status, and has no
   href, no control and no leader line: it cannot be entered. */
export type Way = {
  key: string;
  name: string;
  href: string;
  question: string;
  brief: string;
  boundary: string;
  does: string;
  deferred?: true;
  status?: string;
};

/* Spacetime's release boundary, in the owner's words (2026-09-05): not
   failed — not released, because the archive does not yet meet the
   coverage threshold; the projection stays frozen as research
   infrastructure (docs/frontend/SPACETIME_RESEARCH_READINESS_CENSUS_v1.md) */
export const SPACETIME_STATUS = "Not available in this release";
export const SPACETIME_RELEASE_NOTE =
  "Spacetime is not released in v49 because the current archive does not yet meet the geographic and temporal coverage threshold required for this research surface.";

export const WAYS: Way[] = [
  {
    key: "context",
    name: "Context Canvas",
    href: "/trace/context-canvas",
    question: "Where does this object sit?",
    brief: "Examine how a selected record sits within project-curated medium, theme and movement contexts.",
    boundary: "Context describes archival positioning, not historical influence.",
    does: "In the function: choose a record; read its governed medium, theme and movement representations in one of three composition templates, with the same rows in text and a public-safe export.",
  },
  {
    key: "spacetime",
    name: "Spacetime",
    href: "",
    question: "A research direction under review.",
    brief: "Spacetime examines how recorded geographic context changes across time. The current v49 archive is not yet geographically balanced enough to support this as a public comparative research surface.",
    boundary: "",
    does: "",
    deferred: true,
    status: SPACETIME_STATUS,
  },
  {
    key: "exploration",
    name: "Exploration",
    href: "/trace/exploration",
    question: "What becomes worth questioning when records are considered together?",
    brief: "Move through evidence-qualified associations and inspect how concepts can be composed within the current governed research space.",
    boundary: "",
    does: "In the function: the validated map — at most eight visible concepts and their generic associations — with its plain-text tree and exports; then, apart, the eleven scoped open inquiries.",
  },
];

/* the four shared principles — titles only on the landing; the reading
   behind each lives in About / Methodology */
export const PRINCIPLES: string[] = [
  "Provenance remains visible",
  "Computation does not become claim",
  "Uncertainty stays visible",
  "Governed, not generated on demand",
];

export const BASELINE_NOTE = "TRACE is an evidence-bounded research baseline, not a complete map of design history.";

/* the concept, in the owner's words: history between records */
export const TRACE_DEFINITION =
  "TRACE is an evidence-bounded environment for reading history between records. It moves from individual objects toward context, distribution, association, and inquiry without turning computational patterns into historical certainty.";
export const CLOSING_WORD = "TRACE";
export const CLOSING = "the design history no single record can show on its own.";

/* the interlayer between Spacetime and Exploration */
export const BETWEEN = {
  name: "Between records",
  question: "What do records show only when considered together?",
  brief: "Read together, records form patterns that no single record carries: recurrences of context, gatherings in time and place, concepts that keep appearing side by side. TRACE keeps these as observations under evidence.",
  boundary: "A pattern is something to question, not something history has settled.",
};

/* the captions inserted into the scene as the scroll goes on: which
   screen, how far into its hold (0..1), where on the sheet (%), what;
   labels are short, paragraphs are for reading — the reader can stop */
export type Caption = { screen: number; at: number; x: number; y: number; text: string; align?: "left" | "right"; kind?: "label" | "para"; width?: number };
export const CAPTIONS: Caption[] = [
  { screen: 0, at: 0.2, x: 78, y: 15, text: "the public archive · 7,995 records" },
  { screen: 0, at: 0.5, x: 5, y: 56, text: "records pass through context, distribution, association" },
  { screen: 0, at: 0.8, x: 94, y: 73, text: "time is linear · context is not", align: "right" },
  { screen: 1, at: 0.1, x: 4, y: 17, width: 30, text: "one record, and the contexts it is filed in" },
  { screen: 1, at: 0.3, x: 4, y: 7, kind: "para", width: 30, text: "Not who it influenced — where it sits. A single record is read against the medium, theme and movement contexts the project has filed it in." },
  { screen: 1, at: 0.6, x: 4, y: 7, kind: "para", width: 30, text: "That is archival positioning. It makes no claim about historical influence, and the canvas never draws an arrow from one record to another." },
  { screen: 1, at: 0.75, x: 4, y: 72.5, width: 34, text: "medium · theme · movement — a path through contexts" },
  { screen: 1, at: 0.9, x: 97, y: 62, text: "contexts as a field", align: "right" },
  { screen: 2, at: 0.1, x: 5, y: 7, width: 30, text: "where records gather — mapped geographies" },
  { screen: 2, at: 0.3, x: 5, y: 80, kind: "para", width: 26, text: "Not an object's exact path. Records are gathered by period and by governed geography, and read for concentration and for absence." },
  { screen: 2, at: 0.6, x: 5, y: 80, kind: "para", width: 26, text: "A map of what the archive holds and where it is silent — not of where things moved. Geographies without an evidence-backed point stay in the count and off the map." },
  { screen: 2, at: 0.8, x: 62, y: 77, text: "23 periods — when", align: "right" },
  { screen: 3, at: 0.15, x: 5.2, y: 62, kind: "para", width: 24, text: "Between the views something happens that none of them owns. A record is placed in its context; contexts gather in time and place; gatherings repeat; repetition becomes a pattern worth asking about." },
  { screen: 3, at: 0.55, x: 5.2, y: 62, kind: "para", width: 24, text: "Each step keeps its evidence. None of them turns into certainty: the scroll rounds the figure and returns it to its lines, and the figure itself never changes." },
  { screen: 3, at: 0.8, x: 5.2, y: 84, text: "record → context → pattern → association → question" },
  { screen: 4, at: 0.1, x: 26, y: 4.5, text: "association — generic, non-directional" },
  { screen: 4, at: 0.3, x: 97, y: 76, kind: "para", width: 26, align: "right", text: "From record to context to pattern to association — and on to a new research question." },
  { screen: 4, at: 0.6, x: 97, y: 76, kind: "para", width: 26, align: "right", text: "An association is generic and has no direction; an inquiry is a question the evidence has not answered. They never share a map." },
  { screen: 4, at: 0.75, x: 4, y: 68.3, text: "resonance between records" },
  { screen: 4, at: 0.9, x: 4, y: 4.5, text: "open inquiry — held apart" },
];

export type Baseline = { objects: number; periods: number; geographies: number; associations: number; inquiries: number; yearFrom: number; yearTo: number };

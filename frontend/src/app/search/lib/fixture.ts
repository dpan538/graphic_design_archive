/* Search — design exploration fixture.
 *
 * Synthetic public archive objects: real object types, themes, movements, places
 * and years; descriptive titles and generic studio names — no claim about a
 * specific historical work or person. Shaped to the fields a Search result row
 * renders. The live search.public-objects.v1 API is not wired. */

export type SearchRecord = {
  id: string;
  title: string;
  credited: string | null;
  displayDate: string;
  year: number;
  place: string;
  objectType: string;
  themes: string[];
  movements: string[];
  deliveryState: "REMOTE_IMAGE" | "SOURCE_VIEWER" | "CITATION_ONLY";
};

export const OBJECT_TYPES = [
  "Poster",
  "Book",
  "Magazine cover",
  "Type specimen",
  "Identity",
  "Catalogue",
  "Record sleeve",
  "Signage",
  "Stamp",
  "Packaging",
] as const;

export const THEMES = [
  "Advertising",
  "Culture",
  "Politics",
  "Public information",
  "Typography",
  "Music",
  "Editorial",
  "Identity",
] as const;

/* Movement coverage is deliberately sparse (see §3). Most records carry none. */
export const MOVEMENTS = [
  "Constructivism",
  "New Typography",
  "Swiss Style",
  "Psychedelic",
  "Punk",
  "New Wave",
] as const;

export const PUBLIC_RECORD_COUNT = 7995;

const D: Array<
  [string, string, string | null, number, string, string, string[], string[]]
> = [
  ["MGDA-000148", "Type specimen for a sans-serif family", "Schrift-Werkstatt", 1926, "Frankfurt", "Type specimen", ["Typography"], ["New Typography"]],
  ["MGDA-000203", "Poster for a workers' theatre production", null, 1928, "Moscow", "Poster", ["Politics", "Culture"], ["Constructivism"]],
  ["MGDA-000377", "Tourism poster for a mountain railway", "Studio Halvorsen", 1931, "Zürich", "Poster", ["Advertising"], []],
  ["MGDA-000455", "Book jacket for a poetry anthology", "M. Berger", 1934, "Leipzig", "Book", ["Editorial"], []],
  ["MGDA-000560", "Poster for an international exposition", "P. Roussel", 1937, "Paris", "Poster", ["Culture", "Advertising"], []],
  ["MGDA-000604", "Public-health notice on food rationing", "Ministry information unit", 1939, "London", "Poster", ["Public information", "Politics"], []],
  ["MGDA-000781", "Identity for a national airline", "Werkstatt für Gestaltung", 1948, "Copenhagen", "Identity", ["Identity", "Advertising"], []],
  ["MGDA-000844", "Grid-based poster for a design society", "Atelier recorded on the sheet", 1951, "Zürich", "Poster", ["Typography", "Culture"], ["Swiss Style"]],
  ["MGDA-000931", "Exhibition poster for a graphic-design review", "Atelier recorded on the sheet", 1954, "Zürich", "Poster", ["Typography", "Culture"], ["Swiss Style"]],
  ["MGDA-001005", "Poster for a contemporary music festival", "Atelier recorded on the sheet", 1956, "Zürich", "Poster", ["Music", "Culture"], ["Swiss Style"]],
  ["MGDA-001048", "Type specimen for a foundry", "Haas-Werkstatt", 1957, "Münchenstein", "Type specimen", ["Typography"], ["Swiss Style"]],
  ["MGDA-001094", "Signage programme for a transport authority", "Design unit", 1958, "London", "Signage", ["Public information"], []],
  ["MGDA-001133", "Poster protesting nuclear testing", null, 1959, "Warsaw", "Poster", ["Politics"], []],
  ["MGDA-001188", "Record sleeve for a jazz label", "T. Adler", 1960, "New York", "Record sleeve", ["Music"], []],
  ["MGDA-001221", "Corporate identity manual", "Design office", 1961, "Chicago", "Identity", ["Identity"], []],
  ["MGDA-001357", "Poster for an Olympic host city", "Organising committee studio", 1964, "Tokyo", "Poster", ["Public information", "Identity"], []],
  ["MGDA-001444", "Anti-war demonstration poster", null, 1966, "Berkeley", "Poster", ["Politics"], ["Psychedelic"]],
  ["MGDA-001487", "Psychedelic concert poster", "Studio for visual design", 1967, "San Francisco", "Poster", ["Music", "Culture"], ["Psychedelic"]],
  ["MGDA-001522", "Exhibition poster for a municipal cultural programme", "Atelier recorded on the sheet", 1968, "Zürich", "Poster", ["Typography", "Public information"], ["Swiss Style"]],
  ["MGDA-001569", "Annual report for a manufacturing group", "Design office", 1969, "Stuttgart", "Catalogue", ["Identity", "Editorial"], []],
  ["MGDA-001656", "Wayfinding for an Olympic park", "Exhibition graphics team", 1972, "Munich", "Signage", ["Public information", "Identity"], []],
  ["MGDA-001744", "Book series design for a university press", "M. Berger", 1975, "Cambridge", "Book", ["Editorial", "Typography"], []],
  ["MGDA-001788", "Punk gig flyer", null, 1977, "London", "Poster", ["Music", "Culture"], ["Punk"]],
  ["MGDA-001875", "Postage stamp series on folk craft", "State printing office", 1980, "Budapest", "Stamp", ["Culture", "Public information"], []],
  ["MGDA-001912", "New-wave record sleeve", "Studio for visual design", 1982, "Manchester", "Record sleeve", ["Music"], ["New Wave"]],
  ["MGDA-001999", "Lecture-series poster for an architecture school", "K. Novak", 1986, "New York", "Poster", ["Typography", "Culture"], ["New Wave"]],
  ["MGDA-002087", "Type specimen for a digital foundry", "Schrift-Werkstatt", 1991, "The Hague", "Type specimen", ["Typography"], []],
  ["MGDA-002140", "Festival identity for an electronic-music event", "Studio for visual design", 1994, "Berlin", "Identity", ["Music", "Identity"], []],
  ["MGDA-002233", "Public-transport information redesign", "Design unit", 2001, "Paris", "Signage", ["Public information"], []],
  ["MGDA-002331", "Poster archive retrospective", "Cooperative design workshop", 2011, "Zürich", "Poster", ["Culture", "Typography"], []],
];

const DELIVERY: SearchRecord["deliveryState"][] = [
  "REMOTE_IMAGE",
  "SOURCE_VIEWER",
  "CITATION_ONLY",
];

export const RECORDS: SearchRecord[] = D.map(
  ([id, title, credited, year, place, objectType, themes, movements], i) => ({
    id,
    title,
    credited,
    displayDate: String(year),
    year,
    place,
    objectType,
    themes,
    movements,
    deliveryState: DELIVERY[i % DELIVERY.length],
  }),
);

/* Four deterministic starter queries — real values, no model call, no ranking
   or personalisation behind them. They are a hand-picked constant.

   Chosen to span the three vocabularies a reader can enter by — movement,
   object type, theme — and to read as design entry points. The previous set
   ended on a bare "music": a real theme (record sleeves, concert posters,
   sheet music), but as an opening suggestion in a graphic-design archive it
   reads as subject matter rather than as a way in. "Record sleeve" reaches
   the same material through its design form. */
export const STARTERS = ["Swiss Style", "Type specimen", "Record sleeve", "Public information"];

export const YEAR_MIN = Math.min(...RECORDS.map((r) => r.year));
export const YEAR_MAX = Math.max(...RECORDS.map((r) => r.year));

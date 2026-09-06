import type { PublicSpacetimeGeographyClass, PublicSpacetimeMappingState, PublicSpacetimePrecisionBreakdown } from "@/features/trace-v49/spacetime/governed/types";
import { WAYS } from "../../lib/content";

/* Spacetime — every string the desktop shows (FRONTEND_DESIGN_DECISION.md
   §7h). The copy restates the governed atlas: records, the archive,
   recorded context, the selected period, the public aggregate — never
   activity, influence or importance. Figures are the atlas's own. */

const WAY = WAYS.find((way) => way.key === "spacetime");

export const KICKER = "TRACE";
export const NAME = WAY?.name ?? "Spacetime";
export const STATEMENT = "See where archive records gather across time and governed geographic context.";
export const BOUNDARY = "Marks represent aggregate recorded geographic context, not object coordinates.";

/* 01 — the period profile */
export const PERIOD_LABEL = "Period";
export const PERIODS_LABEL = "Periods, 1800s to 2020s";
export const PUBLIC_RECORDS = (n: number) => `${n.toLocaleString("en-US")} public record${n === 1 ? "" : "s"}`;
export const RECORDS = (n: number) => `${n.toLocaleString("en-US")} record${n === 1 ? "" : "s"}`;
export const GEOGRAPHIES = (n: number) => `${n.toLocaleString("en-US")} recorded geograph${n === 1 ? "y" : "ies"}`;
export const TOP_CONCENTRATION = "Top concentration";
export const SHARE_OF_PERIOD = (share: number) => `${(share * 100).toFixed(1)}% of public archive records in this period`;
export const SHARE_SHORT = (share: number) => `${(share * 100).toFixed(1)}%`;
export const PREVIOUS_PERIOD = "Previous period";
export const CURRENT_PERIOD = "Current period";
export const NEXT_PERIOD = "Next period";
export const MAPPED = (n: number) => `${n.toLocaleString("en-US")} mapped`;
export const NOT_MAPPED = (n: number) => `${n.toLocaleString("en-US")} not mapped`;
export const DATA_QUALITY = "Data quality";
export const DATA_QUALITY_NOTE = "How the records of this period are dated, and how many stand on the map.";
export const PRECISION_WORDS: Readonly<Record<keyof PublicSpacetimePrecisionBreakdown, string>> = Object.freeze({
  day: "day",
  month: "month",
  year: "year",
  range: "range",
  approximate: "approximate",
  unknown: "unknown",
});
export const precisionLine = (value: PublicSpacetimePrecisionBreakdown): string =>
  (Object.keys(PRECISION_WORDS) as (keyof PublicSpacetimePrecisionBreakdown)[])
    .filter((key) => value[key] > 0)
    .map((key) => `${PRECISION_WORDS[key]} ${value[key].toLocaleString("en-US")}`)
    .join(" · ");
export const RAIL_COLUMNS = "Columns: public records by recorded year in the current archive release.";
export const RAIL_ABOUT = "About the periods";
export const RAIL_OVERLAP = "A decade's total is the governed period's: a range record counts in every period it overlaps, so the decade can exceed the sum of its years.";
export const WINDOW_WORDS = Object.freeze({ previous: "Previous", current: "Current", next: "Next" });

/* 02 — the map: its layer and its style */
export const MAP_LABEL = "Aggregate map";
export const LAYER_LABEL = "Map layer";
export const LAYERS = Object.freeze([
  { id: "distribution", label: "Distribution", brief: "Where the records of this period gather." },
  { id: "temporal", label: "Temporal", brief: "How each place's records stand in the previous, this and the next period." },
] as const);
export const STYLE_LABEL = "Map style";
export const VIEWS = Object.freeze([
  { id: "aggregate", label: "Aggregate", brief: "One mark per mapped geography; its size follows the record count." },
  { id: "density", label: "Density", brief: "The record count as derived dots inside the geography." },
  { id: "texture", label: "Texture", brief: "The count tier as a pattern over the geography." },
] as const);
export const VIEW_HELP = "About the styles";
export const VIEW_NOTE = "Styles change the drawing only: counts, membership and selection stay.";
export const WORLD_VIEW = "World view";
export const NOT_PLOTTED_TITLE = "Not plotted";
export const NOT_PLOTTED_NOTE = "Counted in every period, without a safe map position.";
export const NOT_PLOTTED_MARK = "Not plotted";
export const NOT_PLOTTED_HINT = "This governed geography is available as an aggregate but has no safe map geometry.";
export const LEGEND: Readonly<Record<"aggregate" | "density" | "texture", string>> = Object.freeze({
  aggregate: "Ring size: records in the geography; the ring's form its count tier.",
  density: "One dot per record where the geometry has room; a ring carries the rest.",
  texture: "Pattern spacing: the record-count tier.",
});
export const LEGEND_TEMPORAL = "Three bars at each place: records in the previous, this and the next period.";
export const PROJECTION_NOTE = (version: string, scale: string) => `Equal Earth · Natural Earth ${version} ${scale}`;
export const LOADING_GEOMETRY = "Loading the governed geometry…";
export const GEOMETRY_FAILED = "The governed geometry could not be loaded.";
export const LOADING_PERIOD = (label: string) => `Loading the ${label}…`;
export const PERIOD_FAILED = "The selected period could not be loaded.";
export const EMPTY_PERIOD = "No public records overlap this period.";
export const RETRY = "Try again";
export const STATUS_PERIOD = (label: string) => `${label} on the map.`;
export const STATUS_SELECTED = (label: string) => `${label} selected.`;
export const STATUS_RESET = "World view.";
export const STATUS_VIEW = (label: string) => `${label} style.`;
export const STATUS_LAYER = (label: string) => `${label} layer.`;

/* 03 — Place profile */
export const PLACE_PROFILE = "Place profile";
export const PLACE_PROFILE_CLOSE = "Close place profile";
export const PLACE_PROFILE_OPEN = "Place profile";
export const PLACE_PROFILE_DISABLED = "Select a place to open Place profile";
export const LABEL_RECORDS = (n: number) => `${n.toLocaleString("en-US")} record${n === 1 ? "" : "s"}`;
export const RANK_OF = (rank: number, of: number) => `Rank #${rank} of ${of.toLocaleString("en-US")} recorded geographies`;
export const AROUND_PERIOD = "Around this period";
export const ROW_RECORDS = "Records";
export const ROW_SHARE = "Share";
export const ROW_RANK = "Rank";
export const UNAVAILABLE = "—";
export const STATE_WORDS: Readonly<Record<PublicSpacetimeMappingState, string>> = Object.freeze({
  mapped: "Mapped",
  aggregate_only: "Not plotted on the map",
  unmapped: "Not plotted on the map",
});
export const STATE_NOTES: Readonly<Partial<Record<PublicSpacetimeMappingState, string>>> = Object.freeze({
  aggregate_only: "Counted in this period; no governed geometry, so no position on the map.",
  unmapped: "Counted in this period; not placed on the map.",
});
export const CLASS_WORDS: Readonly<Record<PublicSpacetimeGeographyClass, string>> = Object.freeze({
  country: "Country",
  territory: "Territory",
  subnational: "Subnational",
  broad_region: "Broad region",
  transnational: "Transnational",
  historical: "Historical",
  unresolved: "Unresolved",
  other: "Other",
});
export const RECORDS_OF = (n: number, denominator: number, period: string) =>
  `${n.toLocaleString("en-US")} of ${denominator.toLocaleString("en-US")} records in the ${period}`;
export const TIME_PRECISION = "Time precision";
export const QUALIFICATION = "Qualification";
export const VIEW_RECORDS = "View matching records";
export const TECHNICAL = "Technical provenance";
export const RELEASE = "Release";
export const PROJECTION = "Projection";

/* 04 — matching records */
export const MATCHING = "Matching records";
export const MATCHING_COUNT = (n: number) => `${n.toLocaleString("en-US")} matching public record${n === 1 ? "" : "s"}`;
export const MATCHING_OF = (geography: string, period: string) => `${geography} · ${period}`;
export const LOAD_MORE = "Load more";
export const LOADING_RECORDS = "Loading matching records…";
export const RECORDS_FAILED = "The matching records could not be loaded.";
export const OPEN_RECORD = "Object page";

/* 05 — the place ranking */
export const RANKING_TITLE = "Place ranking";
export const RANKING_NOTE = "Every recorded geography of the period, by records; the same counts as the map.";
export const RANKING_OPEN = "Place ranking";
export const RANKING_CLOSE = "Close the place ranking";
export const RANKING_COLUMNS = Object.freeze({ place: "Place", records: "Records", share: "Share of period", rank: "Rank" });
export const DRAWER_CLOSE = "Close";

/* 08 — the shell */
export const FAILURE_TITLE = "Spacetime is unavailable";
export const FAILURE_NOTE = "No map geometry or record payload was sent. The governed projection failed its integrity checks.";
export const DOCK_TOOLS = "Spacetime tools";

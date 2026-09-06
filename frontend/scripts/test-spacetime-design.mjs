/* Spacetime (§7h) — the design contract, checked against the source and
   the guidance service: the desktop is presentation over the one
   orchestration; the copy speaks of records, never of activity; no
   gradient, no arrow, no relation line; System suggests only after a
   choice, two actions at most, its note bounded and deterministic in its
   numbers; the route's mobile boundary first. */

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const jiti = require("jiti")(fileURLToPath(import.meta.url), {
  interopDefault: true,
  alias: { "@": join(frontendRoot, "src"), "server-only": join(frontendRoot, "scripts/server-only-marker.mjs") },
});
const route = join(frontendRoot, "src/app/trace/spacetime");
const read = (path) => readFileSync(path, "utf8");
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

/* --- the desktop layer: presentation only --- */
const desktopDir = join(route, "desktop");
const desktopFiles = readdirSync(desktopDir).filter((name) => name.endsWith(".tsx"));
const desktopSource = desktopFiles.map((name) => read(join(desktopDir, name))).join("\n");
const desktopCss = readdirSync(desktopDir).filter((name) => name.endsWith(".css")).map((name) => read(join(desktopDir, name))).join("\n");
const content = read(join(route, "lib/content.ts"));
const page = read(join(route, "page.tsx"));
const workspace = read(join(frontendRoot, "src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx"));

check(desktopSource.includes("useSpacetimeWorkspace(periods, initialAtlas"), "the desktop reads the workspace's one orchestration");
check(!/\bfetch\(|readApi\(|SpacetimeRequestEpochGate|applySpacetimeRecordPage|\/api\/v1\/releases/u.test(desktopSource), "the desktop carries no second request orchestration");
check(!/spacetime\/gis\/(?:projection|geometry|dot-density|native-pattern|renderer|runtime-cache)"/u.test(desktopSource), "the desktop touches no GIS module directly");
check(workspace.includes("export function useSpacetimeWorkspace") && workspace.includes("export function MapGraphic"), "the workspace exports its orchestration and its map graphic");
check(page.indexOf("isLikelyMobileTraceRequest()") < page.indexOf("await Promise.all"), "the route's mobile boundary precedes the runtime imports");
check(!/export|Export PNG|Download|CSV/u.test(desktopSource.replace(/export (?:default |interface |const |type )/g, "")), "no export workflow this round");

/* --- what the map never says --- */
check(!/<line\b|<marker\b|marker-end|arrow|→/u.test(desktopSource), "no arrows, paths or relation lines in the desktop");
check(!/linear-gradient\((?!.*repeating)|radial-gradient\((?!circle, color-mix)/u.test(desktopCss.replace(/repeating-linear-gradient\([^)]*\)/g, "")), "no value gradient in the map's colours");
check(content.includes("not object coordinates") && desktopSource.includes("BOUNDARY"), "the boundary sentence stands on the page");
const forbidden = /\b(?:influence|diffusion|migration|spread|caus\w*|importance|activity|birthplace|nationality|travel|route)\b/iu;
check(!forbidden.test(content.replace(/\/\*[\s\S]*?\*\//g, "")), "the copy never speaks of activity, influence, diffusion, migration, causation or importance");
for (const word of ["records", "archive", "recorded", "selected period", "aggregate"]) check(content.toLowerCase().includes(word), `the copy speaks of ${word}`);

/* --- the states, told apart --- */
for (const state of ["mapped", "aggregate_only", "unmapped"]) check(content.includes(`${state}:`), `the ${state} state has its word`);
check(desktopCss.includes(".unplotted::before") && content.includes("has no safe map geometry") && content.includes('aggregate_only: "Not plotted on the map"'), "a place without a safe map position carries the not-plotted mark, its reason on hover");
check(/selectGeography\(row\.geographyId\)|onSelect\(row\.geographyId\)/u.test(desktopSource) && !/centroid|geocode/iu.test(desktopSource), "a table row selects its geography; nothing is geocoded");

/* --- Place context and its guidance --- */
const placeContext = read(join(desktopDir, "PlaceProfile.tsx"));
const desktop = read(join(desktopDir, "SpacetimeDesktop.tsx"));
check(!/\bInspector\b/u.test(desktopSource) && content.includes('PLACE_PROFILE = "Place profile"'), "the right column is PLACE PROFILE, not an inspector");
check(placeContext.includes('surface="TRACE_SPACETIME"') && placeContext.includes("maxActions={2}") && placeContext.includes('variant="block"'), "System suggests sits inside Place profile, two actions at most");
check(/guidanceReady \? \(\s*<SystemSuggestionsPanel/u.test(placeContext), "System suggests renders only when the guidance is ready");
check(/const guidanceReady = Boolean\(selectedGeography\) && atlasState === "ready"/u.test(desktop), "guidance needs a selected geography and a ready atlas");
check(!/<SystemSuggestionsPanel/u.test(desktop) && !/<SystemSuggestionsPanel/u.test(read(join(desktopDir, "MapFrame.tsx"))), "no guidance panel outside Place profile");

/* --- the period rail --- */
const periodRail = read(join(desktopDir, "PeriodRail.tsx"));
check(periodRail.includes('role="radiogroup"') && periodRail.includes("ArrowRight") && periodRail.includes("Math.sqrt(count / most)"), "the period rail: one choice, arrow keys, a square-root column");
check(!/transition:\s*height|animation/u.test(read(join(desktopDir, "PeriodRail.module.css"))), "no animation through history");
check(content.includes("in the current archive release") && content.includes("counts in every period it overlaps"), "the columns are named for what they are; the overlap rule stays");
check(/start % 50 === 0 \? String\(start\) : `\$\{String\(start\)\.slice\(2\)\}s`/u.test(periodRail), "full years at the fifties, short decades between");
check(periodRail.includes('layer === "temporal" && role') && content.includes('previous: "Previous", current: "Current", next: "Next"'), "the rail names the temporal window");
/* the year series: public records by recorded year, counted from the frozen status dataset, the cohort's total */
const { publicRecordsByYear, YEAR_FIRST, YEAR_LAST } = await jiti.import(join(route, "lib/years.server.ts"));
const spacetimeManifest = JSON.parse(readFileSync(join(frontendRoot, "generated/trace-spacetime-v1/manifest.json"), "utf8"));
const years = publicRecordsByYear(spacetimeManifest.counts.publicObjects);
check(years.length === YEAR_LAST - YEAR_FIRST + 1 && years[0].year === 1800 && years[years.length - 1].year === 2026, "one column a year, 1800 to 2026");
check(years.reduce((sum, entry) => sum + entry.count, 0) === spacetimeManifest.counts.publicObjects, "the columns sum to the public cohort");
check(!/\[\[1800,/u.test(desktopSource + content), "no year series typed into the view");

/* the cartography: the coast under-layer, the dot screens, interaction-led labels, one drawer */
const mapFrame = read(join(desktopDir, "MapFrame.tsx"));
const mapCss = read(join(desktopDir, "MapFrame.module.css"));
check(mapFrame.includes('data-layer="coast"') && mapCss.includes("stroke-width: 1.1") && mapCss.includes("stroke-width: 0.5"), "the coast under-layer over hairline boundaries");
check(/\.stage\[data-mode="aggregate"\] \.aggregateMark,[\s\S]*display: none;/u.test(mapCss) && /\.ringOuter,\s*\.ringInner \{[^}]*fill: color-mix\(in srgb, var\(--sp-blue\) 10%/u.test(mapCss), "the distribution is drawn as rings; the solid disc never shows");
check(mapFrame.includes("sealedRadius(mark.geography.recordCount)") && mapFrame.includes("Math.max(4, Math.min(18, 3 + Math.sqrt(count) * 0.75))"), "ring radius is the sealed count policy");
check(mapFrame.includes("TRACE_NATIVE_COUNT_TIERS") && mapFrame.includes("FULL_GLYPH_TIER = 2"), "the level of detail follows the sealed count tiers");
check(mapFrame.includes('layer === "temporal"') && /\[series\.previous, series\.current, series\.next\]/u.test(mapFrame) && mapFrame.includes('data-role={index === 1 ? "current" : "neighbour"}'), "the temporal glyph: previous · current · next bars, the current one set apart");
check(!/growth|decline|trend|arrow|marker-end/iu.test(mapFrame + mapCss) && !/green/iu.test(mapCss), "no growth or decline semantics, no arrows");
check(mapFrame.includes("NOT_PLOTTED_TITLE") && mapFrame.includes("notPlotted.map"), "not-plotted places stand in a companion list with the same window");
check(mapFrame.includes("focused && selectedDensity") && mapFrame.includes("selectedDensity.dots.map"), "the focused place shows its sealed dot field");
check(/const wanted = \[selectedGeographyId, hoverId\]/u.test(mapFrame), "labels only for the selected and the hovered geography");
check(!/<text/u.test(mapFrame), "no label on every country");
check(desktop.includes('drawer === "records"') && desktop.includes("<Drawer") && !/<MatchingRecords[\s\S]*<GeographyTable[\s\S]*<\/div>\s*\) : null\}\s*<\/div>/u.test(desktop.replace(/\) : \(\s*<GeographyTable/u, "")), "one drawer under the map, the records or the table");
check(desktop.includes("PLACE_PROFILE_DISABLED") && content.includes("Select a place to open Place profile"), "the disabled control says why");
const railCss = read(join(desktopDir, "SpacetimeRail.module.css"));
check(/\.stack \{\s*display: grid;/u.test(railCss) && !/\.stack \{[^}]*grid-template-columns: repeat/u.test(railCss), "the layer control is a stack");
const railSource = read(join(desktopDir, "SpacetimeRail.tsx"));
check(!railSource.includes("VIEWS.find((view) => view.id === mode)?.brief} {VIEW_NOTE}") && railSource.includes("VIEW_HELP"), "the styles' meanings sit behind a fold, not under the control");
/* the product: layer as the research control, style secondary; no FIT; WORLD VIEW only with a selection or a focus */
check(railSource.includes("LAYER_LABEL") && railSource.indexOf("LAYER_LABEL") < railSource.indexOf("STYLE_LABEL"), "MAP LAYER comes before MAP STYLE in the rail");
check(content.includes('id: "distribution"') && content.includes('id: "temporal"'), "the two layers: Distribution and Temporal");
check(!/\bFIT\b|"Fit"/u.test(content + desktopSource), "no Fit control");
check(/\{focused \|\| selectedGeographyId \? \(\s*<button type="button" onClick=\{onWorldView\}>\{WORLD_VIEW\}/u.test(mapFrame), "WORLD VIEW appears only with a selection or a focus");
check(!/reset map/iu.test(content), "nothing is called Reset map");
/* the period profile */
for (const word of ["TOP_CONCENTRATION", "GEOGRAPHIES", "SHARE_OF_PERIOD", "PREVIOUS_PERIOD"]) check(content.includes(word), `the period profile speaks of ${word}`);
check(content.includes("of public archive records in this period") && !/design activity/u.test(content), "share is of public archive records, never of activity");
/* the place profile: records · share · rank around the period */
check(placeContext.includes("RANK_OF") && placeContext.includes("ROW_SHARE") && placeContext.includes("ROW_RANK") && placeContext.includes("series?.previous") && placeContext.includes("series?.next"), "the place profile shows records, share and rank across the window");
/* the ranking: place · records · share · rank; the state is not a column */
const ranking = read(join(desktopDir, "PlaceRanking.tsx"));
check(ranking.includes("RANKING_COLUMNS.share") && ranking.includes("RANKING_COLUMNS.rank") && !/STATE_WORDS/u.test(ranking) && ranking.includes("NOT_PLOTTED_MARK"), "the ranking carries share and rank; not-plotted is a light mark, not a column");

/* the temporal window, on three real governed atlases: the United
   States in the 1970s · 1980s · 1990s — records, share and rank as the
   frozen aggregates state them; edges have no neighbour; ranks agree with
   the ranking; the desktop fetches nothing itself */
{
  const { deriveSpacetimeTemporalWindow, rankSpacetimeRows, deriveSpacetimePeriodProfile } = await jiti.import(join(frontendRoot, "src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx"));
  const reader = await jiti.import(join(frontendRoot, "src/features/trace-v49/spacetime/governed/reader.server.ts"));
  const periods = reader.getGovernedSpacetimePeriodsDataset();
  const atlasOf = (id) => { const result = reader.lookupGovernedSpacetimeAtlas(id); assert.ok(result.ok, id); return result.data; };
  const a70 = atlasOf("SPT-PERIOD-1970-1980"), a80 = atlasOf("SPT-PERIOD-1980-1990"), a90 = atlasOf("SPT-PERIOD-1990-2000");
  const window80 = deriveSpacetimeTemporalWindow(a70, a80, a90);
  const us = [...window80.values()].find((series) => series.label === "United States");
  check(Boolean(us) && us.current.records === 49 && us.current.rank === 3 && Math.abs(us.current.share - 49 / 1898) < 1e-9, "United States in the 1980s: 49 records, rank 3, share 49/1,898");
  check(us.previous.records === 226 && us.previous.rank === 1 && us.next.records === 129 && us.next.rank === 2, "United States around the 1980s: 226 (rank 1) before, 129 (rank 2) after");
  const uk = [...window80.values()].find((series) => series.label === "United Kingdom");
  check(uk.current.rank === 1 && uk.current.records === 1630 && Math.abs(uk.current.share - 1630 / 1898) < 1e-9, "the 1980s concentrate in the United Kingdom: 1,630 of 1,898, rank 1");
  const ranking80 = rankSpacetimeRows(a80);
  check(ranking80[0].row.label === "United Kingdom" && ranking80[2].row.label === "United States" && ranking80.every((entry, index) => entry.rank === index + 1), "the ranking orders by records, rank 1 first");
  const profile80 = deriveSpacetimePeriodProfile(a80, periods);
  check(profile80.records === 1898 && profile80.geographies === 22 && profile80.top.label === "United Kingdom" && profile80.previous.label === "1970s" && profile80.next.label === "1990s", "the period profile: 1,898 records, 22 geographies, the top concentration, the neighbours");
  const first = atlasOf(periods.periods[0].periodId);
  const edge = deriveSpacetimeTemporalWindow(null, first, atlasOf(periods.periods[1].periodId));
  check([...edge.values()].every((series) => series.previous === null && series.next !== null), "the first period has no previous; the window never wraps");
  const notPlotted = [...window80.values()].filter((series) => series.mappingState !== "mapped");
  check(notPlotted.length >= 1 && notPlotted.every((series) => series.current !== null), "not-plotted places keep their temporal window");
  check(/adjacentControllerRef|setAdjacent/u.test(workspace) && !/setAdjacent|readApi/u.test(desktopSource), "the adjacent atlases are the hook's, never fetched by the desktop");
}

/* --- the guidance service: the Spacetime gate --- */
const { createSystemSuggestions } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/service.server.ts"));
const { spacetimeFallbackNote, SPACETIME_GUIDANCE_MAX_WORDS } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/providers.server.ts"));
const context = {
  stateType: "SPACETIME_DISTRIBUTION_AGGREGATE_VIEW",
  labels: ["1960s", "Germany", "mapped", "country", "1950s", "1970s", "share larger than in the previous period"],
  counts: { publicDenominator: 1397, selectedRecords: 342, selectedRank: 3, geographyCount: 55, previousPeriodRecords: 383, previousSelectedRecords: 40, nextPeriodRecords: 1096, nextSelectedRecords: 118 },
  validActionIds: ["SELECT_GEOGRAPHY", "COMPARE_PUBLIC_COUNTS", "RESET_VIEW"],
  evidenceClass: "PUBLIC_AGGREGATE",
};
const request = (ctx = context) => ({ schemaVersion: "gda-system-suggestions-request/v1", surface: "TRACE_SPACETIME", stateHash: "a".repeat(16), context: ctx });
const environment = { SYSTEM_SUGGESTIONS_PROVIDER: "deepseek", DEEPSEEK_API_KEY: "test-key" };
const providerWith = (note, ids) => async () => new Response(JSON.stringify({ output_text: JSON.stringify({ note, suggestion_ids: ids }) }), { status: 200, headers: { "Content-Type": "application/json" } });
const ids = (response) => response.suggestions.map((s) => s.id);
const good = await createSystemSuggestions(request(), { environment, fetchImpl: providerWith("Germany accounts for 342 of 1,397 public records in the 1960s, ranking third among 55 recorded geographies. Its share of the public archive is larger here than in the 1950s.", ["trace-trace-spacetime-select-geography"]) });
check(good.sourceClass === "MODEL" && good.providerStatus === "MODEL_OK" && good.suggestions.length === 1, "a bounded, deterministic note passes");
const fallbackFor = async (note, actionIds = []) => createSystemSuggestions(request(), { environment, fetchImpl: providerWith(note, actionIds) });
for (const [label, note, actionIds] of [
  ["a causal claim", "Germany accounts for 342 of 1,397 public records in the 1960s. This reflects postwar economic growth.", []],
  ["an influence claim", "Modernism spread from Switzerland to Germany.", []],
  ["a design-activity claim", "German design activity expanded in the 1960s.", []],
  ["a number not supplied", "Germany accounts for 512 of 1,397 public records in the 1960s.", []],
  ["a percentage", "The archive contains 24% more records than in the 1950s.", []],
  ["four sentences", "One. Two. Three. Four.", []],
  ["three actions", "Germany accounts for 342 of 1,397 public records in the 1960s.", ["trace-trace-spacetime-select-geography", "trace-trace-spacetime-compare-public-counts", "trace-trace-spacetime-reset-view"]],
  ["too many words", Array.from({ length: SPACETIME_GUIDANCE_MAX_WORDS + 5 }, () => "records").join(" ") + ".", []],
]) {
  const response = await fallbackFor(note, actionIds);
  check(response.sourceClass === "STATIC_FALLBACK" && response.providerStatus === "INVALID_RESPONSE", `${label} falls back to the deterministic note`);
  check(response.suggestions.length <= 2, `${label}: the fallback shows two actions at most`);
}
const fallback = await createSystemSuggestions(request(), { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } });
check(fallback.note === "Germany accounts for 342 of 1,397 public records in the 1960s, ranking third among 55 recorded geographies. Its share of the public archive is larger here than in the 1950s.", "the fallback states the counts, the rank and the place's own share against the previous period");
check(fallback.suggestions.length <= 2 && ids(fallback).every((id) => id.startsWith("trace-trace-spacetime-")), "the fallback offers two approved actions at most");
check(spacetimeFallbackNote({ labels: ["1980s"], counts: { publicDenominator: 1898 } }).startsWith("The 1980s carry 1,898 public records"), "without a place the fallback names the period's total");
check(spacetimeFallbackNote({ labels: ["1980s", "United States", "mapped", "country", "1970s", "1990s"], counts: { publicDenominator: 1898, selectedRecords: 49, selectedRank: 3, geographyCount: 22, previousPeriodRecords: 1096, previousSelectedRecords: 226, nextPeriodRecords: 441, nextSelectedRecords: 129 } }) === "United States accounts for 49 of 1,898 public records in the 1980s, ranking third among 22 recorded geographies. Its share of the public archive is smaller here than in the 1970s.", "the fallback voices a smaller share as smaller");
const other = await createSystemSuggestions({ ...request(), surface: "TRACE_CONTEXT", context: { stateType: "CONTEXT", labels: ["x"], counts: {}, validActionIds: ["EXPAND_MEDIUM"], evidenceClass: "PUBLIC_CONTEXT" } }, { environment, fetchImpl: providerWith("Review the medium. Then the theme.", ["trace-trace-context-expand-medium"]) });
check(other.sourceClass === "MODEL" && other.suggestions.length === 1, "the other surfaces keep the shared gate");

console.log(`SPACETIME_DESIGN=PASS CHECKS=${checks} DESKTOP_FILES=${desktopFiles.length}`);

import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { feature } from "topojson-client";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const require = createRequire(import.meta.url);

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

function decodeCompact(payload) {
  return payload.items.map((values) => Object.fromEntries(
    payload.schema.map((field, index) => {
      const dictionary = payload.dictionaries[field];
      return [field, dictionary ? dictionary[Number(values[index])] : values[index]];
    }),
  ));
}

const aliases = {
  "United States": ["United States of America"],
  "Aotearoa New Zealand": ["New Zealand"],
  "Australia / Indigenous": ["Australia"],
  "Bosnia and Herzegovina": ["Bosnia and Herz."],
  "Cape Verde": ["Cabo Verde"],
  "China / Hong Kong": ["China"],
  "Cook Islands": ["Cook Is."],
  "Cuba / transnational": ["Cuba"],
  "Czech Republic": ["Czechia"],
  "Democratic Republic of the Congo": ["Dem. Rep. Congo"],
  "Dominican Republic": ["Dominican Rep."],
  "Federated States of Micronesia": ["Micronesia"],
  "Hawaii": ["United States of America"],
  "Israel / Palestine": ["Israel", "Palestine"],
  "Korean Peninsula": ["North Korea", "South Korea"],
  "Marshall Islands": ["Marshall Is."],
  "Mexico City": ["Mexico"],
  "North Macedonia": ["Macedonia"],
  "Palestine / transnational": ["Palestine"],
  "Republic of the Congo": ["Congo"],
  "Solomon Islands": ["Solomon Is."],
  "Wallis and Futuna": ["Wallis and Futuna Is."],
  "Global / transnational": [],
  "Latin America": [],
  "Manchukuo": [],
  "Tokelau": [],
  "Yugoslavia": [],
};

const atlas = await readJson(join(root, "public/data/trace-v48/atlas.json"));
const catalogPayload = await readJson(join(root, "public", atlas.assets.catalog));
const catalog = decodeCompact(catalogPayload);
const archiveSearch = await readJson(join(root, "public/data/archive-search-v1.json"));
const worldPath = require.resolve("world-atlas/countries-50m.json");
const topology = await readJson(worldPath);
const countries = feature(topology, topology.objects.countries);
const countryNames = new Set(countries.features.map((country) => country.properties?.name).filter(Boolean));

function resolve(region) {
  if (Object.hasOwn(aliases, region)) return aliases[region];
  if (countryNames.has(region)) return [region];
  const suffix = region.split(",").at(-1)?.trim();
  if (suffix && suffix !== region) {
    const names = aliases[suffix] ?? [suffix];
    if (names.every((name) => countryNames.has(name))) return names;
  }
  return [];
}

const regionCounts = new Map();
for (const item of catalog) regionCounts.set(item.region, (regionCounts.get(item.region) ?? 0) + 1);
const unmapped = [...regionCounts]
  .filter(([region]) => resolve(region).length === 0)
  .map(([region, count]) => ({ region, count }))
  .sort((left, right) => right.count - left.count || left.region.localeCompare(right.region));
const unmappedObjects = unmapped.reduce((sum, entry) => sum + entry.count, 0);

const taxonomyText = await readFile(join(root, "src/components/archive/trace/trace-taxonomy.ts"), "utf8");
const primitivesText = await readFile(join(root, "src/components/archive/primitives.tsx"), "utf8");
const shellSearchText = await readFile(join(root, "src/components/archive/shell/search.tsx"), "utf8");
const evolutionFieldText = await readFile(join(root, "src/components/archive/trace/ChronogeographicRoutes.tsx"), "utf8");
const constellationText = await readFile(join(root, "src/components/archive/trace/TraceConstellation.tsx"), "utf8");
const definitions = [...taxonomyText.matchAll(
  /id:\s*"([^"]+)"[\s\S]*?family:\s*"([^"]+)"\s*,\s*count:\s*(\d+)\s*,\s*status:/g,
)].map((match) => ({ id: match[1], family: match[2], count: Number(match[3]) }));
const atlasRelations = new Map(atlas.relationTypes.map((relation) => [relation.label, relation]));
const taxonomyMismatches = definitions.flatMap((definition) => {
  if (definition.id === "influenced_by") {
    return definition.count === atlas.counts.influenceEdges ? [] : [{ ...definition, atlas: atlas.counts.influenceEdges }];
  }
  const relation = atlasRelations.get(definition.id);
  return relation && relation.count === definition.count && relation.family === definition.family
    ? []
    : [{ ...definition, atlas: relation ?? null }];
});

const checks = {
  active_catalog_count: catalog.length === atlas.counts.activeObjects,
  unresolved_region_active: !catalog.some((item) => item.region === "Unresolved region"),
  influence_edges_zero: atlas.counts.influenceEdges === 0,
  taxonomy_covers_atlas_relations: atlas.relationTypes.every((relation) => definitions.some((definition) => definition.id === relation.label)),
  taxonomy_counts_match_atlas: taxonomyMismatches.length === 0,
  real_map_geometry_present: countries.features.length >= 200,
  archive_search_index_is_consistent:
    archiveSearch.version === "archive-search-v1"
    && archiveSearch.count === archiveSearch.items.length
    && archiveSearch.items.every((item) => item.length === archiveSearch.schema.length),
  archive_search_surface_ids_are_unique:
    new Set(archiveSearch.items.map((item) => item[0])).size === archiveSearch.items.length,
  trace_shell_avoids_large_archive_mock:
    !primitivesText.includes("@/lib/archive-data")
    && !shellSearchText.includes("@/lib/archive-data")
    && !shellSearchText.includes("public_surface_mock_v0"),
  evolution_field_uses_frozen_aggregates:
    evolutionFieldText.includes("atlas.regionMatrix")
    && evolutionFieldText.includes("atlas.decadeTotals")
    && evolutionFieldText.includes("atlas.relationTypes")
    && evolutionFieldText.includes("atlas.assets.catalog"),
  evolution_field_keeps_inference_boundary:
    evolutionFieldText.includes("does not claim geographic diffusion")
    && evolutionFieldText.includes("does not encode an inferred causal route"),
  evolution_field_mobile_scroll_binding:
    evolutionFieldText.includes("IntersectionObserver")
    && evolutionFieldText.includes("data-evolution-decade"),
  evolution_field_preserves_object_drilldown:
    evolutionFieldText.includes("exploreCell(row, cell.decade)"),
  constellation_uses_frozen_tree_and_relation_counts:
    constellationText.includes("atlas.treeCounts")
    && constellationText.includes("atlas.relationTypes")
    && constellationText.includes("atlas.counts.activeObjects"),
  constellation_geometry_is_deterministic:
    constellationText.includes("const rings = [")
    && constellationText.includes("polarPoint")
    && constellationText.includes("arcPath")
    && !constellationText.includes("Math.random"),
  constellation_keeps_inference_boundary:
    constellationText.includes("It does not encode influence")
    && constellationText.includes("not historical influence claims"),
  constellation_has_keyboard_and_text_fallback:
    constellationText.includes('role="button"')
    && constellationText.includes("onKeyDown")
    && constellationText.includes("Exact tree and relation ledger"),
};

console.log(JSON.stringify({
  version: atlas.version,
  checks,
  counts: {
    activeObjects: catalog.length,
    normalizedTraceTypes: definitions.length,
    observedRelationTypes: atlas.relationTypes.length,
    countryFeatures: countries.features.length,
    catalogRegionLabels: regionCounts.size,
    mappedObjects: catalog.length - unmappedObjects,
    unmappedObjects,
    unmappedRegionLabels: unmapped,
    archiveSearchSurfaces: archiveSearch.items.length,
  },
  taxonomyMismatches,
}, null, 2));

if (Object.values(checks).some((passed) => !passed)) process.exitCode = 1;

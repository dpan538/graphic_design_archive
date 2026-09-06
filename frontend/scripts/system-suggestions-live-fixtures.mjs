export async function liveCases(jiti, frontendRoot, join) {
const search = await jiti.import(join(frontendRoot, "src/features/search-v2/service.server.ts"));
const searchIndex = await jiti.import(join(frontendRoot, "src/features/search-v2/index.server.ts"));
const governed = await jiti.import(join(frontendRoot, "src/features/trace-v49/context/governed/index.server.ts"));
const exploration = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/service.server.ts"));
const inquiries = await jiti.import(join(frontendRoot, "src/features/trace-v49/open-inquiry-v1/service.server.ts"));

/* ---- the fixed, public-safe cases: five per surface ---- */
const facets = search.publicSearchFacets();
const firstDocument = searchIndex.getPublicSearchIndex().documents[0];
const searchCases = [
  ["search-zero", { query: "zzqx-no-match", filters: {} }],
  ["search-single", { query: firstDocument.stableId, filters: {} }],
  ["search-multi", { query: "poster", filters: {} }],
  ["search-filters", { query: "poster", filters: { yearFrom: 1960, yearTo: 1969, objectType: facets.objectTypes[0].value } }],
  ["search-theme", { query: "", filters: { theme: facets.themes[0].value } }],
].map(([id, reference]) => ({ id, surface: "SEARCH_RESULTS", reference }));
const examples = governed.getGovernedContextExampleOptions();
const contextCases = examples.slice(0, 5).map((option, index) => {
  const dataset = governed.lookupGovernedContextDataset(option.stableId).data;
  const termIds = dataset.representations.map((item) => item.termId);
  const onCanvas = index % 2 === 0 ? termIds : termIds.slice(0, Math.max(0, termIds.length - 1));
  return { id: `context-${option.role}`, surface: "TRACE_CONTEXT", reference: { objectId: option.stableId, onCanvas } };
});
const points = exploration.listExplorationStartingPoints().data.starting_points;
const ladder = (label, steps) => { let view = exploration.createExplorationView({ vocabulary_id: points.find((point) => point.label === label).vocabulary_id }).data; for (let i = 0; i < steps; i += 1) { const next = exploration.applyExplorationViewAction(view.restore.map_id, { action: "MORE", expected_state_hash: view.restore.state_hash, template_id: view.restore.template_id, variant_id: view.restore.variant_id }); if (!next.ok) break; view = next.data; } return view; };
const explorationCases = [
  ["exploration-s2", ladder("design diplomacy", 0)],
  ["exploration-s3", ladder("design diplomacy", 1)],
  ["exploration-s4", ladder("design diplomacy", 2)],
  ["exploration-production", ladder("production", 1)],
  ["exploration-rejection", ladder("rejection", 0)],
].map(([id, view]) => ({ id, surface: "TRACE_VALIDATED_EXPLORATION", reference: { mapId: view.restore.map_id, stateId: view.restore.state_id } }));
const inquiryCases = inquiries.listOpenInquiries().data.data.items.slice(0, 5).map((item, index) => ({ id: `inquiry-${index + 1}`, surface: "TRACE_OPEN_INQUIRY", reference: { inquiryId: item.inquiry_id } }));
return [...searchCases, ...contextCases, ...explorationCases, ...inquiryCases];

}

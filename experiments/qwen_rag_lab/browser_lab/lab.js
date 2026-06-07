const fixtureUrl = "../fixtures/archive_fixture_v0.json";
const queriesUrl = "../fixtures/benchmark_queries_v0.json";

const STOP = new Set("a an and are as at be by can did do does for from has have here how i if in is it me of on or should the this to using was what when where who why with without".split(" "));

const elements = {
  querySelect: document.querySelector("#querySelect"),
  topK: document.querySelector("#topK"),
  noteMode: document.querySelector("#noteMode"),
  includeTopology: document.querySelector("#includeTopology"),
  includeSourceRights: document.querySelector("#includeSourceRights"),
  runButton: document.querySelector("#runButton"),
  packetOutput: document.querySelector("#packetOutput"),
  runLog: document.querySelector("#runLog"),
  metricRetrieval: document.querySelector("#metricRetrieval"),
  metricCandidates: document.querySelector("#metricCandidates"),
  metricBytes: document.querySelector("#metricBytes"),
  metricTokens: document.querySelector("#metricTokens"),
  metricWebgpu: document.querySelector("#metricWebgpu")
};

let fixture;
let queries;

function terms(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .split(/\s+/)
    .filter((term) => term.length > 2 && !STOP.has(term));
}

function haystack(record) {
  return [
    record.surfaceId,
    record.sourceRecordId,
    record.title,
    record.creator,
    record.dateText,
    record.region,
    record.objectType,
    record.medium,
    record.source.name,
    record.rights.state,
    record.rights.label,
    record.imageState.code,
    record.topology.folderTitles.join(" "),
    Object.values(record.text).join(" ")
  ].join(" ").toLowerCase();
}

function route(query) {
  const routes = {
    archive_orientation: ["assistant", 3, "Orient the user to archive scope and evidence limits."],
    casual_archive_help: ["assistant", 2, "Give navigational help without making historical claims."],
    current_object_explanation: ["assistant", 4, "Explain the current object and name source/rights limits."],
    first_earliest_claim: ["assistant", 6, "Handle chronology cautiously and refuse unsupported first/earliest claims."],
    region_period_recommendation: ["assistant", 5, "Suggest a route, not a canon or ranking."],
    source_rights_question: ["assistant", 3, "Answer from source and rights fields only."],
    comparison: ["assistant", 6, "Compare only retrieved objects and visible source support."],
    method_process_question: ["research", 4, "Explain the archive method and evidence boundary."],
    more_context: ["research", 6, "Give a bounded next-reading route from current topology."],
    no_evidence_refusal: ["assistant", 0, "Refuse before generation when evidence is missing."]
  };
  const [lane, maxCandidates, directive] = routes[query.queryType] || ["assistant", 3, "Answer from retrieved evidence."];
  return { lane, maxCandidates, directive };
}

function retrieve(query, topK) {
  if (query.queryType === "no_evidence_refusal") return [];
  const queryTerms = terms(query.question);
  const exact = query.surfaceContext ? fixture.records.find((record) => record.surfaceId === query.surfaceContext) : null;
  const ranked = fixture.records
    .map((record) => {
      const text = haystack(record);
      let score = 0;
      for (const term of queryTerms) {
        if (text.includes(term)) score += 1;
        if (record.title.toLowerCase().includes(term)) score += 2;
      }
      if (query.surfaceContext && record.surfaceId === query.surfaceContext) score += 100;
      if (query.queryType === "source_rights_question" && record.rights.label) score += 4;
      if (query.queryType === "region_period_recommendation" && record.region) score += 2;
      return { record, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || (a.record.dateStart || 9999) - (b.record.dateStart || 9999))
    .map((item) => item.record);
  if (exact && !ranked.some((record) => record.surfaceId === exact.surfaceId)) ranked.unshift(exact);
  return ranked.slice(0, topK);
}

function evidenceRecord(record, options) {
  const note = options.noteMode === "raw"
    ? record.text.descriptionSummary
    : [record.text.sourceDescription, record.text.sourceNotes, record.text.uncertaintyNote].filter(Boolean).join(" ");
  const packetRecord = {
    id: record.surfaceId,
    title: record.title,
    date: record.dateText,
    region: record.region,
    imageState: record.imageState,
    note
  };
  if (options.includeSourceRights) {
    packetRecord.source = record.source;
    packetRecord.rights = record.rights;
  }
  if (options.includeTopology) packetRecord.topology = record.topology;
  return packetRecord;
}

function estimateTokens(text) {
  return Math.ceil(String(text).length / 4);
}

function runSelected() {
  const query = queries.find((item) => item.queryId === elements.querySelect.value);
  const plan = route(query);
  const topK = Math.min(Number(elements.topK.value), plan.maxCandidates);
  const options = {
    noteMode: elements.noteMode.value,
    includeTopology: elements.includeTopology.checked,
    includeSourceRights: elements.includeSourceRights.checked
  };
  const t0 = performance.now();
  const candidates = retrieve(query, topK);
  const t1 = performance.now();
  const packet = {
    queryId: query.queryId,
    queryType: query.queryType,
    lane: plan.lane,
    answerDirective: plan.directive,
    evidencePolicy: "Research output only; AI text is not archive evidence.",
    qwenSlot: "not_run_no_model_download",
    candidates: candidates.map((record) => evidenceRecord(record, options))
  };
  const serialized = JSON.stringify(packet, null, 2);
  elements.packetOutput.textContent = serialized;
  elements.metricRetrieval.textContent = `${(t1 - t0).toFixed(3)} ms`;
  elements.metricCandidates.textContent = String(candidates.length);
  elements.metricBytes.textContent = String(new Blob([serialized]).size);
  elements.metricTokens.textContent = String(estimateTokens(serialized));
  elements.metricWebgpu.textContent = "not run";
  elements.runLog.textContent = JSON.stringify({
    timestamp: new Date().toISOString(),
    query: query.question,
    generationStatus: "not_run_no_model_download",
    runtimeComparison: "research-only; product path unchanged"
  }, null, 2);
}

async function init() {
  const [fixtureResponse, queriesResponse] = await Promise.all([fetch(fixtureUrl), fetch(queriesUrl)]);
  fixture = await fixtureResponse.json();
  queries = (await queriesResponse.json()).queries;
  for (const query of queries) {
    const option = document.createElement("option");
    option.value = query.queryId;
    option.textContent = `${query.queryId} - ${query.queryType}: ${query.question}`;
    elements.querySelect.append(option);
  }
  elements.runButton.addEventListener("click", runSelected);
  runSelected();
}

init().catch((error) => {
  elements.runLog.textContent = String(error?.stack || error);
});

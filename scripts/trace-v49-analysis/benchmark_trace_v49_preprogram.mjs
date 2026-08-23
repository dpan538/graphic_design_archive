import { performance } from "node:perf_hooks";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = join(here, "..", "..");
const frontendRoot = join(repositoryRoot, "frontend");
const featureRoot = join(frontendRoot, "src/features/trace-v49");
const createJiti = createRequire(join(frontendRoot, "package.json"))("jiti");
const jiti = createJiti(import.meta.url, { alias: { "@": join(frontendRoot, "src") } });
const trace = await jiti.import(join(featureRoot, "index.ts"));
const fixture = await jiti.import(join(featureRoot, "fixtures/public-synthetic.ts"));

const tiers = Object.freeze([
  { name: "minimal", controlledAssignments: 2, curatedMemberships: 3, places: 1, times: 1, sourceAssociations: 1 },
  { name: "median", controlledAssignments: 2, curatedMemberships: 3, places: 1, times: 1, sourceAssociations: 1 },
  { name: "p95", controlledAssignments: 2, curatedMemberships: 3, places: 1, times: 1, sourceAssociations: 1 },
  { name: "p99", controlledAssignments: 3, curatedMemberships: 4, places: 1, times: 1, sourceAssociations: 1 },
  { name: "maximum", controlledAssignments: 4, curatedMemberships: 5, places: 1, times: 1, sourceAssociations: 1 },
]);

const results = [];
for (const tier of tiers) {
  const inputs = buildInputs(tier);
  for (const [domain, derive, accessible, input] of [
    ["context", trace.deriveContextTraceDataset, trace.toContextAccessibleRows, inputs.context],
    ["spacetime", trace.deriveSpacetimeTraceDataset, trace.toSpacetimeAccessibleRows, inputs.spacetime],
    ["sources", trace.deriveSourcesTraceDataset, trace.toSourcesAccessibleRows, inputs.sources],
  ]) {
    const dataset = derive(input);
    const projection = benchmark(() => derive(input));
    const accessibleRows = benchmark(() => accessible(dataset));
    const serializedBytes = Buffer.byteLength(JSON.stringify(dataset));
    const retainedHeapDeltaBytesFor250Outputs = retainedHeapDelta(() => derive(input), 250);
    results.push({
      workload: tier.name,
      domain,
      measured_input_counts: {
        controlled_assignments: tier.controlledAssignments,
        curated_memberships: tier.curatedMemberships,
        places: tier.places,
        times: tier.times,
        source_associations: tier.sourceAssociations,
        accepted_semantic_edges: 0,
      },
      output_counts: {
        items: dataset.counts.itemCount,
        non_semantic_associations: dataset.counts.nonSemanticAssociationCount,
        semantic_edges: dataset.counts.semanticEdgeCount,
        accessible_rows: dataset.accessibleRows.length,
      },
      projection_ms: projection,
      accessible_rows_ms: accessibleRows,
      serialized_output_bytes: serializedBytes,
      retained_heap_delta_bytes_for_250_outputs: retainedHeapDeltaBytesFor250Outputs,
    });
  }
}

const maxProjectionP95 = Math.max(...results.map((item) => item.projection_ms.p95));
const receipt = {
  benchmark_version: "trace-v49-preprogram-benchmark-v1",
  runtime: process.version,
  platform: `${process.platform}-${process.arch}`,
  source_sha: "f9bdfdd293023592ddc6af92858a24857c5a532a",
  release_id: fixture.TRACE_V49_FIXTURE_RELEASE.releaseId,
  release_manifest_sha256: fixture.TRACE_V49_FIXTURE_RELEASE.manifestSha256,
  fixture_classification: "public-safe synthetic structures sized from measured v49 public-object density; no held rows",
  iterations_per_timing: 2000,
  warmup_iterations: 200,
  provisional_projection_p95_target_ms: 20,
  maximum_observed_projection_p95_ms: round(maxProjectionP95),
  target_met: maxProjectionP95 < 20,
  memory_measurement_note: "Retained heap delta after 250 simultaneously retained outputs; null means GC/runtime noise made the delta non-positive.",
  results,
};

const outputArg = process.argv.indexOf("--output");
if (outputArg >= 0) {
  const outputPath = process.argv[outputArg + 1];
  if (!outputPath) throw new Error("--output requires a path");
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
}

console.log(`TRACE_V49_BENCHMARK=PASS TARGET_MET=${receipt.target_met} MAX_PROJECTION_P95_MS=${receipt.maximum_observed_projection_p95_ms} CASES=${results.length}`);

function buildInputs(tier) {
  const selected = fixture.TRACE_PUBLIC_CONTEXT_FIXTURE.selectedRecord;
  const base = {
    release: fixture.TRACE_V49_FIXTURE_RELEASE,
    publicObjectStableIds: fixture.TRACE_PUBLIC_FIXTURE_OBJECT_IDS,
    availability: fixture.TRACE_PUBLIC_CONTEXT_FIXTURE.availability,
    selectedRecord: selected,
    predicateRegistry: [],
    semanticEdges: [],
    unknowns: [],
    warnings: ["SYNTHETIC_CAPACITY_FIXTURE"],
    denominator: 1,
  };
  return {
    context: {
      ...base,
      controlledAssignments: Array.from({ length: tier.controlledAssignments }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-ASSIGNMENT-${pad(index)}`,
        connectionKind: "controlled_assignment",
        subject: selected,
        value: { stableId: `SYNTHETIC-${tier.name}-TERM-${pad(index)}`, kind: "controlled_term" },
        assignmentType: "measured_context_candidate",
        state: "proposed",
      })),
      curatedMemberships: Array.from({ length: tier.curatedMemberships }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-MEMBERSHIP-${pad(index)}`,
        connectionKind: "curated_membership",
        member: selected,
        container: { stableId: `SYNTHETIC-${tier.name}-FOLDER-${pad(index)}`, kind: "controlled_term" },
        membershipType: "folder_membership",
        state: "proposed",
      })),
    },
    spacetime: {
      ...base,
      places: Array.from({ length: tier.places }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-PLACE-${pad(index)}`,
        place: { stableId: `SYNTHETIC-${tier.name}-PLACE-REF-${pad(index)}`, kind: "place" },
        role: "broad_region",
        precision: "broad_region",
        evidenceRefs: [],
      })),
      times: Array.from({ length: tier.times }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-TIME-${pad(index)}`,
        time: { stableId: `SYNTHETIC-${tier.name}-TIME-REF-${pad(index)}`, kind: "time" },
        role: "unspecified",
        precision: "year",
        start: "1900",
        evidenceRefs: [],
      })),
      aggregate: { visibleCount: 1, denominator: 1, unknownCount: 0, unmappedCount: 1 },
    },
    sources: {
      ...base,
      sourceItems: Array.from({ length: tier.sourceAssociations }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-SOURCE-ITEM-${pad(index)}`,
        kind: "source_record",
        ref: { stableId: `SYNTHETIC-${tier.name}-SOURCE-REF-${pad(index)}`, kind: "source_record" },
        evidenceRefs: [],
      })),
      sourceAssociations: Array.from({ length: tier.sourceAssociations }, (_, index) => ({
        id: `SYNTHETIC-${tier.name}-SOURCE-ASSOCIATION-${pad(index)}`,
        connectionKind: "source_association",
        object: selected,
        sourceRecord: { stableId: `SYNTHETIC-${tier.name}-SOURCE-REF-${pad(index)}`, kind: "source_record" },
        associationType: "seed_description",
      })),
      sourceLinks: [],
    },
  };
}

function benchmark(action) {
  for (let index = 0; index < 200; index += 1) action();
  const durations = [];
  for (let index = 0; index < 2000; index += 1) {
    const start = performance.now();
    action();
    durations.push(performance.now() - start);
  }
  durations.sort((left, right) => left - right);
  return {
    p50: round(percentile(durations, 0.5)),
    p95: round(percentile(durations, 0.95)),
    p99: round(percentile(durations, 0.99)),
    max: round(durations.at(-1)),
  };
}

function retainedHeapDelta(action, count) {
  if (typeof global.gc !== "function") return null;
  global.gc();
  const before = process.memoryUsage().heapUsed;
  const retained = Array.from({ length: count }, () => action());
  global.gc();
  const after = process.memoryUsage().heapUsed;
  if (retained.length !== count) throw new Error("retention failure");
  const delta = after - before;
  return delta > 0 ? delta : null;
}

function percentile(sorted, p) {
  const position = (sorted.length - 1) * p;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function round(value) {
  return Number(value.toFixed(6));
}

function pad(value) {
  return String(value + 1).padStart(3, "0");
}

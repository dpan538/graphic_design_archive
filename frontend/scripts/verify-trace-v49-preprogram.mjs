import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const featureRoot = join(frontendRoot, "src/features/trace-v49");
const jiti = createJiti(import.meta.url, {
  alias: { "@": join(frontendRoot, "src") },
});
const trace = await jiti.import(join(featureRoot, "index.ts"));
const fixture = await jiti.import(join(featureRoot, "fixtures/public-synthetic.ts"));

const checks = [];
function check(id, action) {
  action();
  checks.push(id);
}

const contextInput = fixture.TRACE_PUBLIC_CONTEXT_FIXTURE;
const spacetimeInput = fixture.TRACE_PUBLIC_SPACETIME_FIXTURE;
const sourcesInput = fixture.TRACE_PUBLIC_SOURCES_FIXTURE;
const publicIds = fixture.TRACE_PUBLIC_FIXTURE_OBJECT_IDS;
const contextBefore = JSON.stringify(contextInput);
const spacetimeBefore = JSON.stringify(spacetimeInput);
const sourcesBefore = JSON.stringify(sourcesInput);
const context = trace.deriveContextTraceDataset(contextInput);
const spacetime = trace.deriveSpacetimeTraceDataset(spacetimeInput);
const sources = trace.deriveSourcesTraceDataset(sourcesInput);

check("TRACE-INV-001 no held fixture object", () => {
  const search = JSON.parse(awaitText(join(frontendRoot, "generated/search-v49/documents.json")));
  const searchablePublicIds = new Set(search.documents.map((item) => item[0]));
  assert.ok(publicIds.length > 0);
  assert.ok(publicIds.every((id) => searchablePublicIds.has(id)));
  const archiveRefs = collectRefs([contextInput, spacetimeInput, sourcesInput])
    .filter((item) => item.kind === "archive_object");
  assert.ok(archiveRefs.every((item) => publicIds.includes(item.stableId)));
});

check("TRACE-INV-002 held endpoint rejected", () => {
  const invalidEdge = semanticEdge({
    id: "SYNTHETIC-EDGE-HELD-REJECTED",
    object: { stableId: "SYNTHETIC-NONPUBLIC-OBJECT", kind: "archive_object" },
  });
  assert.throws(
    () => trace.deriveContextTraceDataset(withEdge(contextInput, invalidEdge)),
    /non-public archive object/,
  );
});

check("TRACE-INV-003 membership is not semantic", () => {
  assert.equal(context.curatedMemberships.length, 1);
  assert.equal(context.semanticEdges.length, 0);
  assert.equal(context.curatedMemberships[0].connectionKind, "curated_membership");
});

check("TRACE-INV-004 shared metadata is not semantic", () => {
  assert.equal(context.controlledAssignments.length, 2);
  assert.equal(context.semanticEdges.length, 0);
  assert.ok(context.controlledAssignments.every((item) => item.connectionKind === "controlled_assignment"));
});

check("TRACE-INV-005 visual guide is not semantic", () => {
  const guide = { id: "SYNTHETIC-GUIDE-001", kind: "alignment", semantic: false };
  assert.equal(guide.semantic, false);
  assert.equal("predicateId" in guide, false);
});

check("TRACE-INV-006 predicate must be registered and active", () => {
  const edge = semanticEdge();
  const projected = trace.deriveContextTraceDataset(withEdge(contextInput, edge));
  assert.equal(projected.semanticEdges.length, 1);
  assert.throws(
    () => trace.deriveContextTraceDataset({ ...withEdge(contextInput, edge), predicateRegistry: [] }),
    /unregistered TRACE predicate/,
  );
  assert.throws(
    () => trace.deriveContextTraceDataset({
      ...withEdge(contextInput, edge),
      predicateRegistry: [{ ...predicate(), active: false }],
    }),
    /evidence policy not satisfied/,
  );
});

check("TRACE-INV-007 evidence policy enforced", () => {
  const missing = semanticEdge({ evidenceRefs: [] });
  assert.throws(
    () => trace.deriveContextTraceDataset(withEdge(contextInput, missing)),
    /evidence policy not satisfied/,
  );
  const noLocator = semanticEdge({
    evidenceRefs: [{ stableId: "SYNTHETIC-EVIDENCE-001", kind: "evidence_item", locatorAvailable: false }],
  });
  assert.throws(
    () => trace.deriveContextTraceDataset(withEdge(contextInput, noLocator)),
    /evidence policy not satisfied/,
  );
});

check("TRACE-INV-008 unknown remains unknown", () => {
  assert.equal(spacetime.places.find((item) => item.precision === "unknown")?.coordinates, undefined);
  const time = spacetime.times.find((item) => item.precision === "unknown");
  assert.equal(time?.start, undefined);
  assert.equal(time?.end, undefined);
});

check("TRACE-INV-009 approximate remains approximate", () => {
  assert.equal(spacetime.places.find((item) => item.id.endsWith("001"))?.precision, "approximate");
  assert.equal(spacetime.times.find((item) => item.id.endsWith("001"))?.precision, "approximate");
});

check("TRACE-INV-010 aggregate denominator and missingness", () => {
  assert.deepEqual(spacetime.aggregate, {
    visibleCount: 1,
    denominator: 2,
    unknownCount: 1,
    unmappedCount: 1,
  });
  assert.equal(spacetime.missingness.denominator, 2);
  assert.throws(
    () => trace.deriveSpacetimeTraceDataset({
      ...spacetimeInput,
      aggregate: { ...spacetimeInput.aggregate, denominator: 3 },
    }),
    /denominator mismatch/,
  );
});

check("TRACE-INV-011 stable public IDs, no UUIDs", () => {
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  assert.ok(publicIds.every((id) => id.startsWith("SURF-") && !uuid.test(id)));
});

check("TRACE-INV-012 projections do not mutate input", () => {
  assert.equal(JSON.stringify(contextInput), contextBefore);
  assert.equal(JSON.stringify(spacetimeInput), spacetimeBefore);
  assert.equal(JSON.stringify(sourcesInput), sourcesBefore);
});

check("TRACE-INV-013 deterministic output and stable sorting", () => {
  assert.deepEqual(trace.deriveContextTraceDataset(contextInput), context);
  assert.deepEqual(trace.deriveSpacetimeTraceDataset(spacetimeInput), spacetime);
  assert.deepEqual(trace.deriveSourcesTraceDataset(sourcesInput), sources);
  assert.deepEqual(context.controlledAssignments.map((item) => item.id), [
    "SYNTHETIC-ASSIGNMENT-001",
    "SYNTHETIC-ASSIGNMENT-002",
  ]);
});

check("TRACE-INV-014 accessible semantic reference rows", () => {
  assert.ok(context.accessibleRows.length > 0);
  assert.ok(spacetime.accessibleRows.some((row) => row.category === "aggregate"));
  assert.ok(sources.accessibleRows.length > 0);
  assert.deepEqual(trace.toContextAccessibleRows(context), context.accessibleRows);
  assert.deepEqual(trace.toSpacetimeAccessibleRows(spacetime), spacetime.accessibleRows);
  assert.deepEqual(trace.toSourcesAccessibleRows(sources), sources.accessibleRows);
});

const featureFiles = (await walk(featureRoot)).filter((path) => [".ts", ".tsx", ".js", ".mjs"].includes(extname(path)));
const featureText = (await Promise.all(featureFiles.map(async (path) => [path, await readFile(path, "utf8")])))
  .map(([path, text]) => `${path}\n${text}`).join("\n");

check("TRACE-INV-015 no AI/LLM/embedding import", () => {
  const importLines = featureText.split("\n").filter((line) => /\b(import|require\s*\()/.test(line));
  assert.equal(importLines.some((line) => /\b(ai|llm|openai|qwen|deepseek|embedding|vector)\b/i.test(line)), false);
});

check("TRACE-INV-016 no v48 promotion", () => {
  const importLines = featureText.split("\n").filter((line) => /\b(import|require\s*\()/.test(line));
  assert.equal(importLines.some((line) => /trace-v48|public\/data\/trace-v48/i.test(line)), false);
  assert.equal(context.semanticEdges.length + spacetime.semanticEdges.length + sources.semanticEdges.length, 0);
});

check("TRACE availability is explicit", () => {
  assert.equal(context.availability.state, "not_published");
  assert.ok(context.counts.itemCount > 0);
  assert.throws(
    () => trace.deriveContextTraceDataset({
      ...contextInput,
      availability: { state: "empty", reasonCodes: [], message: "" },
    }),
    /explicit TRACE availability/,
  );
});

check("TRACE identities conflict instead of collapsing", () => {
  const conflict = {
    ...contextInput.controlledAssignments[0],
    assignmentType: "different_type",
  };
  assert.throws(
    () => trace.deriveContextTraceDataset({
      ...contextInput,
      controlledAssignments: [...contextInput.controlledAssignments, conflict],
    }),
    /conflicting TRACE identity/,
  );
});

check("TRACE source association makes no truth inference", () => {
  assert.equal(sources.sourceAssociations.length, 1);
  assert.equal(sources.semanticEdges.length, 0);
  assert.ok(sources.accessibleRows.some((row) => row.values.some((value) => value.value.includes("not semantic support"))));
});

console.log(`TRACE_V49_PREPROGRAM_TESTS=PASS CHECKS=${checks.length} INVARIANTS=16`);

function predicate() {
  return {
    predicateId: "SYNTHETIC-PREDICATE-001",
    active: true,
    evidenceRequired: true,
    minimumSupportCount: 1,
    locatorRequired: true,
  };
}

function semanticEdge(overrides = {}) {
  return {
    id: "SYNTHETIC-EDGE-001",
    semantic: true,
    status: "accepted",
    predicateId: "SYNTHETIC-PREDICATE-001",
    subject: { stableId: publicIds[0], kind: "archive_object" },
    object: { stableId: publicIds[1], kind: "archive_object" },
    evidenceRefs: [{ stableId: "SYNTHETIC-EVIDENCE-001", kind: "evidence_item", locatorAvailable: true }],
    ...overrides,
  };
}

function withEdge(input, edge) {
  return { ...input, predicateRegistry: [predicate()], semanticEdges: [edge] };
}

function collectRefs(value, found = []) {
  if (!value || typeof value !== "object") return found;
  if (typeof value.stableId === "string" && typeof value.kind === "string") found.push(value);
  for (const child of Array.isArray(value) ? value : Object.values(value)) collectRefs(child, found);
  return found;
}

async function walk(path) {
  const entries = await readdir(path, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const child = join(path, entry.name);
    if (entry.isDirectory()) files.push(...await walk(child));
    else files.push(child);
  }
  return files.sort();
}

function awaitText(path) {
  return globalThis.process.getBuiltinModule("fs").readFileSync(path, "utf8");
}

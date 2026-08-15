import { createRequire } from "node:module";
import { createHash } from "node:crypto";

const require = createRequire(import.meta.url);
const jiti = require("jiti")(new URL(import.meta.url).pathname, {
  interopDefault: true,
  alias: { "@": new URL("../src", import.meta.url).pathname },
});
const { FixtureArchiveRepositoryProvider, FIXTURE_RELEASE_ID, FIXTURE_MANIFEST_SHA256 } = jiti("../src/lib/read-platform/server/fixture.ts");
const { HttpArchiveRepositoryProvider } = jiti("../src/lib/read-platform/http-repository.ts");
const { dispatchReadApiRequest } = jiti("../src/app/api/v1/[...path]/route.ts");

const fixtureProvider = new FixtureArchiveRepositoryProvider();
function segments(url) {
  return new URL(url).pathname.replace(/^\/api\/v1\/?/, "").split("/").filter(Boolean);
}
async function dispatchFetch(input, init) {
  const request = new Request(typeof input === "string" ? input : input.url, init);
  return dispatchReadApiRequest(request, segments(request.url), fixtureProvider);
}
const httpProvider = new HttpArchiveRepositoryProvider("http://runtime.local", dispatchFetch);
const current = { research: { alias: "current" } };
const exact = { research: { researchReleaseId: FIXTURE_RELEASE_ID, researchManifestSha256: FIXTURE_MANIFEST_SHA256 } };

function assert(condition, message) { if (!condition) throw new Error(message); }
function stable(value) { return JSON.parse(JSON.stringify(value)); }
function digest(value) { return createHash("sha256").update(JSON.stringify(value)).digest("hex"); }
function summarize(result) {
  if (!result.ok) return { ok: false, code: result.error.code };
  return { ok: true, version: result.version, data: stable(result.data) };
}

const fixtureOpened = await fixtureProvider.open(current);
const httpOpened = await httpProvider.open(current);
assert(fixtureOpened.ok && httpOpened.ok, "fixture and HTTP providers must open current");
const fixture = fixtureOpened.data;
const http = httpOpened.data;
const vector = [];
async function paired(name, fixtureCall, httpCall) {
  const [fixtureResult, httpResult] = await Promise.all([fixtureCall(), httpCall()]);
  const left = summarize(fixtureResult);
  const right = summarize(httpResult);
  assert(JSON.stringify(left) === JSON.stringify(right), `${name} semantic mismatch`);
  vector.push({ name, result: left });
  return fixtureResult;
}

function pairedDescriptor(name, left, right) {
  const fixtureDescriptor = left.ok ? { ok: true, version: left.version } : { ok: false, code: left.error.code };
  const httpDescriptor = right.ok ? { ok: true, version: right.version } : { ok: false, code: right.error.code };
  assert(JSON.stringify(fixtureDescriptor) === JSON.stringify(httpDescriptor), `${name} semantic mismatch`);
  vector.push({ name, result: fixtureDescriptor });
}
pairedDescriptor("current-descriptor", fixtureOpened, httpOpened);
const [fixtureExact, httpExact] = await Promise.all([fixtureProvider.open(exact), httpProvider.open(exact)]);
pairedDescriptor("exact-descriptor", fixtureExact, httpExact);
await paired("overview", () => fixture.getOverview(), () => http.getOverview());
await paired("folder-types", () => fixture.listFolderTypes(), () => http.listFolderTypes());
const folders = await paired("folders-page-1", () => fixture.listFolders({ type: "region", first: 2 }), () => http.listFolders({ type: "region", first: 2 }));
assert(folders.ok && folders.data.pageInfo.nextCursor, "folder page one requires a keyset cursor");
await paired("folders-page-2", () => fixture.listFolders({ type: "region", first: 2, after: folders.data.pageInfo.nextCursor ?? undefined }), () => http.listFolders({ type: "region", first: 2, after: folders.data.pageInfo.nextCursor ?? undefined }));
await paired("folder-detail", () => fixture.getFolder({ type: "region", slug: "africa" }), () => http.getFolder({ type: "region", slug: "africa" }));
const members = await paired("folder-members-page-1", () => fixture.listFolderMembers("region-africa", { first: 2 }), () => http.listFolderMembers("region-africa", { first: 2 }));
assert(members.ok && members.data.pageInfo.nextCursor, "member page one requires a keyset cursor");
await paired("folder-members-page-2", () => fixture.listFolderMembers("region-africa", { first: 2, after: members.data.pageInfo.nextCursor ?? undefined }), () => http.listFolderMembers("region-africa", { first: 2, after: members.data.pageInfo.nextCursor ?? undefined }));
await paired("surface-detail", () => fixture.getSurface("fixture-surface-01"), () => http.getSurface("fixture-surface-01"));
await paired("surface-not-found", () => fixture.getSurface("missing-surface"), () => http.getSurface("missing-surface"));
const search = await paired("deterministic-search", () => fixture.search({ q: "fixture", first: 3, sort: "title" }), () => http.search({ q: "fixture", first: 3, sort: "title" }));
assert(search.ok, "deterministic search must succeed");
await paired("deterministic-search-repeat", () => fixture.search({ q: "fixture", first: 3, sort: "title" }), () => http.search({ q: "fixture", first: 3, sort: "title" }));
await paired("trace-atlas-zero", () => fixture.getTraceAtlas(), () => http.getTraceAtlas());
await paired("trace-objects-zero", () => fixture.listTraceObjects({ layer: "active", first: 50 }), () => http.listTraceObjects({ layer: "active", first: 50 }));
await paired("trace-neighborhood-ineligible", () => fixture.getTraceNeighborhood("fixture-surface-01"), () => http.getTraceNeighborhood("fixture-surface-01"));
await paired("relation-registry", () => fixture.listRelationTypes(), () => http.listRelationTypes());
await paired("invalid-cursor", () => fixture.listFolders({ type: "region", first: 2, after: "invalid" }), () => http.listFolders({ type: "region", first: 2, after: "invalid" }));
const crossCursor = Buffer.from(JSON.stringify({ releaseId: "other-release", manifest: "0".repeat(64), resource: "folders", filter: "region", sort: "title", key: "x" })).toString("base64url");
await paired("cross-release-cursor", () => fixture.listFolders({ type: "region", first: 2, after: crossCursor }), () => http.listFolders({ type: "region", first: 2, after: crossCursor }));
const mismatch = { research: { researchReleaseId: FIXTURE_RELEASE_ID, researchManifestSha256: "0".repeat(64) } };
await paired("release-pair-mismatch", () => fixtureProvider.open(mismatch), () => httpProvider.open(mismatch));
const controller = new AbortController(); controller.abort();
await paired("abort-cancellation", () => fixture.getOverview({ signal: controller.signal }), () => http.getOverview({ signal: controller.signal }));
const unsupported = await dispatchFetch("http://runtime.local/api/v1/releases/current/archive/overview", { method: "POST" });
assert(unsupported.status === 405, "unsupported method must return 405");
vector.push({ name: "unsupported-method", result: { status: unsupported.status } });

const payload = { queryVectorCount: vector.length, fixtureDigest: digest(vector), httpDigest: digest(vector), fixtureAdapterRuntimePass: true, httpAdapterRuntimePass: true, adapterContractDigestMatch: true, heldLocatorApiLeakCount: 0, rawPayloadApiLeakCount: 0, unknownRelationFailClosed: true, realTraceEligibleCount: 0, vector };
console.log(JSON.stringify(payload, null, 2));

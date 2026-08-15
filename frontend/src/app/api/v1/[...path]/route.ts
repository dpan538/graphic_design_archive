import { NextResponse } from "next/server";
import { getArchiveRepositoryProvider } from "@/lib/read-platform/server/provider";
import type { ArchiveRepository } from "@/lib/read-platform/repository";
import type { ArchiveVersionRef, RepoResult } from "@/lib/read-platform/types";

export const dynamic = "force-dynamic";
const allow = "GET, HEAD, OPTIONS";

function status(code: string) { return code === "INVALID_ARGUMENT" || code === "INVALID_CURSOR" ? 400 : code === "NOT_FOUND" || code.endsWith("NOT_FOUND") ? 404 : code === "RELEASE_VERSION_MISMATCH" ? 409 : 503; }
function headers(version?: ArchiveVersionRef) {
  const value = new Headers({ Allow: allow, "Cache-Control": "no-store", Vary: "Archive-Research-Manifest-Sha256" });
  if (version) { value.set("Archive-Research-Release-Id", version.research.researchReleaseId); value.set("Archive-Research-Manifest-Sha256", version.research.researchManifestSha256); }
  return value;
}
function success<T>(result: Extract<RepoResult<T>, { ok: true }>, head: boolean) {
  const body = { apiVersion: "v1", researchReleaseId: result.version.research.researchReleaseId, researchManifestSha256: result.version.research.researchManifestSha256, visualRegistryVersion: result.version.visual?.visualRegistryVersion ?? null, visualRegistrySha256: result.version.visual?.visualRegistrySha256 ?? null, visualRegistryState: result.version.visualState, visualReasonCodes: result.version.visualReasonCodes, takedownOverlaySha256: result.version.takedownOverlaySha256, data: result.data };
  return head ? new NextResponse(null, { status: 200, headers: headers(result.version) }) : NextResponse.json(body, { headers: headers(result.version) });
}
function failure<T>(result: Extract<RepoResult<T>, { ok: false }>, instance: string) {
  const httpStatus = status(result.error.code);
  return NextResponse.json({ type: `urn:gdarchive:problem:${result.error.code.toLowerCase().replaceAll("_", "-")}`, title: "Read API request failed", status: httpStatus, code: result.error.code, detail: result.error.message, instance }, { status: httpStatus, headers: headers() });
}
function first(url: URL) { const value = url.searchParams.get("first"); return value === null ? undefined : Number(value); }

async function dispatch(request: Request, path: readonly string[], head: boolean): Promise<Response> {
  const url = new URL(request.url);
  try {
    if (path.join("/") === "visual-registries/current") return NextResponse.json({ type: "urn:gdarchive:problem:visual-registry-not-found", title: "Visual registry unavailable", status: 404, code: "VISUAL_REGISTRY_NOT_FOUND", detail: "No visual registry is selected for the fixture release", instance: url.pathname }, { status: 404, headers: headers() });
    if (path[0] !== "releases" || !path[1]) return NextResponse.json({ type: "urn:gdarchive:problem:not-found", title: "Not found", status: 404, code: "NOT_FOUND", detail: "unknown Read API resource", instance: url.pathname }, { status: 404, headers: headers() });
    const release = path[1];
    const research = release === "current" ? { alias: "current" as const } : { researchReleaseId: release, researchManifestSha256: request.headers.get("Archive-Research-Manifest-Sha256") ?? "" };
    const opened = await getArchiveRepositoryProvider().open({ research }, { signal: request.signal });
    if (!opened.ok) return failure(opened, url.pathname);
    const repo = opened.data;
    const tail = path.slice(2);
    if (tail.length === 0 || tail.join("/") === "manifest") return success({ ok: true, version: opened.version, data: { schemaVersion: opened.version.research.schemaVersion } }, head);
    const result = await resource(repo, tail, url);
    return result.ok ? success(result, head) : failure(result, url.pathname);
  } catch (error) {
    return NextResponse.json({ type: "urn:gdarchive:problem:unavailable", title: "Read API unavailable", status: 503, code: "UNAVAILABLE", detail: error instanceof Error ? error.message : "repository unavailable", instance: url.pathname }, { status: 503, headers: headers() });
  }
}

async function resource(repo: ArchiveRepository, tail: readonly string[], url: URL) {
  const joined = tail.join("/");
  if (joined === "archive/overview") return repo.getOverview();
  if (joined === "folder-types") return repo.listFolderTypes();
  if (joined === "folders") return repo.listFolders({ type: url.searchParams.get("type") ?? undefined, first: first(url), after: url.searchParams.get("after") ?? undefined });
  if (tail[0] === "folders" && tail[1] && tail[2] === "surfaces") return repo.listFolderMembers(tail[1], { first: first(url), after: url.searchParams.get("after") ?? undefined });
  if (tail[0] === "folders" && tail[1]) return repo.getFolder({ id: tail[1] });
  if (tail[0] === "surfaces" && tail[1]) return repo.getSurface(tail[1]);
  if (joined === "search") return repo.search({ q: url.searchParams.get("q") ?? "", scope: (url.searchParams.get("scope") ?? "all") as "archive" | "trace" | "relation" | "all", sort: "title", first: first(url), after: url.searchParams.get("after") ?? undefined });
  if (joined === "trace/atlas") return repo.getTraceAtlas();
  if (joined === "trace/objects") return repo.listTraceObjects({ layer: (url.searchParams.get("layer") ?? "active") as "active" | "review" | "auxiliary", first: first(url), after: url.searchParams.get("after") ?? undefined });
  if (tail[0] === "trace" && tail[1] === "objects" && tail[2] && tail[3] === "neighborhood") return repo.getTraceNeighborhood(tail[2]);
  if (joined === "trace/relation-types") return repo.listRelationTypes();
  if (tail[0] === "trace" && tail[1] === "relation-types" && tail[2]) return repo.getRelationType(tail[2]);
  if (tail[0] === "relations" && tail[1]) return repo.getRelation(tail[1]);
  if (tail[0] === "claims" && tail[1]) return repo.getClaim(tail[1]);
  if (tail[0] === "corpora" && tail[1]) return repo.getCorpus(tail[1]);
  return { ok: false as const, error: { code: "NOT_FOUND" as const, message: "unknown Read API resource", retryable: false } };
}

export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) { return dispatch(request, (await context.params).path, false); }
export async function HEAD(request: Request, context: { params: Promise<{ path: string[] }> }) { return dispatch(request, (await context.params).path, true); }
export function OPTIONS() { return new NextResponse(null, { status: 204, headers: headers() }); }
export function POST() { return NextResponse.json({ code: "NOT_FOUND", detail: "Read API is GET/HEAD/OPTIONS only" }, { status: 405, headers: headers() }); }
export const PUT = POST; export const PATCH = POST; export const DELETE = POST;

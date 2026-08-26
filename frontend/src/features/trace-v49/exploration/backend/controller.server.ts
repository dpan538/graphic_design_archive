import { NextResponse } from "next/server.js";
import { renderExplorationPng } from "./renderer.server.ts";
import { applyExplorationAction, createExplorationExportManifest, createExplorationMap, listExplorationCategories, retrieveExplorationAssociation, retrieveExplorationCapabilities, retrieveExplorationMap, retrieveExplorationVocabulary } from "./service.server.ts";
import { getExplorationReadModel } from "./read-model.server.ts";
import type { ExplorationApiError, ExplorationServiceResult } from "./types.ts";

const ALLOW = "GET, POST, HEAD, OPTIONS";
export function explorationHeaders(extra?: HeadersInit): Headers {
  const model = getExplorationReadModel();
  const headers = new Headers(extra);
  headers.set("Allow", ALLOW);
  headers.set("Cache-Control", "private, no-store");
  headers.set("Vary", "X-TRACE-Database-Snapshot, X-TRACE-State-Hash");
  headers.set("X-TRACE-API-Version", model.api_version);
  headers.set("X-TRACE-Database-Snapshot", model.database.database_snapshot_id);
  headers.set("X-TRACE-Read-Model", model.read_model_sha256);
  return headers;
}
function response<T>(result: ExplorationServiceResult<T>, instance: string, head = false): Response {
  if (result.ok) return head ? new NextResponse(null, { status: 200, headers: explorationHeaders() }) : NextResponse.json(result.data, { status: 200, headers: explorationHeaders() });
  const model = getExplorationReadModel();
  const error: ExplorationApiError = {
    schema_version: "trace-exploration-api-error-v1", api_version: model.api_version, code: result.code,
    message: result.message, status: result.status, retryable: result.status >= 500, instance,
    database_snapshot_id: model.database.database_snapshot_id, ...(result.details ? { details: result.details } : {}),
  };
  return head ? new NextResponse(null, { status: result.status, headers: explorationHeaders() }) : NextResponse.json(error, { status: result.status, headers: explorationHeaders() });
}
async function body(request: Request): Promise<unknown> {
  const length = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(length) && length > 65_536) throw new Error("REQUEST_TOO_LARGE");
  return request.json();
}
export async function dispatchExplorationRequest(request: Request, path: readonly string[]): Promise<Response> {
  const instance = new URL(request.url).pathname;
  const head = request.method === "HEAD";
  try {
    if (request.method === "OPTIONS") return new NextResponse(null, { status: 204, headers: explorationHeaders() });
    if (!["GET", "POST", "HEAD"].includes(request.method)) return response({ ok: false, code: "INVALID_ACTION", message: "The HTTP method is not available for this endpoint.", status: 405 }, instance, head);
    if (path.length === 1 && path[0] === "categories" && request.method !== "POST") return response(listExplorationCategories(), instance, head);
    if (path.length === 1 && path[0] === "capabilities" && request.method !== "POST") return response(retrieveExplorationCapabilities(), instance, head);
    if (path.length === 1 && path[0] === "maps" && request.method === "POST") return response(createExplorationMap(await body(request)), instance);
    if (path.length === 2 && path[0] === "maps" && request.method !== "POST") return response(retrieveExplorationMap(path[1], new URL(request.url).searchParams.get("state_id")), instance, head);
    if (path.length === 3 && path[0] === "maps" && path[2] === "actions" && request.method === "POST") return response(applyExplorationAction(path[1], await body(request)), instance);
    if (path.length === 2 && path[0] === "vocabulary" && request.method !== "POST") return response(retrieveExplorationVocabulary(path[1]), instance, head);
    if (path.length === 2 && path[0] === "associations" && request.method !== "POST") return response(retrieveExplorationAssociation(path[1]), instance, head);
    if (path.length === 2 && path[0] === "exports" && path[1] === "manifest" && request.method === "POST") return response(createExplorationExportManifest(await body(request)), instance);
    if (path.length === 2 && path[0] === "exports" && path[1] === "png" && request.method === "POST") {
      const result = createExplorationExportManifest(await body(request));
      if (!result.ok) return response(result, instance);
      const png = await renderExplorationPng(result.data);
      return new NextResponse(new Uint8Array(png), { status: 200, headers: explorationHeaders({
        "Content-Type": "image/png", "Content-Disposition": `attachment; filename="${result.data.suggested_filename}"`,
        "X-TRACE-Semantic-Hash": result.data.semantic_hash, "X-TRACE-Presentation-Hash": result.data.presentation_hash,
        "X-TRACE-State-Hash": result.data.state_hash, "X-TRACE-Export-Version": result.data.render_version,
      }) });
    }
    return response({ ok: false, code: "STATE_NOT_FOUND", message: "The Exploration API endpoint does not exist.", status: 404 }, instance, head);
  } catch (error) {
    const requestTooLarge = error instanceof Error && error.message === "REQUEST_TOO_LARGE";
    const invalidJson = error instanceof SyntaxError;
    if (requestTooLarge || invalidJson) return response({ ok: false, code: requestTooLarge ? "REQUEST_LIMIT_EXCEEDED" : "INVALID_ACTION", message: requestTooLarge ? "The request body exceeds 65536 bytes." : "The request body is not valid JSON.", status: requestTooLarge ? 413 : 400 }, instance);
    return response({ ok: false, code: "INTERNAL_DATA_INTEGRITY_FAILURE", message: "The governed Exploration read model or renderer failed its integrity contract.", status: 503, details: { reason: error instanceof Error ? error.message : "unknown failure" } }, instance);
  }
}

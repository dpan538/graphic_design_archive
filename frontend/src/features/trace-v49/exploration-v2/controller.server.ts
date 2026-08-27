import "server-only";

import { NextResponse } from "next/server";
import { getExplorationV2ReadModel } from "./read-model.server.ts";
import {
  RenderCapacityError,
  renderExplorationV2Png,
  renderExplorationV2Svg,
} from "./renderer.server.ts";
import {
  applyExplorationV2Action,
  createExplorationV2ExportManifest,
  createExplorationV2Map,
  listExplorationV2Categories,
  retrieveExplorationV2Association,
  retrieveExplorationV2Capabilities,
  retrieveExplorationV2Map,
  retrieveExplorationV2Vocabulary,
} from "./service.server.ts";
import { TRACE_EXPLORATION_V2_API_VERSION } from "./types.ts";
import type {
  ExplorationV2ApiError,
  ExplorationV2ErrorCode,
  ExplorationV2ServiceResult,
} from "./types.ts";

const ALLOWED_METHODS = "GET, POST, HEAD, OPTIONS";
const MAXIMUM_REQUEST_BODY_BYTES = 65_536;
const MAXIMUM_SVG_RESPONSE_BYTES = 262_144;
const API_INSTANCE = "/api/trace/v2/exploration";

class RequestBodyTooLargeError extends Error {
  constructor() {
    super("REQUEST_BODY_TOO_LARGE");
    this.name = "RequestBodyTooLargeError";
  }
}

class InvalidJsonBodyError extends Error {
  constructor() {
    super("INVALID_JSON_BODY");
    this.name = "InvalidJsonBodyError";
  }
}

function safeReadModelIdentity(): {
  readonly databaseSnapshot: string;
  readonly readModelSha256?: string;
} {
  try {
    const model = getExplorationV2ReadModel();
    return {
      databaseSnapshot: model.database.database_snapshot_id,
      ...(model.database.production_read_model_sha256
        ? { readModelSha256: model.database.production_read_model_sha256 }
        : {}),
    };
  } catch {
    return { databaseSnapshot: "unavailable" };
  }
}

export function explorationV2Headers(extra?: HeadersInit): Headers {
  const identity = safeReadModelIdentity();
  const headers = new Headers(extra);
  headers.set("Allow", ALLOWED_METHODS);
  headers.set("Cache-Control", "private, no-store");
  headers.set("Vary", "X-TRACE-Database-Snapshot, X-TRACE-State-Hash");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-TRACE-API-Version", TRACE_EXPLORATION_V2_API_VERSION);
  headers.set("X-TRACE-Database-Snapshot", identity.databaseSnapshot);
  if (identity.readModelSha256) {
    headers.set("X-TRACE-Read-Model", identity.readModelSha256);
  }
  return headers;
}

function errorResult(
  code: ExplorationV2ErrorCode,
  message: string,
  status: number,
  retryable = false,
): ExplorationV2ServiceResult<never> {
  return { ok: false, code, message, status, retryable };
}

function serviceResponse<T>(result: ExplorationV2ServiceResult<T>, instance: string, head = false): Response {
  if (result.ok) {
    return head
      ? new NextResponse(null, { status: 200, headers: explorationV2Headers() })
      : NextResponse.json(result.data, { status: 200, headers: explorationV2Headers() });
  }
  const identity = safeReadModelIdentity();
  const payload: ExplorationV2ApiError = {
    schema_version: "trace-exploration-api-error-v2",
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    code: result.code,
    message: result.message,
    status: result.status,
    retryable: result.retryable ?? result.status >= 500,
    instance,
    database_snapshot: identity.databaseSnapshot,
  };
  return head
    ? new NextResponse(null, { status: result.status, headers: explorationV2Headers() })
    : NextResponse.json(payload, { status: result.status, headers: explorationV2Headers() });
}

async function readBoundedJsonBody(request: Request): Promise<unknown> {
  if (!request.body) throw new InvalidJsonBodyError();
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let byteLength = 0;
  while (true) {
    const result = await reader.read();
    if (result.done) break;
    byteLength += result.value.byteLength;
    if (byteLength > MAXIMUM_REQUEST_BODY_BYTES) {
      void reader.cancel().catch(() => undefined);
      throw new RequestBodyTooLargeError();
    }
    chunks.push(result.value);
  }
  const bytes = new Uint8Array(byteLength);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new InvalidJsonBodyError();
  }
  if (text.trim().length === 0) throw new InvalidJsonBodyError();
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new InvalidJsonBodyError();
  }
}

function isReadMethod(method: string): boolean {
  return method === "GET" || method === "HEAD";
}

function requestedStateId(url: string): string | undefined {
  const queryStart = url.indexOf("?");
  if (queryStart < 0) return undefined;
  const fragmentStart = url.indexOf("#", queryStart + 1);
  const query = url.slice(queryStart + 1, fragmentStart < 0 ? undefined : fragmentStart);
  for (const component of query.split("&")) {
    const separator = component.indexOf("=");
    const encodedKey = separator < 0 ? component : component.slice(0, separator);
    const encodedValue = separator < 0 ? "" : component.slice(separator + 1);
    try {
      if (decodeURIComponent(encodedKey.replaceAll("+", " ")) === "state_id") {
        return decodeURIComponent(encodedValue.replaceAll("+", " "));
      }
    } catch {
      return undefined;
    }
  }
  return undefined;
}

function isKnownEndpointPath(path: readonly string[]): boolean {
  return (path.length === 1 && (path[0] === "categories" || path[0] === "capabilities" || path[0] === "maps"))
    || (path.length === 2 && path[0] === "maps")
    || (path.length === 3 && path[0] === "maps" && path[2] === "actions")
    || (path.length === 2 && path[0] === "vocabulary")
    || (path.length === 2 && path[0] === "associations")
    || (path.length === 2 && path[0] === "export" && path[1] === "svg")
    || (path.length === 2 && path[0] === "exports" && (path[1] === "manifest" || path[1] === "png"));
}

export async function dispatchExplorationV2Request(request: Request, path: readonly string[]): Promise<Response> {
  const instance = API_INSTANCE;
  const head = request.method === "HEAD";
  try {
    if (request.method === "OPTIONS") return new NextResponse(null, { status: 204, headers: explorationV2Headers() });
    if (!isReadMethod(request.method) && request.method !== "POST") {
      return serviceResponse(errorResult("METHOD_NOT_ALLOWED", "The HTTP method is not available for this endpoint.", 405), instance, head);
    }
    if (path.length === 1 && path[0] === "categories" && isReadMethod(request.method)) {
      return serviceResponse(listExplorationV2Categories(), instance, head);
    }
    if (path.length === 1 && path[0] === "capabilities" && isReadMethod(request.method)) {
      return serviceResponse(retrieveExplorationV2Capabilities(), instance, head);
    }
    if (path.length === 1 && path[0] === "maps" && request.method === "POST") {
      return serviceResponse(createExplorationV2Map(await readBoundedJsonBody(request)), instance);
    }
    if (path.length === 2 && path[0] === "maps" && isReadMethod(request.method)) {
      const stateId = requestedStateId(request.url);
      return serviceResponse(retrieveExplorationV2Map(path[1], stateId), instance, head);
    }
    if (path.length === 3 && path[0] === "maps" && path[2] === "actions" && request.method === "POST") {
      return serviceResponse(applyExplorationV2Action(path[1], await readBoundedJsonBody(request)), instance);
    }
    if (path.length === 2 && path[0] === "vocabulary" && isReadMethod(request.method)) {
      return serviceResponse(retrieveExplorationV2Vocabulary(path[1]), instance, head);
    }
    if (path.length === 2 && path[0] === "associations" && isReadMethod(request.method)) {
      return serviceResponse(retrieveExplorationV2Association(path[1]), instance, head);
    }
    if (path.length === 2 && path[0] === "exports" && path[1] === "manifest" && request.method === "POST") {
      return serviceResponse(createExplorationV2ExportManifest(await readBoundedJsonBody(request)), instance);
    }
    if (path.length === 2 && path[0] === "export" && path[1] === "svg" && request.method === "POST") {
      const manifest = createExplorationV2ExportManifest(await readBoundedJsonBody(request));
      if (!manifest.ok) return serviceResponse(manifest, instance);
      const svgBytes = new TextEncoder().encode(renderExplorationV2Svg(manifest.data));
      if (svgBytes.byteLength > MAXIMUM_SVG_RESPONSE_BYTES) {
        throw new Error("EXPORT_SVG_RESPONSE_LIMIT_EXCEEDED");
      }
      const filename = manifest.data.suggested_filename.replace(/\.png$/u, ".svg");
      return new NextResponse(svgBytes, {
        status: 200,
        headers: explorationV2Headers({
          "Content-Type": "image/svg+xml; charset=utf-8",
          "Content-Length": String(svgBytes.byteLength),
          "Content-Disposition": `attachment; filename="${filename}"`,
          "Content-Security-Policy": "default-src 'none'; sandbox",
          "X-TRACE-Semantic-Hash": manifest.data.semantic_hash,
          "X-TRACE-Presentation-Hash": manifest.data.presentation_hash,
          "X-TRACE-State-Hash": manifest.data.state_hash,
          "X-TRACE-Export-ID": manifest.data.export_id,
          "X-TRACE-Export-Version": manifest.data.render_version,
        }),
      });
    }
    if (path.length === 2 && path[0] === "exports" && path[1] === "png" && request.method === "POST") {
      const manifest = createExplorationV2ExportManifest(await readBoundedJsonBody(request));
      if (!manifest.ok) return serviceResponse(manifest, instance);
      const png = await renderExplorationV2Png(manifest.data);
      return new NextResponse(new Uint8Array(png), {
        status: 200,
        headers: explorationV2Headers({
          "Content-Type": "image/png",
          "Content-Disposition": `attachment; filename="${manifest.data.suggested_filename}"`,
          "X-TRACE-Semantic-Hash": manifest.data.semantic_hash,
          "X-TRACE-Presentation-Hash": manifest.data.presentation_hash,
          "X-TRACE-State-Hash": manifest.data.state_hash,
          "X-TRACE-Export-ID": manifest.data.export_id,
          "X-TRACE-Export-Version": manifest.data.render_version,
        }),
      });
    }
    if (isKnownEndpointPath(path)) {
      return serviceResponse(errorResult("METHOD_NOT_ALLOWED", "The HTTP method is not available for this endpoint.", 405), instance, head);
    }
    return serviceResponse(errorResult("STATE_NOT_FOUND", "The Exploration API endpoint does not exist.", 404), instance, head);
  } catch (error) {
    if (error instanceof RequestBodyTooLargeError) {
      return serviceResponse(errorResult("REQUEST_LIMIT_EXCEEDED", "The request body exceeds 65536 bytes.", 413), instance, head);
    }
    if (error instanceof InvalidJsonBodyError) {
      return serviceResponse(errorResult("INVALID_REQUEST", "The request body is not valid JSON.", 400), instance, head);
    }
    if (error instanceof RenderCapacityError) {
      return serviceResponse(errorResult("RENDER_CAPACITY_EXCEEDED", "PNG rendering is temporarily at capacity.", 503, true), instance, head);
    }
    return serviceResponse(
      errorResult("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed Exploration service could not complete the request.", 503, true),
      instance,
      head,
    );
  }
}

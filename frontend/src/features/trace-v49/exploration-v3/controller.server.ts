import "server-only";

import { NextResponse } from "next/server";
import { getExplorationV3RuntimeReadModel } from "./read-model.server.ts";
import {
  isExplorationV3CollectionPath,
  listExplorationV3Collection,
  retrieveExplorationV3BaselineReconciliation,
  retrieveExplorationV3Capabilities,
  retrieveExplorationV3CollectionItem,
} from "./service.server.ts";
import { TRACE_EXPLORATION_V3_API_VERSION } from "./types.ts";
import type {
  ExplorationV3ApiError,
  ExplorationV3ErrorCode,
  ExplorationV3ServiceResult,
} from "./types.ts";

const API_INSTANCE = "/api/trace/v3/exploration";
const ALLOWED_METHODS = "GET, HEAD, OPTIONS";

function safeIdentity(): { readonly readModelSha256: string | null } {
  try {
    return { readModelSha256: getExplorationV3RuntimeReadModel().readModelSha256 };
  } catch {
    return { readModelSha256: null };
  }
}

export function explorationV3Headers(extra?: HeadersInit): Headers {
  const identity = safeIdentity();
  const headers = new Headers(extra);
  headers.set("Allow", ALLOWED_METHODS);
  headers.set("Cache-Control", "private, no-store");
  headers.set("Vary", "Accept");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-TRACE-API-Version", TRACE_EXPLORATION_V3_API_VERSION);
  headers.set("X-TRACE-Product-Activation", "FAIL-CLOSED");
  headers.set("X-TRACE-Transition-Status", "FAIL-CLOSED-NO-ACTIVE-PRODUCT-STATE-GRAPH");
  if (identity.readModelSha256) headers.set("X-TRACE-Read-Model", identity.readModelSha256);
  return headers;
}

function failure(
  code: ExplorationV3ErrorCode,
  message: string,
  status: number,
  retryable = false,
): ExplorationV3ServiceResult<never> {
  return { ok: false, code, message, status, retryable };
}

function serviceResponse<T>(
  result: ExplorationV3ServiceResult<T>,
  instance: string,
  head: boolean,
): Response {
  if (result.ok) {
    return head
      ? new NextResponse(null, { status: 200, headers: explorationV3Headers() })
      : NextResponse.json(result.data, { status: 200, headers: explorationV3Headers() });
  }
  const payload: ExplorationV3ApiError = {
    api_version: TRACE_EXPLORATION_V3_API_VERSION,
    code: result.code,
    instance,
    message: result.message,
    read_model_sha256: safeIdentity().readModelSha256,
    retryable: result.retryable ?? result.status >= 500,
    schema_version: "trace-exploration-api-error-v3",
    status: result.status,
  };
  return head
    ? new NextResponse(null, { status: result.status, headers: explorationV3Headers() })
    : NextResponse.json(payload, { status: result.status, headers: explorationV3Headers() });
}

function knownEndpoint(path: readonly string[]): boolean {
  if (path.length === 1 && path[0] === "capabilities") return true;
  if (path.length === 2 && path[0] === "baseline" && path[1] === "reconciliation") return true;
  if (path.length === 1 && isExplorationV3CollectionPath(path[0] ?? "")) return true;
  if (
    path.length === 2
    && isExplorationV3CollectionPath(path[0] ?? "")
  ) return true;
  return path[0] === "controls"
    && (
      (path.length === 2 && isExplorationV3CollectionPath(path[1] ?? ""))
      || (
        path.length === 3
        && isExplorationV3CollectionPath(path[1] ?? "")
      )
    );
}

function dispatchRead(path: readonly string[]): ExplorationV3ServiceResult<unknown> {
  if (path.length === 1 && path[0] === "capabilities") {
    return retrieveExplorationV3Capabilities();
  }
  if (path.length === 2 && path[0] === "baseline" && path[1] === "reconciliation") {
    return retrieveExplorationV3BaselineReconciliation();
  }
  const directCollection = path[0] ?? "";
  if (path.length === 1 && isExplorationV3CollectionPath(directCollection)) {
    return listExplorationV3Collection(directCollection);
  }
  if (
    path.length === 2
    && isExplorationV3CollectionPath(directCollection)
  ) {
    return retrieveExplorationV3CollectionItem(directCollection, path[1] ?? "");
  }
  const controlCollection = path[1] ?? "";
  if (
    path[0] === "controls"
    && path.length === 2
    && isExplorationV3CollectionPath(controlCollection)
  ) {
    return listExplorationV3Collection(controlCollection, true);
  }
  if (
    path[0] === "controls"
    && path.length === 3
    && isExplorationV3CollectionPath(controlCollection)
  ) {
    return retrieveExplorationV3CollectionItem(controlCollection, path[2] ?? "", true);
  }
  return failure("ENDPOINT_NOT_FOUND", "The Exploration v3 API endpoint does not exist.", 404);
}

export async function dispatchExplorationV3Request(
  request: Request,
  path: readonly string[],
): Promise<Response> {
  const instance = path.length ? `${API_INSTANCE}/${path.join("/")}` : API_INSTANCE;
  const head = request.method === "HEAD";
  try {
    if (request.method === "OPTIONS") {
      return new NextResponse(null, { status: 204, headers: explorationV3Headers() });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      const result = knownEndpoint(path)
        ? failure("METHOD_NOT_ALLOWED", "The HTTP method is not available for this read-only endpoint.", 405)
        : failure("ENDPOINT_NOT_FOUND", "The Exploration v3 API endpoint does not exist.", 404);
      return serviceResponse(result, instance, head);
    }
    return serviceResponse(dispatchRead(path), instance, head);
  } catch {
    return serviceResponse(
      failure(
        "INTERNAL_DATA_INTEGRITY_FAILURE",
        "The governed Exploration v3 read model failed closed.",
        503,
        true,
      ),
      instance,
      head,
    );
  }
}

import "server-only";

import { NextResponse } from "next/server";
import { getOpenInquiryRegistryIdentity } from "./registry.server.ts";
import {
  listOpenInquiries,
  openInquiryFailure,
  retrieveOpenInquiry,
} from "./service.server.ts";
import {
  TRACE_OPEN_INQUIRY_API_VERSION,
  TRACE_OPEN_INQUIRY_ERROR_SCHEMA_VERSION,
  TRACE_OPEN_INQUIRY_LAYER,
} from "./types.ts";
import type {
  OpenInquiryApiError,
  OpenInquiryServiceResult,
} from "./types.ts";

const API_INSTANCE = "/api/trace/v1/open-inquiry";
const ALLOWED_METHODS = "GET, HEAD, OPTIONS";

function safeRegistryIdentity(): string | null {
  try {
    return getOpenInquiryRegistryIdentity();
  } catch {
    return null;
  }
}

export function openInquiryHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  headers.set("Allow", ALLOWED_METHODS);
  headers.set("Cache-Control", "private, no-store");
  headers.set("Vary", "Accept");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-TRACE-API-Version", TRACE_OPEN_INQUIRY_API_VERSION);
  headers.set("X-TRACE-Exploration-Layer", TRACE_OPEN_INQUIRY_LAYER);
  headers.set("X-TRACE-Validated-Relation", "false");
  headers.set("X-TRACE-Default-In-Validated-Results", "false");
  const registrySha256 = safeRegistryIdentity();
  if (registrySha256) headers.set("X-TRACE-Open-Inquiry-Registry", registrySha256);
  return headers;
}

function serviceResponse<T>(
  result: OpenInquiryServiceResult<T>,
  instance: string,
  head: boolean,
): Response {
  if (result.ok) {
    return head
      ? new NextResponse(null, { status: 200, headers: openInquiryHeaders() })
      : NextResponse.json(result.data, { status: 200, headers: openInquiryHeaders() });
  }
  const payload: OpenInquiryApiError = {
    schema_version: TRACE_OPEN_INQUIRY_ERROR_SCHEMA_VERSION,
    api_version: TRACE_OPEN_INQUIRY_API_VERSION,
    layer: TRACE_OPEN_INQUIRY_LAYER,
    code: result.code,
    message: result.message,
    status: result.status,
    retryable: result.retryable ?? result.status >= 500,
    instance,
    registry_sha256: safeRegistryIdentity(),
  };
  return head
    ? new NextResponse(null, { status: result.status, headers: openInquiryHeaders() })
    : NextResponse.json(payload, { status: result.status, headers: openInquiryHeaders() });
}

function hasUnsupportedQueryParameter(request: Request): boolean {
  return new URL(request.url).searchParams.size > 0;
}

function methodNotAllowed(): OpenInquiryServiceResult<never> {
  return openInquiryFailure(
    "METHOD_NOT_ALLOWED",
    "The HTTP method is not available for this read-only endpoint.",
    405,
  );
}

function unsupportedQueryParameter(): OpenInquiryServiceResult<never> {
  return openInquiryFailure(
    "UNSUPPORTED_QUERY_PARAMETER",
    "Open Inquiry does not accept query parameters.",
    400,
  );
}

export async function dispatchOpenInquiryListRequest(request: Request): Promise<Response> {
  const head = request.method === "HEAD";
  try {
    if (request.method === "OPTIONS") {
      return new NextResponse(null, { status: 204, headers: openInquiryHeaders() });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return serviceResponse(methodNotAllowed(), API_INSTANCE, head);
    }
    getOpenInquiryRegistryIdentity();
    if (hasUnsupportedQueryParameter(request)) {
      return serviceResponse(unsupportedQueryParameter(), API_INSTANCE, head);
    }
    return serviceResponse(listOpenInquiries(), API_INSTANCE, head);
  } catch {
    return serviceResponse(
      openInquiryFailure(
        "REGISTRY_INTEGRITY_FAILURE",
        "The canonical Open Inquiry registry failed closed.",
        503,
        true,
      ),
      API_INSTANCE,
      head,
    );
  }
}

export async function dispatchOpenInquiryDetailRequest(
  request: Request,
  inquiryId: string,
): Promise<Response> {
  const instance = `${API_INSTANCE}/${encodeURIComponent(inquiryId)}`;
  const head = request.method === "HEAD";
  try {
    if (request.method === "OPTIONS") {
      return new NextResponse(null, { status: 204, headers: openInquiryHeaders() });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return serviceResponse(methodNotAllowed(), instance, head);
    }
    getOpenInquiryRegistryIdentity();
    if (hasUnsupportedQueryParameter(request)) {
      return serviceResponse(unsupportedQueryParameter(), instance, head);
    }
    return serviceResponse(retrieveOpenInquiry(inquiryId), instance, head);
  } catch {
    return serviceResponse(
      openInquiryFailure(
        "REGISTRY_INTEGRITY_FAILURE",
        "The canonical Open Inquiry registry failed closed.",
        503,
        true,
      ),
      instance,
      head,
    );
  }
}

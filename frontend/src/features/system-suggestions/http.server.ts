import "server-only";

import { checkRequestRateLimit } from "./rate-limiter.server";
import { NextResponse } from "next/server";
import { createSystemSuggestions } from "./service.server";
import { MAX_REQUEST_BYTES, parseBoundedJsonBody, SuggestionsInputError } from "./schema.server";

const ALLOW = "POST, OPTIONS";
const HEADERS = {
  Allow: ALLOW,
  "Cache-Control": "private, no-store, max-age=0",
  "Content-Type": "application/json; charset=utf-8",
  "X-Content-Type-Options": "nosniff",
};
/* surfaces whose product is not released in v49 (Spacetime, 2026-09-05):
   the service and its gate stay as frozen research infrastructure; the
   public path answers with the release boundary instead of guidance */
const DEFERRED_SURFACES: ReadonlySet<string> = new Set(["TRACE_SPACETIME"]);

function problem(code: string, detail: string, status: number, headers?: HeadersInit): Response {
  return NextResponse.json({
    type: `urn:gdarchive:problem:${code.toLowerCase().replaceAll("_", "-")}`,
    title: "System Suggestions request failed",
    status,
    code,
    detail,
  }, { status, headers: { ...HEADERS, ...headers } });
}

/* the surface named by a request body, before validation, so that a
   deferred surface answers with its release boundary whatever else the
   body carries; anything unreadable falls through to the parser's own error */
function deferredSurfaceOf(text: string): string | null {
  if (text.length > MAX_REQUEST_BYTES) return null;
  try {
    const value: unknown = JSON.parse(text);
    if (!value || typeof value !== "object") return null;
    const surface = (value as { surface?: unknown }).surface;
    return typeof surface === "string" && DEFERRED_SURFACES.has(surface) ? surface : null;
  } catch {
    return null;
  }
}

export function systemSuggestionsOptionsResponse(): Response {
  return new NextResponse(null, { status: 204, headers: HEADERS });
}

export function systemSuggestionsMethodNotAllowedResponse(): Response {
  return problem("METHOD_NOT_ALLOWED", "System Suggestions is POST/OPTIONS only", 405);
}

export async function handleSystemSuggestionsRequest(request: Request): Promise<Response> {
  const declaredLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) return problem("REQUEST_TOO_LARGE", "request body exceeds 16384 bytes", 413);
  const admission = await checkRequestRateLimit(request);
  if (admission.status === "LIMIT_REACHED") return problem("RATE_LIMITED", "Too many System Suggestions requests; retry later", 429, { "Retry-After": String(admission.retryAfter), "X-RateLimit-Remaining": String(admission.remaining) });
  try {
    const text = await request.text();
    const deferred = deferredSurfaceOf(text);
    if (deferred) return problem("SURFACE_NOT_RELEASED", `${deferred} is not released in v49`, 404);
    const parsed = parseBoundedJsonBody(text);
    const response = await createSystemSuggestions(parsed, { admission });
    return NextResponse.json(response, { headers: HEADERS });
  } catch (error) {
    if (error instanceof SuggestionsInputError) return problem(error.code, error.message, error.code === "REQUEST_TOO_LARGE" ? 413 : 400);
    return problem("UNAVAILABLE", "System Suggestions is temporarily unavailable", 503);
  }
}

export function resetSystemSuggestionsRateLimitForTest(): void {
  if (process.env.NODE_ENV === "production") throw new Error("rate-limit reset is test-only");
  // Shared counters expire naturally; tests use isolated namespaces. No global deletion.
}

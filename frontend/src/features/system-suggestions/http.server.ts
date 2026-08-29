import "server-only";

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
const WINDOW_MS = 60_000;
const MAX_REQUESTS_PER_WINDOW = 30;
const buckets = new Map<string, { startedAt: number; count: number }>();

function problem(code: string, detail: string, status: number, headers?: HeadersInit): Response {
  return NextResponse.json({
    type: `urn:gdarchive:problem:${code.toLowerCase().replaceAll("_", "-")}`,
    title: "System Suggestions request failed",
    status,
    code,
    detail,
  }, { status, headers: { ...HEADERS, ...headers } });
}

function requesterKey(request: Request): string {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || request.headers.get("x-real-ip")?.trim()
    || "local";
}

function rateAllowed(request: Request, now = Date.now()): boolean {
  const key = requesterKey(request);
  const bucket = buckets.get(key);
  if (!bucket || now - bucket.startedAt >= WINDOW_MS) {
    buckets.set(key, { startedAt: now, count: 1 });
    if (buckets.size > 2048) for (const [candidate, value] of buckets) if (now - value.startedAt >= WINDOW_MS) buckets.delete(candidate);
    return true;
  }
  bucket.count += 1;
  return bucket.count <= MAX_REQUESTS_PER_WINDOW;
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
  if (!rateAllowed(request)) return problem("RATE_LIMITED", "Too many System Suggestions requests; retry later", 429, { "Retry-After": "60" });
  try {
    const parsed = parseBoundedJsonBody(await request.text());
    const response = await createSystemSuggestions(parsed);
    return NextResponse.json(response, { headers: HEADERS });
  } catch (error) {
    if (error instanceof SuggestionsInputError) return problem(error.code, error.message, error.code === "REQUEST_TOO_LARGE" ? 413 : 400);
    return problem("UNAVAILABLE", "System Suggestions is temporarily unavailable", 503);
  }
}

export function resetSystemSuggestionsRateLimitForTest(): void {
  if (process.env.NODE_ENV === "production") throw new Error("rate-limit reset is test-only");
  buckets.clear();
}

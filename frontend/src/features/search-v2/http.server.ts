import "server-only";

import { NextResponse } from "next/server";
import { SearchInputError } from "./core";
import { publicSearchFacets, searchPublicObjects } from "./service.server";

const SEARCH_ALLOW = "GET, HEAD, OPTIONS";
const SEARCH_RESPONSE_HEADERS = {
  Allow: SEARCH_ALLOW,
  "Cache-Control": "private, no-store, max-age=0",
  "Content-Type": "application/json; charset=utf-8",
  "X-Content-Type-Options": "nosniff",
};
const ALLOWED_SEARCH_PARAMETERS = new Set(["q", "yearFrom", "yearTo", "objectType", "theme", "movement", "first", "after"]);

function problem(code: string, detail: string, status: number) {
  return NextResponse.json({
    type: `urn:gdarchive:problem:${code.toLowerCase().replaceAll("_", "-")}`,
    title: "Public Search request failed",
    status,
    code,
    detail,
  }, { status, headers: SEARCH_RESPONSE_HEADERS });
}

function integer(value: string | null, name: string): number | undefined {
  if (value === null) return undefined;
  if (!/^[0-9]+$/.test(value)) throw new SearchInputError("INVALID_ARGUMENT", `${name} must be an integer`);
  return Number(value);
}

function rejectUnsupportedParameters(parameters: URLSearchParams): void {
  for (const key of parameters.keys()) {
    if (!ALLOWED_SEARCH_PARAMETERS.has(key)) throw new SearchInputError("INVALID_ARGUMENT", `unsupported Search parameter: ${key}`);
  }
}

export function publicSearchOptionsResponse() {
  return new NextResponse(null, { status: 204, headers: SEARCH_RESPONSE_HEADERS });
}

export function publicSearchMethodNotAllowedResponse() {
  return problem("METHOD_NOT_ALLOWED", "Public Search is GET/HEAD/OPTIONS only", 405);
}

export async function handlePublicSearchRequest(request: Request): Promise<Response> {
  const head = request.method === "HEAD";
  if (request.url.length > 8192) return problem("INVALID_ARGUMENT", "Search request URL is too long", 414);
  try {
    const url = new URL(request.url);
    rejectUnsupportedParameters(url.searchParams);
    const response = searchPublicObjects({
      query: url.searchParams.get("q") ?? "",
      filters: {
        yearFrom: integer(url.searchParams.get("yearFrom"), "yearFrom"),
        yearTo: integer(url.searchParams.get("yearTo"), "yearTo"),
        objectType: url.searchParams.get("objectType") ?? undefined,
        theme: url.searchParams.get("theme") ?? undefined,
        movement: url.searchParams.get("movement") ?? undefined,
      },
      first: integer(url.searchParams.get("first"), "first"),
      after: url.searchParams.get("after") ?? undefined,
    });
    const headers = new Headers(SEARCH_RESPONSE_HEADERS);
    headers.set("Archive-Research-Release-Id", response.release.id);
    headers.set("Archive-Research-Manifest-Sha256", response.release.manifestSha256);
    headers.set("Archive-Search-Index-Sha256", response.release.searchIndexSha256);
    return head ? new NextResponse(null, { status: 200, headers }) : NextResponse.json(response, { headers });
  } catch (error) {
    if (error instanceof SearchInputError) return problem(error.code, error.message, 400);
    return problem("UNAVAILABLE", "Public Search is temporarily unavailable", 503);
  }
}

export function handlePublicSearchFacetsRequest(request: Request): Response {
  const head = request.method === "HEAD";
  const url = new URL(request.url);
  if ([...url.searchParams.keys()].length) return problem("INVALID_ARGUMENT", "Search facets do not accept query parameters", 400);
  try {
    const response = publicSearchFacets();
    const headers = new Headers(SEARCH_RESPONSE_HEADERS);
    headers.set("Archive-Research-Release-Id", response.release.id);
    headers.set("Archive-Research-Manifest-Sha256", response.release.manifestSha256);
    headers.set("Archive-Search-Index-Sha256", response.release.searchIndexSha256);
    return head ? new NextResponse(null, { status: 200, headers }) : NextResponse.json(response, { headers });
  } catch {
    return problem("UNAVAILABLE", "Public Search facets are temporarily unavailable", 503);
  }
}

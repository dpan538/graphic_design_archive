import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const SUCCESSOR = "/api/trace/v2/exploration";
const ALLOW = "GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE";

const RETIREMENT_PAYLOAD = Object.freeze({
  schema_version: "trace-exploration-api-retirement-v1",
  api_version: "trace-exploration/v1",
  code: "API_VERSION_RETIRED",
  message: "This Exploration API version is retired. Use the versioned successor.",
  status: 410,
  retryable: false,
  successor: SUCCESSOR,
});

function retirementHeaders(): Headers {
  return new Headers({
    Allow: ALLOW,
    "Cache-Control": "private, no-store",
    Link: `<${SUCCESSOR}>; rel="successor-version"`,
    Sunset: "Thu, 27 Aug 2026 00:00:00 GMT",
    "X-Content-Type-Options": "nosniff",
    "X-TRACE-API-Version": "trace-exploration/v1-retired",
  });
}

function gone(head = false): Response {
  return head
    ? new NextResponse(null, { status: 410, headers: retirementHeaders() })
    : NextResponse.json(RETIREMENT_PAYLOAD, { status: 410, headers: retirementHeaders() });
}

export function GET(): Response { return gone(); }
export function POST(): Response { return gone(); }
export function HEAD(): Response { return gone(true); }
export function OPTIONS(): Response { return gone(); }
export function PUT(): Response { return gone(); }
export const PATCH = PUT;
export const DELETE = PUT;

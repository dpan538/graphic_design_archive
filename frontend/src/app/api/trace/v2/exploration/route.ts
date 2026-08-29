import { NextResponse } from "next/server";
import {
  dispatchExplorationV2Request,
  explorationV2Headers,
} from "@/features/trace-v49/exploration-v2/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const CAPABILITIES_LOCATION = "/api/trace/v2/exploration/capabilities";

function redirectToCapabilities(): Response {
  return new NextResponse(null, {
    status: 308,
    headers: explorationV2Headers({ Location: CAPABILITIES_LOCATION }),
  });
}

export function GET(): Response {
  return redirectToCapabilities();
}

export const HEAD = GET;

export function OPTIONS(): Response {
  return new NextResponse(null, { status: 204, headers: explorationV2Headers() });
}

export function POST(request: Request): Promise<Response> {
  return dispatchExplorationV2Request(request, ["capabilities"]);
}

export const PUT = POST;
export const PATCH = POST;
export const DELETE = POST;

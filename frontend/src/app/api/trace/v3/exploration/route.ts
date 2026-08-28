import { NextResponse } from "next/server";
import {
  dispatchExplorationV3Request,
  explorationV3Headers,
} from "@/features/trace-v49/exploration-v3/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const CAPABILITIES_LOCATION = "/api/trace/v3/exploration/capabilities";

function redirectToCapabilities(): Response {
  return new NextResponse(null, {
    headers: explorationV3Headers({ Location: CAPABILITIES_LOCATION }),
    status: 308,
  });
}

export function GET(): Response {
  return redirectToCapabilities();
}

export const HEAD = GET;

export function OPTIONS(): Response {
  return new NextResponse(null, { headers: explorationV3Headers(), status: 204 });
}

export function POST(request: Request): Promise<Response> {
  return dispatchExplorationV3Request(request, ["capabilities"]);
}

export const PUT = POST;
export const PATCH = POST;
export const DELETE = POST;

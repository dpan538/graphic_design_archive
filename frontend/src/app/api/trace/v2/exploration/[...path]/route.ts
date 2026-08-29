import { NextResponse } from "next/server";
import {
  dispatchExplorationV2Request,
  explorationV2Headers,
} from "@/features/trace-v49/exploration-v2/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteParameters = { readonly params: Promise<{ readonly path: string[] }> };

export async function GET(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV2Request(request, (await route.params).path);
}

export async function POST(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV2Request(request, (await route.params).path);
}

export async function HEAD(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV2Request(request, (await route.params).path);
}

export function OPTIONS(): Response {
  return new NextResponse(null, { status: 204, headers: explorationV2Headers() });
}

export async function PUT(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV2Request(request, (await route.params).path);
}

export const PATCH = PUT;
export const DELETE = PUT;

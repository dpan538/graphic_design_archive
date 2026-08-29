import { NextResponse } from "next/server";
import {
  dispatchExplorationV3Request,
  explorationV3Headers,
} from "@/features/trace-v49/exploration-v3/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteParameters = { readonly params: Promise<{ readonly path: string[] }> };

export async function GET(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV3Request(request, (await route.params).path);
}

export async function HEAD(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV3Request(request, (await route.params).path);
}

export function OPTIONS(): Response {
  return new NextResponse(null, { headers: explorationV3Headers(), status: 204 });
}

export async function POST(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationV3Request(request, (await route.params).path);
}

export const PUT = POST;
export const PATCH = POST;
export const DELETE = POST;

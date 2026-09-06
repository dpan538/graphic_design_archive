import { dispatchExplorationViewRequest } from "@/features/trace-v49/exploration-view/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteParameters = { readonly params: Promise<{ readonly path: string[] }> };

export async function GET(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationViewRequest(request, (await route.params).path);
}

export async function POST(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationViewRequest(request, (await route.params).path);
}

export async function HEAD(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationViewRequest(request, (await route.params).path);
}

export async function OPTIONS(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationViewRequest(request, (await route.params).path);
}

export async function PUT(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchExplorationViewRequest(request, (await route.params).path);
}

export const PATCH = PUT;
export const DELETE = PUT;

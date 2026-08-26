import { NextResponse } from "next/server";
import { dispatchExplorationRequest, explorationHeaders } from "@/features/trace-v49/exploration/backend/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
type RouteContext = { readonly params: Promise<{ readonly path: string[] }> };

export async function GET(request: Request, context: RouteContext) { return dispatchExplorationRequest(request, (await context.params).path); }
export async function POST(request: Request, context: RouteContext) { return dispatchExplorationRequest(request, (await context.params).path); }
export async function HEAD(request: Request, context: RouteContext) { return dispatchExplorationRequest(request, (await context.params).path); }
export function OPTIONS() { return new NextResponse(null, { status: 204, headers: explorationHeaders() }); }
export async function PUT(request: Request, context: RouteContext) { return dispatchExplorationRequest(request, (await context.params).path); }
export const PATCH = PUT;
export const DELETE = PUT;

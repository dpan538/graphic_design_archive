import { NextResponse } from "next/server";
import { dispatchReadApiRequest, readApiHeaders, readApiMethodNotAllowedResponse } from "@/lib/read-platform/server/read-api-controller";

export const dynamic = "force-dynamic";

export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) { return dispatchReadApiRequest(request, (await context.params).path); }
export async function HEAD(request: Request, context: { params: Promise<{ path: string[] }> }) { return dispatchReadApiRequest(request, (await context.params).path); }
export function OPTIONS() { return new NextResponse(null, { status: 204, headers: readApiHeaders() }); }
export function POST() { return readApiMethodNotAllowedResponse(); }
export const PUT = POST; export const PATCH = POST; export const DELETE = POST;

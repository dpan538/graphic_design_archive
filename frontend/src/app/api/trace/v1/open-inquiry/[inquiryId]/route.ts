import { NextResponse } from "next/server";
import {
  dispatchOpenInquiryDetailRequest,
  openInquiryHeaders,
} from "@/features/trace-v49/open-inquiry-v1/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteParameters = {
  readonly params: Promise<{ readonly inquiryId: string }>;
};

export async function GET(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchOpenInquiryDetailRequest(request, (await route.params).inquiryId);
}

export async function HEAD(request: Request, route: RouteParameters): Promise<Response> {
  return dispatchOpenInquiryDetailRequest(request, (await route.params).inquiryId);
}

export function OPTIONS(): Response {
  return new NextResponse(null, { status: 204, headers: openInquiryHeaders() });
}

import { NextResponse } from "next/server";
import {
  dispatchOpenInquiryListRequest,
  openInquiryHeaders,
} from "@/features/trace-v49/open-inquiry-v1/controller.server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(request: Request): Promise<Response> {
  return dispatchOpenInquiryListRequest(request);
}

export function HEAD(request: Request): Promise<Response> {
  return dispatchOpenInquiryListRequest(request);
}

export function OPTIONS(): Response {
  return new NextResponse(null, { status: 204, headers: openInquiryHeaders() });
}

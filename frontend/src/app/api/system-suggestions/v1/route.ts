import {
  handleSystemSuggestionsRequest,
  systemSuggestionsMethodNotAllowedResponse,
  systemSuggestionsOptionsResponse,
} from "@/features/system-suggestions/http.server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request): Promise<Response> {
  return handleSystemSuggestionsRequest(request);
}

export async function OPTIONS(): Promise<Response> {
  return systemSuggestionsOptionsResponse();
}

export async function GET(): Promise<Response> {
  return systemSuggestionsMethodNotAllowedResponse();
}

export async function HEAD(): Promise<Response> {
  return systemSuggestionsMethodNotAllowedResponse();
}

export async function PUT(): Promise<Response> {
  return systemSuggestionsMethodNotAllowedResponse();
}

export async function PATCH(): Promise<Response> {
  return systemSuggestionsMethodNotAllowedResponse();
}

export async function DELETE(): Promise<Response> {
  return systemSuggestionsMethodNotAllowedResponse();
}

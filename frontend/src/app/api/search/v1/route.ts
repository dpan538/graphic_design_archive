import {
  handlePublicSearchRequest,
  publicSearchMethodNotAllowedResponse,
  publicSearchOptionsResponse,
} from "@/features/search-v2/http.server";

export const dynamic = "force-dynamic";

export const GET = handlePublicSearchRequest;
export const HEAD = handlePublicSearchRequest;
export const OPTIONS = publicSearchOptionsResponse;
export const POST = publicSearchMethodNotAllowedResponse;
export const PUT = publicSearchMethodNotAllowedResponse;
export const PATCH = publicSearchMethodNotAllowedResponse;
export const DELETE = publicSearchMethodNotAllowedResponse;

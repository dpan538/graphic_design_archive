import { NextResponse, type NextRequest } from "next/server";

// These frozen files predate current public/held eligibility. Keep the bytes
// for research/tests, but never expose them through the production HTTP server.
export function middleware(_request: NextRequest) {
  if (process.env.NODE_ENV !== "production") return NextResponse.next();
  return new NextResponse("Not found", { status: 404, headers: {
    "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
  } });
}

export const config = {
  matcher: ["/data/trace-v48/:path*", "/data/public_surface_mock_v0.json"],
};

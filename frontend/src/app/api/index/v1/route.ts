import { NextResponse } from "next/server";
import { getCataloguePayload } from "@/app/directory/lib/catalogue.server";

/* GET /api/index/v1 — the Index directory's catalogue: every public record
   of the sealed release, as one compact payload. Read-only; bound to the
   release the Search v2 artifact was built for. */

export const dynamic = "force-static";

export function GET() {
  const { payload, etag } = getCataloguePayload();
  return NextResponse.json(payload, {
    headers: {
      "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
      ETag: `"${etag}"`,
      "X-Archive-Release": payload.releaseId,
    },
  });
}

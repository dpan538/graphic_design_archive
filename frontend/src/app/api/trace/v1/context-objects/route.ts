import { NextResponse } from "next/server";
import { searchGovernedContextObjects } from "@/features/trace-v49/context/governed/index.server";

/* /api/trace/v1/context-objects?q= — the Context Canvas object chooser's
   search (FRONTEND_DESIGN_DECISION.md §7g). Words find reader-facing
   titles (folded: case and diacritics do not matter); a public record ID
   or its prefix finds any governed public record. Reads the sealed v49
   governed Context projection through its reader; never the data itself. */

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const url = new URL(request.url);
  const query = (url.searchParams.get("q") ?? "").slice(0, 80);
  const results = searchGovernedContextObjects(query, 8).map((entry) => ({
    stableId: entry.stableId,
    title: entry.title,
    readerFacing: entry.readerFacing,
    contexts: entry.counts.medium + entry.counts.theme + entry.counts.movement_context,
  }));
  return NextResponse.json({ query, results }, { headers: { "Cache-Control": "no-store" } });
}

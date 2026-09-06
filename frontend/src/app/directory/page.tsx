import { getPublicSearchIndex } from "@/features/search-v2/index.server";
import { readerEligibilityOf } from "@/features/reader-eligibility/index.server";
import type { Metadata } from "next";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import IndexDesktop from "./desktop/IndexDesktop";
import IndexMobile from "./mobile/IndexMobile";

export const metadata: Metadata = {
  alternates: { canonical: "/directory" },
  openGraph: { url: "/directory", type: "website" },
  title: "Index",
  description:
    "Browse the archive as a filterable directory: region, year and theme, ordered by year, down to the object record.",
};

/* Server-side device split (§4a): the User-Agent (or a ?view=mobile|desktop
   override) picks the desktop/ or mobile/ tree — they share only lib/. Both
   trees load the catalogue of reader-facing objects from /api/index/v1 (the
   sealed v49 projection, §3b); verified structured geography is still pending
   (FRONTEND_DESIGN_DECISION.md §3), so places are the source-recorded labels. */
export default async function IndexPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));

  return <>{view === "mobile" ? <IndexMobile /> : <IndexDesktop />}<noscript><section aria-label="Index reading without JavaScript"><h2>Public object directory</h2><p>Index browses reader-facing objects. Search supports exact public record-only identifiers. Interactive filters require JavaScript; public object records and source explanations remain readable.</p><p><a href="/source">Sources and methods</a> · <a href="/read-api">Public reading API</a></p><ul>{getPublicSearchIndex().documents.filter(d => readerEligibilityOf(d.stableId) === "INDEX_ELIGIBLE").slice(0, 20).map(d => <li key={d.stableId}><a href={`/surfaces/${d.stableId}`}>{d.title}</a></li>)}</ul></section></noscript></>;
}

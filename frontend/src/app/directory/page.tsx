import type { Metadata } from "next";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import IndexDesktop from "./desktop/IndexDesktop";
import IndexMobile from "./mobile/IndexMobile";

export const metadata: Metadata = {
  title: "Index",
  description:
    "Browse the archive as a filterable directory: region, year and theme, ordered by year, down to the object record.",
};

/* Design exploration. Server-side device split (§4a): the User-Agent (or a
   ?view=mobile|desktop override) picks the desktop/ or mobile/ tree — they share
   only lib/. The live Index API and verified structured geography are not built
   yet (FRONTEND_DESIGN_DECISION.md §3); both trees render the fixture directory. */
export default async function IndexPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));

  return view === "mobile" ? <IndexMobile /> : <IndexDesktop />;
}

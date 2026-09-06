import type { Metadata } from "next";
import { Suspense } from "react";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import SearchDesktop from "./desktop/SearchDesktop";
import SearchMobile from "./mobile/SearchMobile";

export const metadata: Metadata = {
  robots: { index: false, follow: true },
  alternates: { canonical: "/search" },
  title: "Search — Modern Graphic Design Archive",
  description:
    "A global Search window: find one public archive object by query, year, object type, theme or movement. URL-backed state; text and citation only, no assumed imagery.",
};

/* Search is a global utility window (§7d), URL-backed at /search. Server device
   split (§4a): the User-Agent (or ?view=) picks the desktop catalogue-card or
   the mobile ticket treatment; they share lib/ and the live public Search / guidance APIs. */
export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));

  return (
    <Suspense fallback={null}>
      {view === "mobile" ? <SearchMobile /> : <SearchDesktop />}
    </Suspense>
  );
}

import type { Metadata } from "next";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import HomeDesktop from "./home/desktop/HomeDesktop";
import HomeMobile from "./home/mobile/HomeMobile";

export const metadata: Metadata = {
  title: "Modern Graphic Design Archive",
  description:
    "A digital humanities research archive for modern graphic design history — verified records, explicit provenance, and evidence-bounded computational research.",
};

/* Homepage (§7e) — a reading page. Server device split (§4a): the User-Agent
   (or ?view=) picks the scroll-choreographed desktop page or the pared-back
   mobile stack. Copy is final per §2a / §7e; no API. */
export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));

  return view === "mobile" ? <HomeMobile /> : <HomeDesktop />;
}

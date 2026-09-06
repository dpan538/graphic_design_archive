import type { Metadata } from "next";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import AboutView from "./AboutView";
import AboutMobile from "./mobile/AboutMobile";

export const metadata: Metadata = {
  title: "About & Methodology",
  description:
    "Project identity, archive and design research methodology, visual-design references, claim boundaries, and how to cite the Modern Graphic Design Archive.",
};

/* Server device split (§4a): the User-Agent (or ?view=) picks the desktop
   sheet or the mobile tree; never both, never a client swap. */
export default async function AboutPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));
  return view === "mobile" ? <AboutMobile /> : <AboutView />;
}

import type { Metadata } from "next";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import AboutMobile from "../about/mobile/AboutMobile";
import SourceView from "./SourceView";

export const metadata: Metadata = {
  title: "Source",
  description:
    "Provenance, acquisition status, rights conditions, transformation record, evidence status, and reproducibility for the materials incorporated into Modern Graphic Design Archive.",
};

/* Server device split (§4a): on the phone Source lives inside About, so the
   mobile path renders the About tree opened at its Source section. */
export default async function SourcePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const [sp, hdrs] = await Promise.all([searchParams, headers()]);
  const view = resolveView(sp.view, hdrs.get("user-agent"));
  return view === "mobile" ? <AboutMobile focus="source" /> : <SourceView />;
}

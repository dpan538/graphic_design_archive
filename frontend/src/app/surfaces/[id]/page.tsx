import { safeJsonLd, site } from "@/features/machine-reading/project";
import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { resolveView } from "@/lib/device";
import { getPublicSearchIndex } from "@/features/search-v2/index.server";
import { readerEligibilityOf } from "@/features/reader-eligibility/index.server";
import { sourceViewerOf } from "@/features/source-viewer/index.server";
import { visualRegistryEntryOf } from "@/features/visual-registry/index.server";
import { recordFromDocument } from "./lib/fromDocument";
import ObjectDesktop from "./desktop/ObjectDesktop";
import ObjectMobile from "./mobile/ObjectMobile";

/* Object record — one public surface of the sealed v49 release, read from
   the governed Search v2 projection on the server. Server-side device split
   (§4a): the User-Agent (or a ?view=mobile|desktop override) picks the
   desktop/ or the mobile/ tree; both render the same record. An ID outside
   the public projection is a 404 — never a substitute record. A RECORD-ONLY
   entry (reader-eligibility projection) renders as an archive record —
   identity, catalogue metadata, source, citation, provenance — with no
   visual or descriptive layers pretending to be there. */

type Params = Promise<{ id: string }>;

function lookup(id: string) {
  const index = getPublicSearchIndex();
  return index.byId.get(id) ?? index.byId.get(decodeURIComponent(id).toUpperCase()) ?? null;
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  const doc = lookup(id);
  if (!doc) return { title: "Object record" };
  const parts = [doc.creditedLabel, doc.displayDate, doc.place].filter(Boolean).join(" · ");
  return {
    title: doc.title,
    alternates: { canonical: `/surfaces/${encodeURIComponent(doc.stableId)}` },
    robots: { index: readerEligibilityOf(doc.stableId) === "INDEX_ELIGIBLE", follow: true },
    description: `${doc.objectType}${parts ? " · " + parts : ""}. Source: ${doc.sourceLabel}. Record ${doc.stableId}.`,
  };
}

export default async function SurfacePage({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ id }, sp, hdrs] = await Promise.all([params, searchParams, headers()]);
  const doc = lookup(id);
  if (!doc) notFound();
  const rec = recordFromDocument(doc, sourceViewerOf(doc.stableId), visualRegistryEntryOf(doc.stableId));
  const recordOnly = readerEligibilityOf(doc.stableId) === "RECORD_ONLY";
  const view = resolveView(sp.view, hdrs.get("user-agent"));

  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: safeJsonLd({ "@context": "https://schema.org", "@type": "WebPage", url: `${site}/surfaces/${encodeURIComponent(doc.stableId)}`, name: doc.title, identifier: doc.stableId, description: `${doc.objectType} · ${doc.displayDate}. Source: ${doc.sourceLabel}.`, isPartOf: { "@id": `${site}/#website` } }) }} />{view === "mobile" ? <ObjectMobile rec={rec} recordOnly={recordOnly} /> : <ObjectDesktop rec={rec} recordOnly={recordOnly} />}</>;
}

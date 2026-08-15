import { notFound } from "next/navigation";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { FolderDetailReadSlice } from "@/components/archive/read-platform/ReadPlatformViews";
import { openCurrentReadRepository } from "@/lib/read-platform/server/open-read-repository";

// Large regional folders can contain thousands of reader leaves. Resolve the
// requested folder on demand so a UI-only release does not paginate every
// research folder during the production build.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ type: string; slug: string }>;
}) {
  const { type, slug } = await params;
  return { title: `${slug} — Archive Box` };
}

export default async function FolderReaderPage({
  params,
}: {
  params: Promise<{ type: string; slug: string }>;
}) {
  const { type, slug } = await params;
  const repository = await openCurrentReadRepository();
  const result = await repository.getFolder({ type, slug });
  if (!result.ok) notFound();
  return <ArchiveShell activeNav="folders" mainScroll main={<FolderDetailReadSlice folder={result.data} />} />;
}

import { notFound } from "next/navigation";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { SurfaceReadSlice } from "@/components/archive/read-platform/ReadPlatformViews";
import { openCurrentReadRepository } from "@/lib/read-platform/server/open-read-repository";

// The archive currently exposes 8,636 reading routes. Rendering the selected
// record on demand keeps those stable URLs without rebuilding every object for
// each interface-only release. The application already requires a server for
// its evidence routes, so this does not remove an existing static-only target.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return { title: `${id} — Archive Box` };
}

export default async function SurfaceReaderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const repository = await openCurrentReadRepository();
  const result = await repository.getSurface(id);
  if (!result.ok) notFound();
  return <ArchiveShell activeNav="folders" mainScroll main={<SurfaceReadSlice surface={result.data} />} />;
}

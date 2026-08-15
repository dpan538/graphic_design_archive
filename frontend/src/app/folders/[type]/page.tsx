import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { FolderReadSlice } from "@/components/archive/read-platform/ReadPlatformViews";
import { openCurrentReadRepository } from "@/lib/read-platform/server/open-read-repository";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type } = await params;
  return { title: `${type} folders — Archive Box` };
}

export default async function FolderTypePage({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type } = await params;
  const repository = await openCurrentReadRepository();
  const result = await repository.listFolders({ type });
  if (!result.ok) throw new Error(result.error.message);

  return (
    <ArchiveShell
      activeNav="folders"
      main={<FolderReadSlice type={type} folders={result.data.nodes} />}
    />
  );
}

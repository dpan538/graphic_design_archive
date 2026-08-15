import Link from "next/link";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";

export default function NotFound() {
  const main = (
    <div className="flex-1 min-h-0 flex items-center justify-center p-6">
      <div className="border-[1.5px] border-ink bg-paper p-8 text-center max-w-md">
        <span className="border border-ink px-2 py-0.5 text-xs tracking-widest">
          404 · NOT IN BOX
        </span>
        <h1 className="font-bold text-2xl mt-4">No such folder or surface</h1>
        <p className="text-sm text-ink-soft mt-2">
          This coordinate is not part of the selected sealed release.
        </p>
        <Link
          href="/"
          className="inline-block mt-4 border border-ink bg-ink text-paper px-4 py-1.5 text-sm tracking-widest"
        >
          RETURN TO BOX
        </Link>
      </div>
    </div>
  );
  return <ArchiveShell main={main} activeNav="index" />;
}

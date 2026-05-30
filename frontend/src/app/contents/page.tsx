import Link from "next/link";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import TocNav from "@/components/archive/shell/TocNav";
import { TypeSwatch } from "@/components/archive/primitives";
import {
  dateSpanLabel,
  getFolderTypes,
  getFoldersByType,
  getSurfacesForFolder,
  sortChronologically,
} from "@/lib/archive-data";

export const metadata = {
  title: "Index — Modern Graphic Design History",
  description:
    "Full table of contents for the rights-aware graphic design history archive: folder types, folders, and every staged surface.",
};

/**
 * Full Table of Contents — two-column layout.
 * Left: sticky TocNav quick-jump card.
 * Right: scrollable hierarchical TOC.
 */
export default function IndexPage() {
  const types = getFolderTypes();

  const main = (
    <div className="toc-shell">
      {/* ── Left sticky sidebar ── */}
      <aside className="toc-sidebar">
        <TocNav />
      </aside>

      {/* ── Main TOC ── */}
      <div className="toc">
        <header>
          <p className="label-caps text-ink-soft">Index · January 2026</p>
          <h1 className="mt-1">Modern Graphic Design<br />History</h1>
          <p className="mt-3" style={{ fontSize: "0.78rem", lineHeight: 1.6, maxWidth: "30rem" }}>
            A rights-aware archive index. Organised into four folder types; each
            folder is a filter view — the same surface may appear in several folders.
            Entries are listed chronologically and link to their loose-leaf pages.
          </p>
        </header>

        <div className="mt-6">
          {types.map((ft, ti) => {
            const folders = getFoldersByType(ft.type);
            return (
              <section key={ft.type} id={`toc-${ft.type}`} className="toc__sect">
                <div className="toc__secthead">
                  <span className="inline-flex items-center gap-2">
                    <TypeSwatch type={ft.type} />
                    {ti + 1} · {ft.label}
                  </span>
                  <p
                    className="mt-1 font-normal normal-case tracking-normal text-ink-soft"
                    style={{ fontSize: "0.62rem", lineHeight: 1.45 }}
                  >
                    {ft.scopeNote}
                  </p>
                </div>

                <div>
                  {folders.map((folder, fi) => {
                    const surfaces = sortChronologically(
                      getSurfacesForFolder(folder),
                    );
                    return (
                      <div key={folder.folderId} id={`folder-${folder.folderId}`} className="mb-3">
                        <div className="toc__entry">
                          <Link
                            href={`/folders/${folder.type}/${folder.slug}`}
                            className="font-bold"
                          >
                            {ti + 1}.{fi + 1} {folder.title}
                          </Link>
                          <span className="lead" aria-hidden />
                          <span className="ref">
                            {dateSpanLabel(folder.dateStart, folder.dateEnd)} ·{" "}
                            {surfaces.length}
                          </span>
                        </div>
                        <ul className="mt-0.5 ml-3">
                          {surfaces.map((su) => (
                            <li key={su.surfaceId} className="toc__entry">
                              <Link
                                href={`/surfaces/${su.surfaceId}?folder=${folder.folderId}`}
                              >
                                {su.title}
                              </Link>
                              <span className="lead" aria-hidden />
                              <span className="ref">
                                {su.dateText} · {su.provisionalDisplayNumber}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );

  return <ArchiveShell main={main} activeNav="index" mainScroll />;
}

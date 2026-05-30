"use client";

import Link from "next/link";
import { getFolderTypes, getFolderInk } from "@/lib/archive-data";

/**
 * Left fixed index card on the /contents page.
 * It deliberately shows only the four public folder axes; the table contents
 * live in the main sheet, not in this navigation card.
 */
export default function TocNav() {
  const types = getFolderTypes();
  return (
    <nav className="toc-nav" aria-label="Quick navigation">
      <div className="toc-nav__head">Index</div>
      {types.map((ft) => {
        return (
          <div key={ft.type} className="toc-nav__group">
            <Link href={`/contents#toc-${ft.type}`} className="toc-nav__type">
              <span
                className="inline-block w-2 h-2 shrink-0"
                style={{ backgroundColor: getFolderInk(ft.type) }}
                aria-hidden
              />
              {ft.label}
            </Link>
          </div>
        );
      })}
    </nav>
  );
}

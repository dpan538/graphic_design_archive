"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { fuzzySearchSurfaces } from "@/lib/archive-data";
import { ImgBadge, StatusChip } from "../primitives";

/**
 * In-shell fuzzy search. Lives on the right (same width as the counts card),
 * not on a separate page. Deterministic, local-only (substring + subsequence).
 */
export default function SearchBox({ onClose }: { onClose?: () => void }) {
  const [query, setQuery] = useState("");
  const results = useMemo(() => fuzzySearchSurfaces(query), [query]);
  const trimmed = query.trim();

  return (
    <div
      className="corner-card flex flex-col"
      style={{ maxHeight: "inherit", overflow: "hidden" }}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="label-caps">Search</span>
        <button
          type="button"
          onClick={onClose}
          className="label-caps text-ink-soft hover:text-ink"
          aria-label="Close search"
        >
          close ×
        </button>
      </div>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="title, creator, source…"
        className="w-full bg-paper border-[1.5px] border-ink px-2 py-1.5 font-mono text-sm outline-none focus:bg-paper-2"
        autoComplete="off"
        // eslint-disable-next-line jsx-a11y/no-autofocus
        autoFocus
      />
      <div className="text-ink-soft mt-1.5" style={{ fontSize: "0.56rem" }}>
        {trimmed === ""
          ? "Fuzzy match over titles, creators, sources & tables"
          : `${results.length} ${results.length === 1 ? "match" : "matches"}`}
      </div>

      <div className="mt-1.5 -mx-1 px-1 overflow-y-auto panel-scroll flex-1 min-h-0">
        {trimmed !== "" && results.length === 0 ? (
          <p className="text-ink-soft py-2" style={{ fontSize: "0.66rem" }}>
            No matches for “{trimmed}”.
          </p>
        ) : (
          results.slice(0, 30).map(({ surface, field, snippet }) => (
            <Link
              key={surface.surfaceId}
              href={`/surfaces/${surface.surfaceId}`}
              className="block border-t border-line-soft py-1.5 hover:bg-paper-2"
            >
              <div className="flex items-center gap-2" style={{ fontSize: "0.56rem" }}>
                <StatusChip kind={surface.surfaceType} />
                <ImgBadge state={surface.image.state} />
                <span className="text-ink-soft">{surface.dateText}</span>
              </div>
              <div className="font-bold leading-tight" style={{ fontSize: "0.74rem" }}>
                {surface.title}
              </div>
              <div className="text-ink-soft" style={{ fontSize: "0.58rem" }}>
                <span className="label-caps">{field}</span> · {snippet}
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}

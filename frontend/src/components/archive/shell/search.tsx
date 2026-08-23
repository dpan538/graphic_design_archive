"use client";

import Link from "next/link";

/** Compact entry point only. Results come from the exact v49 Read API on explicit submit. */
export default function SearchBox({ onClose }: { onClose?: () => void }) {
  return (
    <div id="archive-search-panel" className="corner-card search-card flex flex-col" role="search">
      <div className="search-card__head">
        <span className="label-caps">Search</span>
        <button type="button" onClick={onClose} className="label-caps text-ink-soft hover:text-ink" aria-label="Close search">
          close ×
        </button>
      </div>
      <form action="/search" method="get">
        <label className="sr-only" htmlFor="shell-search-query">Search public v49 titles and stable IDs</label>
        <input
          id="shell-search-query"
          name="q"
          type="search"
          placeholder="title or stable ID"
          className="w-full bg-paper border-[1.5px] border-ink px-2 py-1.5 font-mono text-sm outline-none focus:bg-paper-2"
          autoComplete="off"
          autoFocus
        />
        <button type="submit" className="w-full border border-ink bg-ink text-paper px-2 py-1.5 mt-2 label-caps">
          Search public release →
        </button>
      </form>
      <p className="text-ink-soft mt-2" style={{ fontSize: "0.6rem" }}>
        Deterministic matching tolerates case, punctuation, partial titles, and bounded spelling errors.
      </p>
      <Link href="/search" className="block border-t border-ink pt-2 mt-2 label-caps text-ink hover:bg-paper-2" style={{ fontSize: "0.6rem" }}>
        Open search workspace →
      </Link>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import SearchBox from "./search";

/**
 * Fixed, non-scrolling viewport. No sidebar column and no top/bottom bar.
 * Navigation is a set of large floating icons (top-right): Index / Folders /
 * Search (+ Contents on the reader). Search expands in the corner-stack.
 * An optional panel (reader contents) slides in; clicking the main area or
 * pressing Backspace closes it. Left-edge swipe or Backspace goes back.
 */
export default function ArchiveShell({
  main,
  activeNav,
  cornerCard,
  panel,
  panelLabel = "Contents",
  folderInk = "#19150f",
  mainScroll = false,
  hideWordmark = false,
}: {
  main: React.ReactNode;
  activeNav?: "index" | "folders" | "search";
  cornerCard?: React.ReactNode;
  panel?: React.ReactNode;
  panelLabel?: string;
  folderInk?: string;
  mainScroll?: boolean;
  /** Hide the top-left wordmark (e.g. in spread mode where space is tight). */
  hideWordmark?: boolean;
}) {
  const router = useRouter();
  const [panelOpen, setPanelOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchFrame, setSearchFrame] = useState<{
    top: number;
    maxHeight: number;
  } | null>(null);
  const touch = useRef<{ x: number; y: number; edge: boolean } | null>(null);
  const searchButtonRef = useRef<HTMLButtonElement | null>(null);
  const searchPanelRef = useRef<HTMLDivElement | null>(null);
  const countCardRef = useRef<HTMLDivElement | null>(null);

  // Left-edge swipe → back. Backspace also goes back.
  useEffect(() => {
    const onStart = (e: TouchEvent) => {
      const t = e.touches[0];
      touch.current = { x: t.clientX, y: t.clientY, edge: t.clientX < 44 };
    };
    const onEnd = (e: TouchEvent) => {
      const s = touch.current;
      touch.current = null;
      if (!s || !s.edge) return;
      const t = e.changedTouches[0];
      if (t.clientX - s.x > 70 && Math.abs(t.clientY - s.y) < 70) {
        router.back();
      }
    };
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (e.key === "Backspace" && tag !== "INPUT" && tag !== "TEXTAREA") {
        e.preventDefault();
        router.back();
      }
    };
    window.addEventListener("touchstart", onStart, { passive: true });
    window.addEventListener("touchend", onEnd, { passive: true });
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("touchstart", onStart);
      window.removeEventListener("touchend", onEnd);
      window.removeEventListener("keydown", onKey);
    };
  }, [router]);

  useEffect(() => {
    if (!searchOpen) {
      setSearchFrame(null);
      return;
    }

    let frame = 0;
    const update = () => {
      const button = searchButtonRef.current;
      if (!button) return;
      const icon = button.getBoundingClientRect();
      const rootSize =
        Number.parseFloat(
          window.getComputedStyle(document.documentElement).fontSize,
        ) || 16;
      const gap = rootSize * 2.5;
      const countTop =
        countCardRef.current?.getBoundingClientRect().top ??
        window.innerHeight - 18;
      const top = Math.round(icon.bottom + gap);
      const maxHeight = Math.max(160, Math.round(countTop - gap - top));
      setSearchFrame({ top, maxHeight });
    };

    const schedule = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(update);
    };

    schedule();
    window.addEventListener("resize", schedule);
    const observer = new ResizeObserver(schedule);
    if (countCardRef.current) observer.observe(countCardRef.current);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", schedule);
      observer.disconnect();
    };
  }, [searchOpen, cornerCard]);

  return (
    <div className="app" style={{ ["--folder-color" as string]: folderInk }}>
      {/* Clicking the main area closes any open panel */}
      <div
        className={`app__main ${mainScroll ? "app__main--scroll" : ""}`}
        onClick={() => {
          if (panelOpen) setPanelOpen(false);
        }}
      >
        {main}
      </div>

      {!hideWordmark && (
        <Link href="/" className="wordmark">
          <div className="label-caps text-ink-soft">Archive Box</div>
          <div className="font-bold text-sm leading-tight">
            Modern Graphic Design History
          </div>
        </Link>
      )}

      <nav className="nav-icons" aria-label="Archive navigation">
        <Link
          href="/contents"
          className="nav-icon"
          data-active={activeNav === "index"}
          aria-label="Index"
        >
          <IconIndex />
          <span>Index</span>
        </Link>
        <Link
          href="/folders"
          className="nav-icon"
          data-active={activeNav === "folders"}
          aria-label="Folders"
        >
          <IconFolder />
          <span>Folders</span>
        </Link>
        <button
          ref={searchButtonRef}
          type="button"
          className="nav-icon"
          data-active={searchOpen}
          aria-label="Search"
          onClick={() => setSearchOpen((v) => !v)}
        >
          <IconSearch />
          <span>Search</span>
        </button>
        {panel ? (
          <button
            type="button"
            className="nav-icon"
            data-active={panelOpen}
            aria-label={panelLabel}
            onClick={() => setPanelOpen((v) => !v)}
          >
            <IconContents />
            <span>{panelOpen ? "Close" : panelLabel}</span>
          </button>
        ) : null}
      </nav>

      {searchOpen ? (
        <div
          ref={searchPanelRef}
          className={`search-stack ${panel ? "search-stack--reader" : ""}`}
          style={
            searchFrame === null
              ? undefined
              : {
                  top: `${searchFrame.top}px`,
                  maxHeight: `${searchFrame.maxHeight}px`,
                }
          }
        >
          <SearchBox onClose={() => setSearchOpen(false)} />
        </div>
      ) : null}

      {cornerCard ? (
        <div
          ref={countCardRef}
          className={`corner-stack ${panel ? "corner-stack--reader" : ""}`}
        >
          <div className="corner-card">{cornerCard}</div>
        </div>
      ) : null}

      {panel && panelOpen ? (
        <aside className="panel-overlay" onClick={(e) => e.stopPropagation()}>
          {panel}
        </aside>
      ) : null}
    </div>
  );
}

// ---- icons (1-bit line art) --------------------------------------------

function IconIndex() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="4" y="3" width="16" height="18" />
      <line x1="8" y1="7" x2="16" y2="7" />
      <line x1="8" y1="11" x2="16" y2="11" />
      <line x1="8" y1="15" x2="13" y2="15" />
    </svg>
  );
}

function IconFolder() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 6h6l2 2h10v11H3z" />
    </svg>
  );
}

function IconSearch() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="10.5" cy="10.5" r="6.5" />
      <line x1="15.5" y1="15.5" x2="21" y2="21" strokeWidth="2" />
    </svg>
  );
}

function IconContents() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <line x1="4" y1="6" x2="20" y2="6" />
      <line x1="4" y1="12" x2="20" y2="12" />
      <line x1="4" y1="18" x2="20" y2="18" />
    </svg>
  );
}

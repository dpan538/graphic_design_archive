"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import SearchBox, { type AssistantContext, type SearchMode } from "./search";

/**
 * Fixed, non-scrolling viewport. No sidebar column and no top/bottom bar.
 * Navigation is a set of large floating icons (top-right): Index / Folders /
 * Search. Search expands in the corner-stack. Reader-specific structure can
 * sit on the left; assistant mode shares the search window.
 */
export default function ArchiveShell({
  main,
  activeNav,
  cornerCard,
  panel,
  panelLabel = "Contents",
  leftPanel,
  leftPanelLabel = "Content",
  leftPanelSecondary,
  leftPanelSecondaryLabel = "Context",
  contextOverlay,
  contextOverlayOpen = false,
  onContextOverlayOpenChange,
  contextOverlayLabel = "Context",
  rightPanel,
  rightPanelOpen = false,
  onRightPanelOpenChange,
  folderInk = "#2E2925",
  mainScroll = false,
  hideWordmark = false,
}: {
  main: React.ReactNode;
  activeNav?: "index" | "folders" | "search" | "about";
  cornerCard?: React.ReactNode;
  /** Legacy right-side contextual panel. Prefer leftPanel/rightPanel. */
  panel?: React.ReactNode;
  panelLabel?: string;
  leftPanel?: React.ReactNode;
  leftPanelLabel?: string;
  leftPanelSecondary?: React.ReactNode;
  leftPanelSecondaryLabel?: string;
  contextOverlay?: React.ReactNode;
  contextOverlayOpen?: boolean;
  onContextOverlayOpenChange?: (open: boolean) => void;
  contextOverlayLabel?: string;
  rightPanel?: React.ReactNode;
  rightPanelOpen?: boolean;
  onRightPanelOpenChange?: (open: boolean) => void;
  folderInk?: string;
  mainScroll?: boolean;
  /** Hide the top-left wordmark for dense reader variants. */
  hideWordmark?: boolean;
}) {
  const router = useRouter();
  const [panelOpen, setPanelOpen] = useState(false);
  const [leftPanelOpen, setLeftPanelOpen] = useState(false);
  const [leftPanelMode, setLeftPanelMode] = useState<"primary" | "secondary">("primary");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchMode, setSearchMode] = useState<SearchMode>("search");
  const [assistantContext, setAssistantContext] =
    useState<AssistantContext | null>(null);
  const [searchFrame, setSearchFrame] = useState<{
    top: number;
    maxHeight: number;
  } | null>(null);
  const touch = useRef<{ x: number; y: number; edge: boolean } | null>(null);
  const searchButtonRef = useRef<HTMLButtonElement | null>(null);
  const searchPanelRef = useRef<HTMLDivElement | null>(null);
  const countCardRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const openAssistant = (event: Event) => {
      const detail = (event as CustomEvent<AssistantContext>).detail ?? null;
      if (searchOpen && searchMode === "assistant") {
        setSearchOpen(false);
        return;
      }
      setAssistantContext(detail);
      setSearchMode("assistant");
      setLeftPanelOpen(false);
      setPanelOpen(false);
      onContextOverlayOpenChange?.(false);
      onRightPanelOpenChange?.(false);
      setSearchOpen(true);
    };
    window.addEventListener("archive:open-assistant", openAssistant);
    return () => {
      window.removeEventListener("archive:open-assistant", openAssistant);
    };
  }, [onContextOverlayOpenChange, onRightPanelOpenChange, searchMode, searchOpen]);

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
      const pageTurnTop =
        document.querySelector<HTMLElement>(".page-turn")?.getBoundingClientRect()
          .top;
      const countTop =
        countCardRef.current?.getBoundingClientRect().top ??
        pageTurnTop ??
        window.innerHeight - 18;
      const top = Math.round(icon.bottom + gap);
      const availableHeight = Math.round(countTop - gap - top);
      const maxHeight = Math.max(72, availableHeight);
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
          if (leftPanelOpen) setLeftPanelOpen(false);
          if (contextOverlayOpen) onContextOverlayOpenChange?.(false);
          if (rightPanelOpen) onRightPanelOpenChange?.(false);
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

      {leftPanel ? (
        <div className="left-panel-triggers" aria-label="Left panel controls">
          <button
            type="button"
            className="nav-icon left-panel-trigger"
            data-active={leftPanelOpen && leftPanelMode === "primary"}
            aria-label={leftPanelLabel}
            onClick={() => {
              if (leftPanelOpen && leftPanelMode === "primary") {
                setLeftPanelOpen(false);
                return;
              }
              setLeftPanelMode("primary");
              setSearchOpen(false);
              setPanelOpen(false);
              setLeftPanelOpen(true);
            }}
          >
            <IconTree />
            <span>{leftPanelOpen && leftPanelMode === "primary" ? "Close" : leftPanelLabel}</span>
          </button>
          {leftPanelSecondary ? (
            <button
              type="button"
              className="nav-icon left-panel-trigger"
              data-active={leftPanelOpen && leftPanelMode === "secondary"}
              aria-label={leftPanelSecondaryLabel}
              onClick={() => {
                if (leftPanelOpen && leftPanelMode === "secondary") {
                  setLeftPanelOpen(false);
                  return;
                }
                setLeftPanelMode("secondary");
                setSearchOpen(false);
                setPanelOpen(false);
                setLeftPanelOpen(true);
              }}
            >
              <IconContext />
              <span>
                {leftPanelOpen && leftPanelMode === "secondary"
                  ? "Close"
                  : leftPanelSecondaryLabel}
              </span>
            </button>
          ) : null}
          {contextOverlay ? (
            <button
              type="button"
              className="nav-icon left-panel-trigger"
              data-active={contextOverlayOpen}
              aria-label={contextOverlayLabel}
              onClick={() => {
                setLeftPanelOpen(false);
                setSearchOpen(false);
                setPanelOpen(false);
                onRightPanelOpenChange?.(false);
                onContextOverlayOpenChange?.(!contextOverlayOpen);
              }}
            >
              <IconContext />
              <span>{contextOverlayOpen ? "Close" : contextOverlayLabel}</span>
            </button>
          ) : null}
        </div>
      ) : null}

      <nav className="nav-icons" aria-label="Archive navigation">
        {activeNav === "about" ? (
          <Link
            href="/contents"
            className="nav-icon"
            data-active={false}
            aria-label="Index"
          >
            <IconIndex />
            <span>Index</span>
          </Link>
        ) : activeNav === "index" ? (
          <Link
            href="/about"
            className="nav-icon"
            data-active={false}
            aria-label="About"
          >
            <IconAbout />
            <span>About</span>
          </Link>
        ) : (
          <div className="nav-icons__row">
            <Link
              href="/about"
              className="nav-icon"
              data-active={false}
              aria-label="About"
            >
              <IconAbout />
              <span>About</span>
            </Link>
            <Link
              href="/contents"
              className="nav-icon"
              data-active={false}
              aria-label="Index"
            >
              <IconIndex />
              <span>Index</span>
            </Link>
          </div>
        )}
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
          data-active={searchOpen && searchMode === "search"}
          aria-label="Search"
          onClick={() => {
            setSearchMode("search");
            setLeftPanelOpen(false);
            setPanelOpen(false);
            onContextOverlayOpenChange?.(false);
            setSearchOpen((v) => (searchMode === "search" ? !v : true));
          }}
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
            onClick={() => {
              setSearchOpen(false);
              setLeftPanelOpen(false);
              onContextOverlayOpenChange?.(false);
              setPanelOpen((v) => !v);
            }}
          >
            <IconContents />
            <span>{panelOpen ? "Close" : panelLabel}</span>
          </button>
        ) : null}
      </nav>

      {searchOpen ? (
        <div
          ref={searchPanelRef}
          className={`search-stack ${panel || leftPanel || rightPanel ? "search-stack--reader" : ""}`}
          style={
            searchFrame === null
              ? undefined
              : {
                  top: `${searchFrame.top}px`,
                  maxHeight: `${searchFrame.maxHeight}px`,
                  height: `${searchFrame.maxHeight}px`,
                }
          }
        >
          <SearchBox
            mode={searchMode}
            assistantContext={assistantContext}
            onClose={() => setSearchOpen(false)}
          />
        </div>
      ) : null}

      {cornerCard ? (
        <div
          ref={countCardRef}
          className={`corner-stack ${panel || leftPanel || rightPanel ? "corner-stack--reader" : ""}`}
        >
          <div className="corner-card">{cornerCard}</div>
        </div>
      ) : null}

      {panel && panelOpen ? (
        <aside className="panel-overlay panel-overlay--right" onClick={(e) => e.stopPropagation()}>
          {panel}
        </aside>
      ) : null}

      {contextOverlay && contextOverlayOpen ? (
        <div className="reader-context-layer" onClick={(e) => e.stopPropagation()}>
          {contextOverlay}
        </div>
      ) : null}

      {leftPanel && leftPanelOpen ? (
        <aside className="panel-overlay panel-overlay--left" onClick={(e) => e.stopPropagation()}>
          {leftPanelMode === "secondary" && leftPanelSecondary
            ? leftPanelSecondary
            : leftPanel}
        </aside>
      ) : null}

      {rightPanel && rightPanelOpen ? (
        <aside className="panel-overlay panel-overlay--right" onClick={(e) => e.stopPropagation()}>
          {rightPanel}
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

function IconAbout() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="12" cy="12" r="9" />
      <line x1="12" y1="10" x2="12" y2="17" />
      <line x1="12" y1="6.5" x2="12" y2="8" strokeWidth="2.2" />
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

function IconTree() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="6" cy="5" r="2" />
      <circle cx="17" cy="12" r="2" />
      <circle cx="17" cy="19" r="2" />
      <path d="M8 5h3v14h4" />
      <path d="M11 12h4" />
    </svg>
  );
}

function IconContext() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="5" y="4" width="14" height="16" />
      <path d="M8 8h8" />
      <path d="M8 12h8" />
      <path d="M8 16h5" />
      <circle cx="5" cy="4" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="19" cy="20" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

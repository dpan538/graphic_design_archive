"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import type { FolderTypeKey } from "@/types/archive";

export interface DrawerItem {
  key: string;
  type?: FolderTypeKey;
  ink?: string;
  tabLabel: string;
  title: string;
  href: string;
  /** Detail lines revealed on hover. */
  reveal: string[];
}

/**
 * A drawer of physical, tabbed folders. Long folder sets live inside a
 * scroll viewport, with edge-hover auto-scroll so hover reveal still works
 * without requiring the wheel/trackpad for every pass through the stack.
 */
export default function FolderDrawer({ items }: { items: DrawerItem[] }) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const speedRef = useRef(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const step = () => {
      const el = scrollRef.current;
      const speed = speedRef.current;
      if (el && speed !== 0) el.scrollTop += speed;
      frameRef.current = window.requestAnimationFrame(step);
    };
    frameRef.current = window.requestAnimationFrame(step);
    return () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    };
  }, []);

  function onPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (e.pointerType !== "mouse") return;
    const el = scrollRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const edge = Math.min(120, rect.height * 0.22);
    const topDistance = e.clientY - rect.top;
    const bottomDistance = rect.bottom - e.clientY;

    if (topDistance < edge) {
      speedRef.current = -Math.max(2, Math.round(((edge - topDistance) / edge) * 18));
    } else if (bottomDistance < edge) {
      speedRef.current = Math.max(2, Math.round(((edge - bottomDistance) / edge) * 18));
    } else {
      speedRef.current = 0;
    }
  }

  function stopAutoScroll() {
    speedRef.current = 0;
  }

  return (
    <div className="drawer-stage">
      <header className="drawer-stage__intro">
        <div>
          <p className="label-caps">Primary drawers · {String(items.length).padStart(2, "0")}</p>
          <h1>Four coordinates for entering the archive.</h1>
        </div>
        <p>
          Each divider opens the same evidence collection from a different
          cataloguing coordinate. Select a tab; the records remain linked.
        </p>
      </header>

      <div className="archive-box-frame">
        <div
          ref={scrollRef}
          className="folder-scroll"
          role="region"
          aria-label="Primary archive drawers"
          tabIndex={0}
          onPointerMove={onPointerMove}
          onPointerLeave={stopAutoScroll}
          onPointerDown={stopAutoScroll}
        >
          <div className="folder-stack">
            {items.map((item, index) => {
              const detailId = `folder-detail-${item.key}`;
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  className="folder-card group"
                  data-folder-type={item.type ?? "unknown"}
                  aria-describedby={detailId}
                  style={
                    {
                      "--folder-index": index,
                      "--folder-tab-left": `${1.15 + index * 7.1}rem`,
                      "--folder-tab-compact-left": `${0.8 + index * 5.75}rem`,
                      "--folder-tab-mobile-left": `${0.65 + index * 0.62}rem`,
                    } as React.CSSProperties
                  }
                >
                  <span className="folder-card__number" aria-hidden>
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="folder-tab">
                    <span className="folder-chip" aria-hidden />
                    {item.tabLabel}
                  </span>

                  <div className="folder-card__action">
                    <span className="label-caps text-ink-soft shrink-0">
                      <span className="folder-action--idle">lift to inspect</span>
                      <span className="folder-action--hover">open drawer →</span>
                      <span className="folder-action--touch">tap to open →</span>
                    </span>
                  </div>

                  <div className="folder-card__body">
                    <span className="folder-title">{item.title}</span>
                    <div className="folder-reveal" id={detailId}>
                      <ul className="mt-3 text-sm text-ink-soft space-y-1">
                        {item.reveal.map((line, i) => (
                          <li key={i}>{line}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="archive-box-front" aria-hidden="true">
          <span>ABX / PRIMARY INDEX</span>
          <span className="archive-box-front__handle">DRAWERS · {String(items.length).padStart(2, "0")}</span>
          <span>RETURN TO SOURCE</span>
        </div>
      </div>

      <p className="drawer-stage__mobile-instruction label-caps">
        Swipe the card set · tap a card to open
      </p>
    </div>
  );
}

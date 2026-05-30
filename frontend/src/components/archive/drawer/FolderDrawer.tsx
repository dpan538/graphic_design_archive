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
      <div
        ref={scrollRef}
        className="folder-scroll"
        onPointerMove={onPointerMove}
        onPointerLeave={stopAutoScroll}
        onPointerDown={stopAutoScroll}
      >
        <div className="folder-stack">
          {items.map((item) => {
            return (
              <Link
                key={item.key}
                href={item.href}
                className="folder-card group"
                data-folder-type={item.type ?? "unknown"}
              >
                <span className="folder-tab">
                  <span
                    className="folder-chip"
                    aria-hidden
                  />
                  {item.tabLabel}
                </span>

                <div className="flex justify-end">
                  <span className="label-caps text-ink-soft shrink-0">
                    <span className="folder-action--idle">hover to select</span>
                    <span className="folder-action--hover">click to open →</span>
                  </span>
                </div>

                <div className="mt-auto">
                  <span className="folder-title">{item.title}</span>
                  <div className="folder-reveal">
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
    </div>
  );
}

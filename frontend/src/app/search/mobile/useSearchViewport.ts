"use client";

import { useEffect, type RefObject } from "react";

/* Only the fixed Search window follows the visual viewport (including a
   keyboard). Home's scene heights remain independent of these events. */
export function useSearchViewport(ref: RefObject<HTMLDivElement | null>, overlay: boolean) {
  useEffect(() => {
    const node = ref.current;
    const viewport = window.visualViewport;
    if (!node || !viewport) return;
    let frame = 0;
    const measure = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        // Pinch zoom remains browser-controlled, without layout intervention.
        if (viewport.scale !== 1) return;
        const bar = document.querySelector<HTMLElement>('[data-nav="mobile"]');
        const top = overlay ? Math.max(bar?.getBoundingClientRect().bottom ?? 0, viewport.offsetTop) : viewport.offsetTop;
        node.style.setProperty("--search-visible-top", `${top}px`);
        node.style.setProperty("--search-visible-height", `${Math.max(0, viewport.offsetTop + viewport.height - top)}px`);
      });
    };
    const bar = document.querySelector('[data-nav="mobile"]');
    const observer = new ResizeObserver(measure);
    if (bar) observer.observe(bar);
    viewport.addEventListener("resize", measure);
    viewport.addEventListener("scroll", measure);
    measure();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      viewport.removeEventListener("resize", measure);
      viewport.removeEventListener("scroll", measure);
      node.style.removeProperty("--search-visible-top");
      node.style.removeProperty("--search-visible-height");
    };
  }, [ref, overlay]);
}

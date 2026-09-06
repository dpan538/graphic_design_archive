"use client";

import { useEffect, type RefObject } from "react";

/* Progress of a tall container through the viewport, 0 at its top edge and
   1 when its bottom edge lands — the scroll distance is the container's
   height minus one viewport. Computed straight from the scroll event (one
   rectangle read, no observer and no animation frame, so it also runs in a
   throttled tab); the callback also hears whether the container is near
   the viewport, so a stage can rest or mount late. */
export function useStageProgress(ref: RefObject<HTMLElement | null>, onProgress: (p: number, near: boolean) => void) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const probe = document.createElement("div");
    probe.style.cssText = "position:fixed;height:100svh;visibility:hidden;pointer-events:none";
    document.body.append(probe);
    const compute = () => {
      const rect = el.getBoundingClientRect();
      const vh = probe.getBoundingClientRect().height;
      const span = rect.height - vh;
      const p = span > 0 ? Math.min(1, Math.max(0, -rect.top / span)) : 1;
      const near = rect.top < vh * 1.25 && rect.bottom > -vh * 0.25;
      onProgress(p, near);
    };
    window.addEventListener("scroll", compute, { passive: true });
    window.addEventListener("resize", compute);
    compute();
    return () => {
      probe.remove();
      window.removeEventListener("scroll", compute);
      window.removeEventListener("resize", compute);
    };
  }, [ref, onProgress]);
}

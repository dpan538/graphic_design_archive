"use client";

import { useEffect, useRef } from "react";
import type { Program } from "./instruments";

/* A canvas that runs one instrument program at ~30 fps while it is on
   screen, the pane is visible and motion is allowed — and draws exactly
   one frame otherwise. `progress` (draw-in) and `active` (brightness) are
   refs the page's scroll handler writes, so no React state moves per frame.
   DPR-aware; the CSS box decides the size. */
export default function Instrument({
  program,
  progress,
  active,
  reduced,
  className,
}: {
  program: Program;
  progress: { current: number };
  active: { current: number };
  reduced: boolean;
  className?: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let w = 0;
    let h = 0;
    let dpr = 1;
    let raf = 0;
    let last = 0;
    let visible = false;
    let dead = false;
    const t0 = performance.now();

    const size = () => {
      const r = canvas.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      w = Math.max(1, Math.round(r.width));
      h = Math.max(1, Math.round(r.height));
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    };
    const frame = (now: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      program(ctx, w, h, reduced ? 0 : (now - t0) / 1000, progress.current, active.current);
    };
    const loop = (now: number) => {
      raf = 0;
      if (dead) return;
      if (now - last >= 32) {
        last = now;
        frame(now);
      }
      if (visible && !reduced && !document.hidden) raf = requestAnimationFrame(loop);
    };
    const start = () => {
      if (!raf && !dead) raf = requestAnimationFrame(loop);
    };

    size();
    frame(performance.now());
    const io = new IntersectionObserver(
      (entries) => {
        visible = entries.some((en) => en.isIntersecting);
        if (visible) start();
      },
      { rootMargin: "80px" },
    );
    io.observe(canvas);
    const ro = new ResizeObserver(() => {
      size();
      frame(performance.now());
      start();
    });
    ro.observe(canvas);
    const onVis = () => {
      if (!document.hidden) start();
    };
    document.addEventListener("visibilitychange", onVis);
    /* the scroll handler nudges a stopped loop so draw-in progresses even
       with motion reduced */
    const onScroll = () => {
      if (reduced) frame(performance.now());
      else start();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    /* a synchronous frame on demand (the dev freeze hook, where no
       animation frame may run) */
    const onDemand = () => frame(performance.now());
    window.addEventListener("mgda:frame", onDemand);
    return () => {
      dead = true;
      cancelAnimationFrame(raf);
      io.disconnect();
      ro.disconnect();
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("mgda:frame", onDemand);
    };
  }, [program, progress, active, reduced]);

  return <canvas ref={ref} className={className} aria-hidden="true" />;
}

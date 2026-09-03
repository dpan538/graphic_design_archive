"use client";

import { useEffect, useRef } from "react";

/* Study III of the ellipsis — the engraved sphere (HOMEPAGE_IDENTITY_SEQUENCE_v1.md
   §F3): a sphere rendered the way a copperplate engraver renders one.
   Three plates: parallel hatching whose line weight carries the light;
   cross-hatching at 50° laid only into the shadow; and the engraver's
   guide lines — five parallels and five meridians of the globe — over
   which the hatching sits. One colour. The light drifts slowly around the
   sphere while it is on screen.

   The drawing happens OFF the main thread: a Worker renders each frame
   into an OffscreenCanvas and posts it as an ImageBitmap, and the page's
   canvas only presents it through a bitmaprenderer context — nothing the
   main thread can measure. (Drawn on the main thread, a frame of ~150
   filled ribbons cost 4–8 ms every 50 ms; inside the studies' film that
   was a dropped scroll frame in three.) Where OffscreenCanvas is missing
   the same program runs on the main thread, as it first did. */

const SIZE = 440;

/* The program. It refers to nothing outside itself — it is shipped to the
   Worker as source text (Function.prototype.toString) — and returns the
   frame function. */
function hatchProgram(ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D, dpr: number) {
  const SIZE = 440;
  const C = SIZE / 2;
  const R = 200;
  const PITCH = 4.6;
  const XPITCH = 7.4;

  const lightAt = (t: number) => {
    const la = -0.9 + Math.sin(t * 0.09) * 0.7;
    const Lx = Math.cos(la) * 0.72;
    const Ly = 0.6 + Math.sin(t * 0.05) * 0.12;
    const Lz = 0.42 + Math.sin(t * 0.07) * 0.1;
    const ll = Math.hypot(Lx, Ly, Lz);
    return [Lx / ll, Ly / ll, Lz / ll];
  };
  const litAt = (x: number, y: number, L: number[]) => {
    const nx = x / R;
    const ny = -y / R;
    const nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
    return { lit: Math.max(0, nx * L[0] + ny * L[1] + nz * L[2]), nz };
  };

  /* a ribbon along a line through (x0,y0) at angle `ang`, its half-width
     from a function of the point */
  const ribbon = (x0: number, y0: number, ang: number, width: (x: number, y: number) => number) => {
    const cs = Math.cos(ang);
    const sn = Math.sin(ang);
    const px = -x0 * sn + y0 * cs; // perpendicular distance from centre
    if (Math.abs(px) >= R) return;
    const half = Math.sqrt(R * R - px * px);
    const xs: number[] = [];
    const ys: number[] = [];
    const ws: number[] = [];
    for (let t = -half; t <= half; t += 4.5) {
      const X = -px * sn + t * cs;
      const Y = px * cs + t * sn;
      xs.push(X);
      ys.push(Y);
      ws.push(width(X, Y));
    }
    if (xs.length < 2) return;
    ctx.beginPath();
    for (let i = 0; i < xs.length; i++) {
      const nx = (-sn * ws[i]) / 2;
      const ny = (cs * ws[i]) / 2;
      const X = C + xs[i] + nx;
      const Y = C + ys[i] + ny;
      if (i === 0) ctx.moveTo(X, Y);
      else ctx.lineTo(X, Y);
    }
    for (let i = xs.length - 1; i >= 0; i--) {
      const nx = (-sn * ws[i]) / 2;
      const ny = (cs * ws[i]) / 2;
      ctx.lineTo(C + xs[i] - nx, C + ys[i] - ny);
    }
    ctx.closePath();
    ctx.fill();
  };

  return (t: number) => {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, SIZE, SIZE);
    const L = lightAt(t);

    /* the plate's ground: a faint tone over the whole disc, so the sphere
       reads as a body and the lit side is not bare black */
    ctx.fillStyle = "rgba(251, 250, 247, 0.07)";
    ctx.beginPath();
    ctx.arc(C, C, R, 0, Math.PI * 2);
    ctx.fill();
    /* plate 1 — horizontal hatching, weight = darkness, a soft rim */
    ctx.fillStyle = "#fbfaf7";
    for (let y = -R + PITCH / 2; y < R; y += PITCH) {
      ribbon(0, y, 0, (x, yy) => {
        const { lit, nz } = litAt(x, yy, L);
        const rim = Math.pow(1 - nz, 3) * 0.55;
        return 0.3 + (PITCH - 1.0) * Math.pow(1 - lit, 1.7) * 0.5 + rim;
      });
    }
    /* plate 2 — cross-hatching at 50°, only where the light has gone */
    ctx.fillStyle = "rgba(251, 250, 247, 0.95)";
    const ang = (50 * Math.PI) / 180;
    for (let d = -R * 1.2; d < R * 1.2; d += XPITCH) {
      const x0 = -d * Math.sin(ang);
      const y0 = d * Math.cos(ang);
      ribbon(x0, y0, ang, (x, yy) => {
        const { lit } = litAt(x, yy, L);
        const shade = Math.max(0, 0.34 - lit) / 0.34;
        return shade > 0 ? 0.12 + 1.5 * Math.pow(shade, 1.4) : 0;
      });
    }
    /* plate 3 — the engraver's guides: parallels and meridians, hairlines */
    ctx.strokeStyle = "rgba(251, 250, 247, 0.5)";
    ctx.lineWidth = 0.75;
    for (let p = 1; p < 6; p++) {
      const lat = (p / 6 - 0.5) * Math.PI;
      const cl = Math.cos(lat);
      const y = C - Math.sin(lat) * R;
      ctx.beginPath();
      ctx.ellipse(C, y, cl * R, cl * R * 0.22, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    const spin = t * 0.06;
    for (let m = 0; m < 5; m++) {
      const lon = (m / 5) * Math.PI + spin;
      ctx.beginPath();
      let pen = false;
      for (let k = 0; k <= 64; k++) {
        const lat = (k / 64 - 0.5) * Math.PI;
        const cl = Math.cos(lat);
        const x = cl * Math.sin(lon);
        const z = cl * Math.cos(lon);
        const y = Math.sin(lat);
        if (z < 0) {
          pen = false;
          continue;
        }
        const px = C + x * R;
        const py = C - y * R;
        if (!pen) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
        pen = true;
      }
      ctx.stroke();
    }
    /* the outline */
    ctx.strokeStyle = "rgba(251, 250, 247, 0.72)";
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.arc(C, C, R + 1, 0, Math.PI * 2);
    ctx.stroke();
  };
}

/* the Worker: the program, a clock, and a 20 fps loop that posts frames */
const workerSource = () => `"use strict";
const program = ${hatchProgram.toString()};
let canvas = null, draw = null, timer = 0, t0 = 0;
const frame = () => {
  draw((performance.now() - t0) / 1000);
  const bitmap = canvas.transferToImageBitmap();
  self.postMessage(bitmap, [bitmap]);
};
self.onmessage = (e) => {
  const m = e.data;
  if (m.type === "init") {
    canvas = new OffscreenCanvas(m.w, m.h);
    draw = program(canvas.getContext("2d"), m.dpr);
    t0 = performance.now();
    frame();
  } else if (m.type === "run") {
    if (!timer) timer = setInterval(frame, 50);
  } else if (m.type === "stop") {
    clearInterval(timer);
    timer = 0;
  }
};
`;

export default function HatchSphere({ className }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = SIZE * dpr;
    canvas.height = SIZE * dpr;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let start = () => {};
    let stop = () => {};
    let dispose = () => {};
    const presenter =
      typeof OffscreenCanvas !== "undefined" && typeof Worker !== "undefined" ? canvas.getContext("bitmaprenderer") : null;
    if (presenter) {
      const url = URL.createObjectURL(new Blob([workerSource()], { type: "text/javascript" }));
      const worker = new Worker(url);
      worker.onmessage = (e: MessageEvent<ImageBitmap>) => presenter.transferFromImageBitmap(e.data);
      worker.postMessage({ type: "init", w: SIZE * dpr, h: SIZE * dpr, dpr });
      start = () => worker.postMessage({ type: "run" });
      stop = () => worker.postMessage({ type: "stop" });
      dispose = () => {
        worker.terminate();
        URL.revokeObjectURL(url);
      };
    } else {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const draw = hatchProgram(ctx, dpr);
      draw(0);
      let raf = 0;
      let last = 0;
      const t0 = performance.now();
      const tick = (now: number) => {
        if (now - last >= 50) {
          last = now;
          draw((now - t0) / 1000);
        }
        raf = requestAnimationFrame(tick);
      };
      start = () => {
        if (!raf) raf = requestAnimationFrame(tick);
      };
      stop = () => {
        cancelAnimationFrame(raf);
        raf = 0;
      };
    }

    /* the light only moves while the sphere is on screen and the page is
       in front */
    let onScreen = false;
    const settle = () => {
      if (onScreen && !reduce && !document.hidden) start();
      else stop();
    };
    const io = new IntersectionObserver(
      ([e]) => {
        onScreen = e.isIntersecting;
        settle();
      },
      { threshold: 0.05 },
    );
    io.observe(canvas);
    document.addEventListener("visibilitychange", settle);
    return () => {
      stop();
      io.disconnect();
      document.removeEventListener("visibilitychange", settle);
      dispose();
    };
  }, []);

  return <canvas ref={ref} className={className} width={440} height={440} aria-hidden="true" />;
}

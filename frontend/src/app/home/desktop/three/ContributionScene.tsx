"use client";

import { useEffect, useRef } from "react";
import type { RefObject } from "react";
import * as THREE from "three";

/* Contribution's isometric field — a visual replication of the supplied
   reference: on black, an undulating white wireframe surface, a scatter
   plane of small white marks floating above it, and colonnades of thin
   coloured stems carrying spheres, rings and tick marks.

   It is NOT a morph of the histogram. The histogram is cleared first, then
   this is drawn from nothing: the surface's wireframe strokes in, the
   scatter fills, the stems extend, and only then do the markers land.

   Everything is deterministic (seeded PRNG, no Math.random at render) so a
   given scroll position always produces the same frame. */

type Props = {
  /** Mutated by the parent each scroll tick; read per-frame so scrolling
   * never re-renders React. */
  progressRef: RefObject<number>;
  active: boolean;
  staticFrame?: boolean;
};

/* Deterministic PRNG — visuals must not shuffle between reloads. */
function mulberry(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PALETTE = [0x4f8ef7, 0xf24b4b, 0xff8a3d, 0xffd93d, 0x4fd18b, 0xe86bb0, 0x9b7bf0];

export default function ContributionScene({ progressRef, active, staticFrame }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef(0);
  const renderRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const rand = mulberry(20260901);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-10, 10, 10, -10, 0.1, 200);
    /* Isometric: equal angles on all three axes. */
    camera.position.set(14, 12, 14);
    /* Look above the ground plane, not at it: the tall stems were running off
       the top edge, so raising the target drops the field lower in frame.
       Eased back from 2.2 after the field was scaled up — aiming slightly
       lower lifts the whole scene, pulling its near lower edge back inside the
       frame where it had begun to clip. Moving the canvas box alone would not
       fix this: the clip is against the frustum, not the element. */
    camera.lookAt(0, 2.0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    /* Capped at 1.35 rather than 2 to give the drawing weight. WebGL ignores
       LineBasicMaterial.linewidth — every line is exactly one device pixel —
       so on a 2x display the whole field renders as hairlines. Lowering the
       ratio is the one lever that actually thickens them; antialiasing is on,
       so the trade in sharpness is small. */
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.35));
    mount.appendChild(renderer.domElement);

    /* ---- 0. Coordinate frame — drawn FIRST, before any data ----
       The field used to arrive all at once, which gave the reader nothing to
       read it against. The axes establish the space, then data enters it. */
    const axisPts: THREE.Vector3[] = [];
    const R = 6.6;
    axisPts.push(new THREE.Vector3(-R, -1.6, -R), new THREE.Vector3(R, -1.6, -R));
    axisPts.push(new THREE.Vector3(-R, -1.6, -R), new THREE.Vector3(-R, -1.6, R));
    axisPts.push(new THREE.Vector3(-R, -1.6, -R), new THREE.Vector3(-R, 5.6, -R));
    for (let i = 1; i <= 5; i += 1) {
      const y = -1.6 + (i / 5) * 7.2;
      axisPts.push(new THREE.Vector3(-R, y, -R), new THREE.Vector3(-R - 0.34, y, -R));
    }
    for (let i = 1; i <= 6; i += 1) {
      const x = -R + (i / 6) * 2 * R;
      axisPts.push(new THREE.Vector3(x, -1.6, -R), new THREE.Vector3(x, -1.6, -R - 0.34));
    }
    const axisGeo = new THREE.BufferGeometry().setFromPoints(axisPts);
    const axisMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.62 });
    const axesObj = new THREE.LineSegments(axisGeo, axisMat);
    scene.add(axesObj);
    const axisCount = axisGeo.attributes.position.count;
    axisGeo.setDrawRange(0, 0);

    /* ---- 1. Undulating wireframe surface ---- */
    const SEG = 26;
    const surfGeo = new THREE.PlaneGeometry(13, 13, SEG, SEG);
    surfGeo.rotateX(-Math.PI / 2);
    const pos = surfGeo.attributes.position;
    for (let i = 0; i < pos.count; i += 1) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const h =
        Math.sin(x * 0.55) * 0.75 + Math.cos(z * 0.62) * 0.7 + Math.sin((x + z) * 0.33) * 0.55;
      pos.setY(i, h * 0.85);
    }
    surfGeo.computeVertexNormals();
    const surfWire = new THREE.WireframeGeometry(surfGeo);
    const surfMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95 });
    const surface = new THREE.LineSegments(surfWire, surfMat);
    surface.position.y = -1.4;
    scene.add(surface);
    const surfCount = surfWire.attributes.position.count;
    surfWire.setDrawRange(0, 0);

    /* ---- 2. Scatter plane of small marks, floating above ---- */
    const SCATTER = 620;
    const markGeo = new THREE.PlaneGeometry(0.17, 0.17);
    markGeo.rotateX(-Math.PI / 2);
    const markMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
    const scatter = new THREE.InstancedMesh(markGeo, markMat, SCATTER);
    const dummy = new THREE.Object3D();
    const scatterOrder: number[] = [];
    for (let i = 0; i < SCATTER; i += 1) {
      const gx = (rand() - 0.5) * 12.4;
      const gz = (rand() - 0.5) * 12.4;
      const d = Math.hypot(gx, gz) / 8.8;
      /* Denser toward the middle, thinning at the edges, like the reference. */
      if (rand() < d * 0.85) {
        dummy.position.set(999, 999, 999);
      } else {
        dummy.position.set(gx, 2.15 + (rand() - 0.5) * 0.12, gz);
      }
      dummy.updateMatrix();
      scatter.setMatrixAt(i, dummy.matrix);
      scatterOrder.push(i);
    }
    scatter.instanceMatrix.needsUpdate = true;
    scatter.count = 0;
    scene.add(scatter);

    /* ---- 3. Colonnades of coloured stems with markers ---- */
    type Stem = {
      line: THREE.Line;
      marker: THREE.Mesh;
      topY: number;
      baseY: number;
      x: number;
      z: number;
    };
    const stems: Stem[] = [];
    const stemGroup = new THREE.Group();
    scene.add(stemGroup);

    const clusters = [
      { cx: -7.6, cz: -3.2, n: 13, spread: 2.1 }, // upper-left colonnade
      { cx: 7.4, cz: 1.4, n: 15, spread: 2.4 }, // right colonnade
      { cx: -4.6, cz: 5.4, n: 18, spread: 1.2 }, // dense cluster, front-left
    ];
    clusters.forEach((cl, ci) => {
      for (let i = 0; i < cl.n; i += 1) {
        const x = cl.cx + (rand() - 0.5) * cl.spread * 2;
        const z = cl.cz + (rand() - 0.5) * cl.spread * 2;
        const baseY = -1.6;
        const topY = baseY + 2.4 + rand() * 5.4;
        const color = PALETTE[Math.floor(rand() * PALETTE.length)];

        const g = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, baseY, z),
          new THREE.Vector3(x, topY, z),
        ]);
        const m = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.95 });
        const line = new THREE.Line(g, m);
        stemGroup.add(line);

        /* Marker type varies by cluster, as in the reference: spheres on the
           left and right colonnades, rings scattered among them. */
        const isRing = ci === 1 && rand() < 0.4;
        const mk = isRing
          ? new THREE.Mesh(
              new THREE.TorusGeometry(0.26, 0.09, 8, 20),
              new THREE.MeshBasicMaterial({ color }),
            )
          : new THREE.Mesh(
              new THREE.SphereGeometry(ci === 2 ? 0.13 : 0.3, 16, 12),
              new THREE.MeshBasicMaterial({ color }),
            );
        if (isRing) mk.rotation.x = Math.PI / 2;
        mk.position.set(x, topY, z);
        mk.scale.setScalar(0.001);
        stemGroup.add(mk);

        stems.push({ line, marker: mk, topY, baseY, x, z });
      }
    });

    /* ---- 4. Yellow tick marks on the ground plane ---- */
    const TICKS = 46;
    const tickGeo = new THREE.PlaneGeometry(0.34, 0.13);
    tickGeo.rotateX(-Math.PI / 2);
    const tickMat = new THREE.MeshBasicMaterial({ color: 0xffd93d, side: THREE.DoubleSide });
    const ticks = new THREE.InstancedMesh(tickGeo, tickMat, TICKS);
    for (let i = 0; i < TICKS; i += 1) {
      const c = clusters[i % clusters.length];
      dummy.position.set(
        c.cx + (rand() - 0.5) * c.spread * 2.4,
        -1.62,
        c.cz + (rand() - 0.5) * c.spread * 2.4,
      );
      dummy.updateMatrix();
      ticks.setMatrixAt(i, dummy.matrix);
    }
    ticks.instanceMatrix.needsUpdate = true;
    ticks.count = 0;
    scene.add(ticks);

    const resize = () => {
      const w = mount.clientWidth || 1;
      const h = mount.clientHeight || 1;
      renderer.setSize(w, h, false);
      const aspect = w / h;
      /* Smaller half = larger drawing: this is the orthographic frustum, so
         tightening it scales the field up (~25% total across two passes)
         without moving the camera.
         Still wider than the original 8.6, which sliced the tallest stems. */
      const half = 8.15;
      camera.left = -half * aspect;
      camera.right = half * aspect;
      camera.top = half;
      camera.bottom = -half;
      camera.updateProjectionMatrix();
      /* Redraw on every resize. Without this the first draw lands in a 1x1
         buffer (the mount has no layout yet when the effect runs), the
         observer then resizes the canvas, and nothing ever repaints it — so
         the panel stays blank in any context where the loop is not running. */
      renderRef.current?.();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    const seg = (p: number, a: number, b: number) =>
      Math.min(Math.max((p - a) / (b - a), 0), 1);

    let drawOnce: (() => void) | null = null;
    renderRef.current = () => {
      const p = staticFrame ? 1 : Math.min(Math.max(progressRef.current ?? 0, 0), 1);

      /* Drawn from nothing, in order: surface → scatter → stems → markers. */
      /* THE BUG THIS FIXES: every range below used to be measured against
         the section's own progress and finished by p = 0.26 — but the canvas
         is not revealed until p ≈ 0.42. The whole build therefore ran while
         the element was invisible, and the reader only ever saw the finished
         scene snap into place. Remap to the window in which the canvas is
         actually on screen, so the drawing is what the reader watches. */
      /* A long window on purpose: the drawing IS the content here, so the
         reader gets to watch the marks land rather than catch the aftermath. */
      const t = seg(p, 0.4, 0.98);
      axisGeo.setDrawRange(0, Math.floor(seg(t, 0.0, 0.14) * axisCount));
      surfWire.setDrawRange(0, Math.floor(seg(t, 0.08, 0.38) * surfCount));
      scatter.count = Math.floor(seg(t, 0.3, 0.8) * SCATTER);
      ticks.count = Math.floor(seg(t, 0.4, 0.82) * TICKS);

      const stemP = seg(t, 0.5, 1.0);
      stems.forEach((s, i) => {
        const local = Math.min(Math.max(stemP * stems.length - i * 0.55, 0), 1);
        const arr = s.line.geometry.attributes.position as THREE.BufferAttribute;
        arr.setY(1, s.baseY + (s.topY - s.baseY) * local);
        arr.needsUpdate = true;
        const mp = Math.min(Math.max((local - 0.72) / 0.28, 0), 1);
        s.marker.position.y = s.baseY + (s.topY - s.baseY) * local;
        s.marker.scale.setScalar(mp);
      });

      renderer.render(scene, camera);
    };

    /* Draw one frame immediately on mount, independent of `active` and of
       requestAnimationFrame. Without this the canvas stays blank whenever the
       loop has not started — a paused/throttled context, or simply before the
       section becomes active — and a blank panel is not a readable state. */
    drawOnce = renderRef.current;
    drawOnce();

    return () => {
      renderRef.current = null;
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      mount.removeChild(renderer.domElement);
      axisGeo.dispose();
      axisMat.dispose();
      surfGeo.dispose();
      surfWire.dispose();
      surfMat.dispose();
      markGeo.dispose();
      markMat.dispose();
      tickGeo.dispose();
      tickMat.dispose();
      stems.forEach((s) => {
        s.line.geometry.dispose();
        (s.line.material as THREE.Material).dispose();
        s.marker.geometry.dispose();
        (s.marker.material as THREE.Material).dispose();
      });
      renderer.dispose();
    };
  }, [staticFrame, progressRef]);

  useEffect(() => {
    /* render only when the progress has moved — a still section costs no
       GPU, and the loop is cheap enough to keep warm during Identity's
       closing so the hand-over does not pay for the first frame */
    let last = NaN;
    const tick = () => {
      const p = progressRef.current;
      if (p !== last) {
        last = p;
        renderRef.current?.();
      }
      if (!staticFrame) rafRef.current = requestAnimationFrame(tick);
    };
    cancelAnimationFrame(rafRef.current);
    if (active) tick();
    return () => cancelAnimationFrame(rafRef.current);
  }, [active, staticFrame, progressRef]);

  return <div ref={mountRef} style={{ width: "100%", height: "100%" }} aria-hidden="true" />;
}

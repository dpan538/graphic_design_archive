/* The structural engine (§7i, the algorithm refactor): a picture's positions
   are not sampled at random; they come from a TOPOLOGICAL SKELETON chosen by
   the term count and the variant, warped by a SEMANTIC FIELD chosen by the
   state's semantic hash, then jittered by the seed within a small bound.
   Two terms oppose; three make a triangle, a chain or an arc; four make two
   clusters, a diamond or a run; more make rings, rows or a spiral. So a
   glance tells the count, the starting point tells the field, and the same
   count under another starting point does not look the same. None of this
   reads confidence, strength or evidence; the field is a hash, not a meaning. */

import type { Frame } from "./types.ts";
import { presentationSeed } from "./seed.ts";

export type Point = { readonly x: number; readonly y: number };

const r1 = (value: number) => Math.round(value * 10) / 10;
const pt = (x: number, y: number): Point => ({ x: r1(x), y: r1(y) });

/* an independent deterministic choice from the seed, per salt */
export function pick(seed: number, salt: string, modulus: number): number {
  return presentationSeed(String(seed), salt) % modulus;
}
/* a deterministic unit value in [0, 1) from the seed, per salt */
export function unit(seed: number, salt: string): number {
  return (presentationSeed(String(seed), salt) % 10_000) / 10_000;
}

export const SKELETON_FAMILIES: Readonly<Record<number, readonly string[]>> = Object.freeze({
  1: ["centre", "centre", "centre"],
  2: ["opposed", "diagonal", "stacked"],
  3: ["triangle", "chain", "arc"],
  4: ["clusters", "diamond", "run"],
  5: ["ring", "rows", "spiral"],
  6: ["ring", "rows", "spiral"],
  7: ["ring", "rows", "spiral"],
  8: ["ring", "rows", "spiral"],
});

export function skeletonFamily(count: number, variant: number): string {
  const families = SKELETON_FAMILIES[Math.min(8, Math.max(1, count))] ?? ["centre"];
  return families[variant % families.length] ?? "centre";
}

/* the skeleton: positions in tree order (the focused term first) */
export function skeletonPoints(count: number, variant: number, seed: number, frame: Frame): Point[] {
  const { x: fx, y: fy, width: w, height: h } = frame;
  const cx = fx + w / 2;
  const cy = fy + h / 2;
  const jitter = (salt: string, amount: number) => (unit(seed, salt) - 0.5) * 2 * amount;
  const family = skeletonFamily(count, variant);
  const at = (u: number, v: number, salt: string, amount = 0.03) => pt(fx + w * (u + jitter(`${salt}:x`, amount)), fy + h * (v + jitter(`${salt}:y`, amount)));
  if (count <= 1) return [at(0.5, 0.5, "c", 0.02)];
  if (count === 2) {
    if (family === "opposed") return [at(0.17, 0.5, "a", 0.04), at(0.83, 0.5, "b", 0.04)];
    if (family === "diagonal") return pick(seed, "diag", 2) === 0 ? [at(0.22, 0.2, "a"), at(0.78, 0.8, "b")] : [at(0.78, 0.2, "a"), at(0.22, 0.8, "b")];
    return [at(0.5, 0.16, "a", 0.04), at(0.5, 0.84, "b", 0.04)];
  }
  if (count === 3) {
    if (family === "triangle") {
      const rotation = unit(seed, "tri:rot") * Math.PI * 2;
      const radius = Math.min(w, h) * 0.34;
      return [0, 1, 2].map((i) => {
        const angle = rotation + (i * Math.PI * 2) / 3;
        const scale = 0.92 + unit(seed, `tri:${i}`) * 0.16;
        return pt(cx + Math.cos(angle) * radius * scale, cy + Math.sin(angle) * radius * scale);
      });
    }
    if (family === "chain") {
      const flip = pick(seed, "chain", 2) === 0;
      return flip ? [at(0.18, 0.2, "a"), at(0.5, 0.5, "b"), at(0.82, 0.8, "c")] : [at(0.82, 0.2, "a"), at(0.5, 0.5, "b"), at(0.18, 0.8, "c")];
    }
    /* arc: three points on an arc bending one way */
    const bend = pick(seed, "arc", 2) === 0 ? 1 : -1;
    return [at(0.18, 0.5 - 0.22 * bend, "a"), at(0.5, 0.5 + 0.18 * bend, "b"), at(0.82, 0.5 - 0.22 * bend, "c")];
  }
  if (count === 4) {
    if (family === "clusters") {
      const corner = pick(seed, "clusters", 2) === 0;
      const c1 = corner ? { u: 0.27, v: 0.27 } : { u: 0.73, v: 0.27 };
      const c2 = corner ? { u: 0.73, v: 0.73 } : { u: 0.27, v: 0.73 };
      const spread = 0.09;
      return [
        at(c1.u - spread, c1.v + spread * 0.5, "a", 0.02),
        at(c1.u + spread, c1.v - spread * 0.5, "b", 0.02),
        at(c2.u - spread, c2.v - spread * 0.5, "c", 0.02),
        at(c2.u + spread, c2.v + spread * 0.5, "d", 0.02),
      ];
    }
    if (family === "diamond") return [at(0.5, 0.14, "a", 0.02), at(0.84, 0.5, "b", 0.02), at(0.5, 0.86, "c", 0.02), at(0.16, 0.5, "d", 0.02)];
    /* run: four along a slanted band */
    const rising = pick(seed, "run", 2) === 0;
    return [0, 1, 2, 3].map((i) => at(0.16 + i * 0.226, rising ? 0.8 - i * 0.2 : 0.2 + i * 0.2, `r${i}`, 0.025));
  }
  /* five to eight */
  if (family === "ring") {
    const rotation = unit(seed, "ring:rot") * Math.PI * 2;
    const radius = Math.min(w, h) * 0.36;
    return Array.from({ length: count }, (_, i) => {
      const angle = rotation + (i * Math.PI * 2) / count;
      return pt(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
    });
  }
  if (family === "rows") {
    const perRow = Math.ceil(count / 2);
    return Array.from({ length: count }, (_, i) => at(0.16 + (i % perRow) * (0.68 / Math.max(1, perRow - 1)), i < perRow ? 0.3 : 0.7, `row${i}`, 0.02));
  }
  return Array.from({ length: count }, (_, i) => {
    const t = i / count;
    const angle = t * Math.PI * 3;
    const radius = Math.min(w, h) * (0.1 + 0.3 * t);
    return pt(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
  });
}

export type FieldKind = "radial" | "shear" | "lattice";

/* the semantic field: the state's semantic hash names it; it bends the
   skeleton the same way for every template of that state */
export function fieldKind(semanticHash: string): FieldKind {
  const code = parseInt(semanticHash.slice(0, 2), 16);
  return (["radial", "shear", "lattice"] as const)[(Number.isFinite(code) ? code : 0) % 3] ?? "radial";
}

export function applySemanticField(points: readonly Point[], semanticHash: string, frame: Frame): Point[] {
  const kind = fieldKind(semanticHash);
  const { x: fx, y: fy, width: w, height: h } = frame;
  const cx = fx + w / 2;
  const cy = fy + h / 2;
  const margin = { x: fx + w * 0.08, y: fy + h * 0.08, right: fx + w * 0.92, bottom: fy + h * 0.92 };
  const clamp = (p: Point) => pt(Math.min(margin.right, Math.max(margin.x, p.x)), Math.min(margin.bottom, Math.max(margin.y, p.y)));
  /* the second byte sets the field's strength, the third its sign */
  const strength = 0.12 + ((parseInt(semanticHash.slice(2, 4), 16) || 0) % 8) * 0.03;
  const sign = ((parseInt(semanticHash.slice(4, 6), 16) || 0) % 2) === 0 ? 1 : -1;
  return points.map((p) => {
    const dx = p.x - cx;
    const dy = p.y - cy;
    if (kind === "radial") {
      const dist = Math.hypot(dx, dy) / Math.max(w, h);
      const factor = 1 + sign * strength * 1.4 * dist;
      return clamp({ x: cx + dx * factor, y: cy + dy * factor });
    }
    if (kind === "shear") return clamp({ x: p.x + sign * strength * 0.8 * dy, y: p.y + sign * strength * 0.5 * dx });
    /* lattice: pulled toward a 4 × 5 grid of the frame */
    const gx = fx + (Math.round(((p.x - fx) / w) * 4) / 4) * w;
    const gy = fy + (Math.round(((p.y - fy) / h) * 5) / 5) * h;
    const pull = 0.45 + strength;
    return clamp({ x: p.x + (gx - p.x) * pull, y: p.y + (gy - p.y) * pull });
  });
}

/* the positions a template draws its terms at: skeleton → field → frame */
export function termPositions(count: number, variant: number, seed: number, semanticHash: string, frame: Frame): Point[] {
  return applySemanticField(skeletonPoints(count, variant, seed, frame), semanticHash, frame);
}

/* the skeleton's shape in numbers, for the phase-transition gate */
export function skeletonSummary(points: readonly Point[]): { readonly meanPairwiseDistance: number; readonly spreadX: number; readonly spreadY: number } {
  let total = 0;
  let pairs = 0;
  for (let i = 0; i < points.length; i += 1) for (let j = i + 1; j < points.length; j += 1) { total += Math.hypot((points[i] as Point).x - (points[j] as Point).x, (points[i] as Point).y - (points[j] as Point).y); pairs += 1; }
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  return { meanPairwiseDistance: pairs ? total / pairs : 0, spreadX: Math.max(...xs) - Math.min(...xs), spreadY: Math.max(...ys) - Math.min(...ys) };
}

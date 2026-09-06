/* The presentation fingerprint (§7i verification): a hash over the generated
   visual structure only — template, variant, frame, the field's ground, every
   definition (gradient stops and directions, the grain's frequency, seed and
   opacity), every primitive's kind, role, coordinates, dimensions, radii, path
   geometry, rotation, opacity and inks, and the terms' and associations'
   regions — and nothing that is text: no vocabulary, no title, no export id,
   no provenance string. Two scenes with the same fingerprint draw the same
   picture; a fingerprint that changes means the geometry changed. Pure and
   deterministic; shared by the tests and the verification suite. */

import type { ExplorationScene, SceneDecoration, SceneDef } from "./types.ts";

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function primitive(item: SceneDecoration): unknown {
  const base = { kind: item.kind, role: item.role ?? null, clip: item.clip ?? false, opacity: item.opacity ?? 1 };
  switch (item.kind) {
    case "rect":
      return { ...base, x: round(item.x), y: round(item.y), w: round(item.width), h: round(item.height), fill: item.fill, stroke: item.stroke ?? null, sw: item.strokeWidth ?? null, rotate: item.rotate ?? 0 };
    case "circle":
      return { ...base, cx: round(item.cx), cy: round(item.cy), r: round(item.r), fill: item.fill, stroke: item.stroke ?? null, sw: item.strokeWidth ?? null };
    case "line":
      return { ...base, x1: round(item.x1), y1: round(item.y1), x2: round(item.x2), y2: round(item.y2), stroke: item.stroke, w: round(item.width) };
    case "polygon":
      return { ...base, points: item.points.map((p) => [round(p.x), round(p.y)]), fill: item.fill, stroke: item.stroke ?? null, sw: item.strokeWidth ?? null };
    case "path":
      return { ...base, d: item.d, fill: item.fill, stroke: item.stroke ?? null, sw: item.strokeWidth ?? null };
    case "cross":
      return { ...base, cx: round(item.cx), cy: round(item.cy), size: round(item.size), stroke: item.stroke, w: round(item.width) };
    default:
      return base;
  }
}

function definition(item: SceneDef): unknown {
  if (item.kind === "grain") return { kind: "grain", id: item.id, f: item.baseFrequency, o: item.octaves, seed: item.seed, opacity: item.opacity };
  if (item.kind === "linear") return { kind: "linear", id: item.id, x1: item.x1, y1: item.y1, x2: item.x2, y2: item.y2, stops: item.stops };
  return { kind: "radial", id: item.id, cx: item.cx, cy: item.cy, r: item.r, stops: item.stops };
}

/* the structure, canonically serialised — the input of the hash */
export function presentationStructure(scene: ExplorationScene): string {
  return JSON.stringify({
    presentation: scene.presentationVersion,
    template: scene.templateId,
    variant: scene.variantId,
    frame: [scene.frame.x, scene.frame.y, scene.frame.width, scene.frame.height],
    fieldFill: scene.fieldFill,
    paper: scene.palette.paper,
    ink: scene.palette.ink,
    defs: scene.defs.map(definition),
    primitives: scene.decorations.map(primitive),
    terms: scene.nodes.map((node) => ({ index: node.index, anchor: [round(node.anchor.x), round(node.anchor.y)], region: [round(node.region.x), round(node.region.y), round(node.region.width), round(node.region.height)] })),
    associations: scene.connectors.map((item) => ({ from: item.from, to: item.to, region: [round(item.region.x), round(item.region.y), round(item.region.width), round(item.region.height)] })),
  });
}

/* the grammar: which primitive kinds the picture is made of, by role, and how the
   terms lie — the skeleton's spread — so two pictures with the same counts but
   another arrangement are told apart */
export function presentationGrammar(scene: ExplorationScene): string {
  const counts = new Map<string, number>();
  for (const item of scene.decorations) {
    const key = `${item.kind}${item.role ? `:${item.role}` : ""}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const xs = scene.nodes.map((node) => node.anchor.x);
  const ys = scene.nodes.map((node) => node.anchor.y);
  const spread = scene.nodes.length > 1 ? `spread=${Math.round(Math.max(...xs) - Math.min(...xs))}x${Math.round(Math.max(...ys) - Math.min(...ys))}` : "spread=0x0";
  return [...counts.entries()].sort(([a], [b]) => (a < b ? -1 : 1)).map(([key, count]) => `${key}=${count}`).concat(spread).join(" ");
}

export async function presentationFingerprint(scene: ExplorationScene): Promise<string> {
  const bytes = new TextEncoder().encode(presentationStructure(scene));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

/* The renderer (§7i): one scene → SVG, deterministic. The VIEW is the
   picture alone — the frame's rectangle, its defs, its primitives — a
   full-frame image with no paper and no word. The EXPORT is one of the five
   reference forms: the form's paper and perforation, its frame line, the
   same template laid out for its image area, its boxes, and its furniture
   text in the form's faces. No script, no external reference, no date;
   feTurbulence carries a fixed seed. */

import { STAMP_FORMS, type StampForm } from "./forms.ts";
import type { ExplorationScene, SceneDecoration, SceneDef, SceneText } from "./types.ts";

const FONTS = {
  sans: "'Helvetica Neue', Helvetica, Arial, 'Liberation Sans', sans-serif",
  serif: "Georgia, 'Times New Roman', Times, 'Liberation Serif', serif",
  mono: "'Courier New', Courier, 'Liberation Mono', monospace",
};

function xml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}
function n(value: number): string {
  return Number.isFinite(value) ? String(Math.round(value * 10) / 10) : "0";
}

function def(item: SceneDef, prefix: string): string {
  if (item.kind === "linear") {
    return `<linearGradient id="${prefix}${item.id}" x1="${n(item.x1)}" y1="${n(item.y1)}" x2="${n(item.x2)}" y2="${n(item.y2)}">${item.stops.map((s) => `<stop offset="${n(s.offset)}" stop-color="${s.colour}"${s.opacity !== undefined ? ` stop-opacity="${n(s.opacity)}"` : ""}/>`).join("")}</linearGradient>`;
  }
  if (item.kind === "radial") {
    return `<radialGradient id="${prefix}${item.id}" cx="${n(item.cx)}" cy="${n(item.cy)}" r="${n(item.r)}">${item.stops.map((s) => `<stop offset="${n(s.offset)}" stop-color="${s.colour}"${s.opacity !== undefined ? ` stop-opacity="${n(s.opacity)}"` : ""}/>`).join("")}</radialGradient>`;
  }
  /* the grain: turbulence on one 240 px tile, taken to a monochrome alpha, repeated as a pattern —
     the filter is rasterised once per tile, not once per frame */
  return `<filter id="${prefix}${item.id}-filter" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" baseFrequency="${n(item.baseFrequency)}" numOctaves="${item.octaves}" seed="${item.seed}" stitchTiles="stitch" result="noise"/><feColorMatrix in="noise" type="matrix" values="0 0 0 0 0.09  0 0 0 0 0.08  0 0 0 0 0.07  0 0 0 ${n(item.opacity)} 0"/></filter>`
    + `<pattern id="${prefix}${item.id}" width="240" height="240" patternUnits="userSpaceOnUse"><rect width="240" height="240" fill="#000000" filter="url(#${prefix}${item.id}-filter)"/></pattern>`;
}

function fillOf(fill: string, prefix: string, defs: readonly SceneDef[]): string {
  const match = /^url\(#(.+)\)$/.exec(fill);
  if (!match) return fill;
  const id = match[1] as string;
  return `url(#${prefix}${id})`;
}

function decoration(item: SceneDecoration, prefix: string, defs: readonly SceneDef[]): string {
  const opacity = item.opacity !== undefined ? ` opacity="${n(item.opacity)}"` : "";
  const role = item.role ? ` data-role="${item.role}"` : "";
  if (item.kind === "rect" && item.fill.startsWith("url(#") && defs.find((d) => d.id === item.fill.slice(5, -1))?.kind === "grain") {
    return `<rect x="${n(item.x)}" y="${n(item.y)}" width="${n(item.width)}" height="${n(item.height)}" fill="url(#${prefix}${item.fill.slice(5, -1)})"${role}/>`;
  }
  switch (item.kind) {
    case "rect": {
      const stroke = item.stroke ? ` stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.strokeWidth ?? 2)}"` : "";
      const rotate = item.rotate ? ` transform="rotate(${n(item.rotate)} ${n(item.x + item.width / 2)} ${n(item.y + item.height / 2)})"` : "";
      return `<rect x="${n(item.x)}" y="${n(item.y)}" width="${n(item.width)}" height="${n(item.height)}" fill="${fillOf(item.fill, prefix, defs)}"${stroke}${rotate}${opacity}${role}/>`;
    }
    case "circle": {
      const stroke = item.stroke ? ` stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.strokeWidth ?? 2)}"` : "";
      return `<circle cx="${n(item.cx)}" cy="${n(item.cy)}" r="${n(item.r)}" fill="${fillOf(item.fill, prefix, defs)}"${stroke}${opacity}${role}/>`;
    }
    case "line":
      return `<line x1="${n(item.x1)}" y1="${n(item.y1)}" x2="${n(item.x2)}" y2="${n(item.y2)}" stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.width)}"${opacity}${role}/>`;
    case "polygon": {
      const stroke = item.stroke ? ` stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.strokeWidth ?? 2)}" stroke-linejoin="miter"` : "";
      return `<polygon points="${item.points.map((p) => `${n(p.x)},${n(p.y)}`).join(" ")}" fill="${fillOf(item.fill, prefix, defs)}"${stroke}${opacity}${role}/>`;
    }
    case "path": {
      const stroke = item.stroke ? ` stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.strokeWidth ?? 2)}" stroke-linejoin="round" stroke-linecap="butt"` : "";
      return `<path d="${item.d}" fill="${fillOf(item.fill, prefix, defs)}"${stroke}${opacity}${role}/>`;
    }
    case "cross": {
      const h = item.size / 2;
      return `<path d="M${n(item.cx - h)} ${n(item.cy)}H${n(item.cx + h)}M${n(item.cx)} ${n(item.cy - h)}V${n(item.cy + h)}" stroke="${fillOf(item.stroke, prefix, defs)}" stroke-width="${n(item.width)}" fill="none"${opacity}${role}/>`;
    }
    default:
      return "";
  }
}

/* the picture: defs, the frame's ground, the clipped and free primitives, the terms' and associations' regions */
function picture(scene: ExplorationScene, prefix: string): string {
  const F = scene.frame;
  /* the primitives in the order the template drew them; each run of clipped ones in one clip group */
  let body = "";
  let open = false;
  for (const item of scene.decorations) {
    const wants = item.clip === true;
    if (wants !== open) { body += open ? "</g>" : `<g clip-path="url(#${prefix}frame)">`; open = wants; }
    body += decoration(item, prefix, scene.defs);
  }
  if (open) body += "</g>";
  const terms = scene.nodes.map((item) => `<g data-term="${xml(item.vocabularyId)}" data-index="${item.index}"${item.focused ? ' data-focused="true"' : ""}><rect x="${n(item.region.x)}" y="${n(item.region.y)}" width="${n(item.region.width)}" height="${n(item.region.height)}" fill="none" stroke="none" pointer-events="none"/></g>`).join("");
  const associations = scene.connectors.map((item) => `<g data-association="${xml(item.associationId)}"><rect x="${n(item.region.x)}" y="${n(item.region.y)}" width="${n(item.region.width)}" height="${n(item.region.height)}" fill="none" stroke="none" pointer-events="none"/></g>`).join("");
  return `<defs><clipPath id="${prefix}frame"><rect x="${n(F.x)}" y="${n(F.y)}" width="${n(F.width)}" height="${n(F.height)}"/></clipPath>${scene.defs.map((item) => def(item, prefix)).join("")}</defs>`
    + `<rect x="${n(F.x)}" y="${n(F.y)}" width="${n(F.width)}" height="${n(F.height)}" fill="${scene.fieldFill}" data-role="ground"/>`
    + `<g data-layer="picture">${body}</g>`
    + `<g data-layer="terms">${terms}</g>`
    + `<g data-layer="associations">${associations}</g>`;
}

export function renderExplorationViewSvg(scene: ExplorationScene): string {
  const F = scene.frame;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${n(F.x)} ${n(F.y)} ${n(F.width)} ${n(F.height)}" width="${n(F.width)}" height="${n(F.height)}" role="img" aria-label="${xml(scene.altText)}" data-presentation="${scene.presentationVersion}" data-template="${scene.templateId}" data-variant="${scene.variantId}">${picture(scene, "v-")}</svg>`;
}

function perforation(form: StampForm): string {
  const { x, y, width, height } = form.sheet;
  const { kind, radius, pitch } = form.perforation;
  const holes: string[] = [];
  const cols = Math.round(width / pitch);
  const rows = Math.round(height / pitch);
  const r = kind === "wave" ? radius : radius;
  for (let i = 0; i <= cols; i += 1) {
    const cx = x + (i * width) / cols;
    holes.push(`<circle cx="${n(cx)}" cy="${n(y)}" r="${r}"/>`, `<circle cx="${n(cx)}" cy="${n(y + height)}" r="${r}"/>`);
  }
  for (let j = 1; j < rows; j += 1) {
    const cy = y + (j * height) / rows;
    holes.push(`<circle cx="${n(x)}" cy="${n(cy)}" r="${r}"/>`, `<circle cx="${n(x + width)}" cy="${n(cy)}" r="${r}"/>`);
  }
  return holes.join("");
}

function text(item: SceneText): string {
  const spacing = item.letterSpacing ? ` letter-spacing="${n(item.letterSpacing)}"` : "";
  const rotate = item.rotate ? ` transform="rotate(${n(item.rotate)} ${n(item.x)} ${n(item.y)})"` : "";
  return `<text x="${n(item.x)}" y="${n(item.y)}" font-family="${FONTS[item.font]}" font-size="${n(item.size)}" font-weight="${item.weight}" text-anchor="${item.anchor}" fill="${item.colour}"${spacing}${rotate} data-role="${item.role}">${xml(item.text)}</text>`;
}

/* the export: the form around the picture laid out for its image area */
export function renderExplorationExportSvg(scene: ExplorationScene, formId: keyof typeof STAMP_FORMS, furniture: readonly SceneText[]): string {
  const form = STAMP_FORMS[formId];
  const sheet = form.sheet;
  const frame = form.frame ? `<rect x="${n(form.frame.box.x)}" y="${n(form.frame.box.y)}" width="${n(form.frame.box.width)}" height="${n(form.frame.box.height)}" fill="none" stroke="${form.ink}" stroke-width="${n(form.frame.stroke)}"/>` : "";
  const boxes = form.boxes.map((item) => `<rect x="${n(item.box.x)}" y="${n(item.box.y)}" width="${n(item.box.width)}" height="${n(item.box.height)}" fill="${item.fill ?? "none"}" stroke="${form.ink}" stroke-width="${n(item.stroke)}"/>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${form.width}" height="${form.height}" viewBox="0 0 ${form.width} ${form.height}" role="img" aria-label="${xml(scene.altText)}" data-presentation="${scene.presentationVersion}" data-template="${scene.templateId}" data-variant="${scene.variantId}" data-form="${form.id}">`
    + `<rect width="${form.width}" height="${form.height}" fill="${form.ground}"/>`
    + `<rect x="${n(sheet.x)}" y="${n(sheet.y)}" width="${n(sheet.width)}" height="${n(sheet.height)}" fill="${form.paper}"/>`
    + `<g fill="${form.ground}">${perforation(form)}</g>`
    + picture(scene, "e-")
    + frame
    + boxes
    + `<g data-layer="furniture">${furniture.map(text).join("")}</g>`
    + `</svg>`;
}

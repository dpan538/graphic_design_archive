import "server-only";

import sharp from "sharp";
import { EXPLORATION_V2_THEME_TOKENS } from "./theme-tokens.ts";
import type {
  ExplorationV2ExportManifestDto,
  ExplorationV2MapNodeDto,
} from "./types.ts";

const PNG_RENDER_CONCURRENCY = 2;
const PNG_RENDER_QUEUE_LIMIT = 32;
const PNG_RENDER_WAIT_MILLISECONDS = 10_000;

interface RenderWaiter {
  readonly resolve: (release: () => void) => void;
  readonly reject: (error: RenderCapacityError) => void;
  readonly timer: ReturnType<typeof setTimeout>;
}

class BoundedRenderSemaphore {
  private active = 0;
  private readonly waiters: RenderWaiter[] = [];

  constructor(
    private readonly concurrency: number,
    private readonly queueLimit: number,
  ) {}

  async acquire(): Promise<() => void> {
    if (this.active < this.concurrency) {
      this.active += 1;
      return this.releasePermit();
    }
    if (this.waiters.length >= this.queueLimit) throw new RenderCapacityError();
    return new Promise<() => void>((resolve, reject) => {
      const waiter: RenderWaiter = {
        resolve,
        reject,
        timer: setTimeout(() => {
          const index = this.waiters.indexOf(waiter);
          if (index >= 0) this.waiters.splice(index, 1);
          reject(new RenderCapacityError());
        }, PNG_RENDER_WAIT_MILLISECONDS),
      };
      this.waiters.push(waiter);
    });
  }

  private releasePermit(): () => void {
    let released = false;
    return () => {
      if (released) return;
      released = true;
      const next = this.waiters.shift();
      if (next) {
        clearTimeout(next.timer);
        next.resolve(this.releasePermit());
        return;
      }
      this.active = Math.max(0, this.active - 1);
    };
  }
}

const renderSemaphore = new BoundedRenderSemaphore(PNG_RENDER_CONCURRENCY, PNG_RENDER_QUEUE_LIMIT);

export class RenderCapacityError extends Error {
  constructor() {
    super("PNG_RENDER_CAPACITY_EXCEEDED");
    this.name = "RenderCapacityError";
  }
}

function xml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function wrapLabel(label: string, maximumCodePoints: number): readonly string[] {
  const words = label.split(/\s+/u).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const proposed = current ? `${current} ${word}` : word;
    if ([...proposed].length <= maximumCodePoints || current.length === 0) current = proposed;
    else {
      lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines.flatMap((line) => {
    const points = [...line];
    if (points.length <= maximumCodePoints) return [line];
    const chunks: string[] = [];
    for (let index = 0; index < points.length; index += maximumCodePoints) {
      chunks.push(points.slice(index, index + maximumCodePoints).join(""));
    }
    return chunks;
  });
}

function wrapTreeLine(line: string): readonly string[] {
  const points = [...line];
  if (points.length <= 58) return [line];
  const lines: string[] = [points.slice(0, 58).join("")];
  for (let index = 58; index < points.length; index += 54) {
    lines.push(`    ${points.slice(index, index + 54).join("")}`);
  }
  return lines;
}

function mapX(node: ExplorationV2MapNodeDto): number {
  return 136 + (node.position.normalised_x * 808);
}

function mapY(node: ExplorationV2MapNodeDto): number {
  return 216 + (node.position.normalised_y * 500);
}

export function renderExplorationV2Svg(manifest: ExplorationV2ExportManifestDto): string {
  if (manifest.dimensions.width !== 1080 || manifest.dimensions.height !== 1620 || manifest.export_preset !== "portrait_card") {
    throw new Error("EXPORT_RENDER_CONTRACT_MISMATCH");
  }
  if (manifest.nodes.length < 1 || manifest.nodes.length > 8 || manifest.plain_text_tree.tree_node_ids.length !== manifest.nodes.length) {
    throw new Error("EXPORT_RENDER_CONTENT_MISMATCH");
  }
  const theme = EXPLORATION_V2_THEME_TOKENS[manifest.theme_token_set];
  const nodeById = new Map(manifest.nodes.map((node) => [node.vocabulary_id, node]));
  const edgeMarkup = manifest.associations.map((association) => {
    const [leftId, rightId] = association.endpoint_vocabulary_ids;
    const left = nodeById.get(leftId);
    const right = nodeById.get(rightId);
    if (!left || !right) throw new Error("EXPORT_RENDER_EDGE_MISMATCH");
    return `<line x1="${mapX(left)}" y1="${mapY(left)}" x2="${mapX(right)}" y2="${mapY(right)}" stroke="${theme.connector}" stroke-width="3" />`;
  }).join("");
  const nodeMarkup = manifest.nodes.map((node) => {
    const x = mapX(node);
    const y = mapY(node);
    const lines = wrapLabel(node.canonical_label, 18);
    const fontSize = lines.length > 3 ? 17 : 20;
    const lineHeight = fontSize + 3;
    const firstOffset = -((lines.length - 1) * lineHeight) / 2;
    const labelMarkup = lines.map((line, index) => (
      `<tspan x="${x}" dy="${index === 0 ? firstOffset : lineHeight}">${xml(line)}</tspan>`
    )).join("");
    const fill = node.expanded ? theme.expandedNodeFill : theme.nodeFill;
    const stroke = node.focused ? theme.focusStroke : theme.nodeStroke;
    const strokeWidth = node.focused ? 6 : 3;
    return `<g aria-label="${xml(node.canonical_label)}"><circle cx="${x}" cy="${y}" r="62" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}"/><text x="${x}" y="${y + 7}" text-anchor="middle" font-family="${theme.fontFamily}" font-size="${fontSize}" fill="${theme.ink}">${labelMarkup}</text></g>`;
  }).join("");

  const treeLines = manifest.plain_text_tree.plain_text_tree.split("\n").flatMap(wrapTreeLine);
  if (treeLines.length === 0 || treeLines.length > 18) throw new Error("EXPORT_RENDER_TREE_BOUND_MISMATCH");
  const treeFontSize = treeLines.length > 14 ? 18 : treeLines.length > 10 ? 21 : 25;
  const treeLineHeight = treeLines.length > 14 ? 24 : treeLines.length > 10 ? 28 : 34;
  const treeMarkup = treeLines.map((line, index) => (
    `<tspan x="112" dy="${index === 0 ? 0 : treeLineHeight}">${xml(line)}</tspan>`
  )).join("");
  const categoryLabel = manifest.category.entry_label ?? manifest.category.label;

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1620" viewBox="0 0 1080 1620" role="img" aria-label="${xml(manifest.export_alt_text)}">
  <rect width="1080" height="1620" fill="${theme.background}"/>
  <rect x="72" y="72" width="936" height="1476" rx="22" fill="${theme.panel}" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="132" font-family="${theme.fontFamily}" font-size="22" letter-spacing="2" fill="${theme.mutedInk}">TRACE EXPLORATION · ${xml(categoryLabel.toUpperCase())}</text>
  <g aria-label="Qualified generic-association map">${edgeMarkup}${nodeMarkup}</g>
  <line x1="112" y1="832" x2="968" y2="832" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="892" font-family="${theme.fontFamily}" font-size="20" letter-spacing="1.5" fill="${theme.mutedInk}">PLAIN-TEXT TREE</text>
  <text x="112" y="950" font-family="${theme.treeFontFamily}" font-size="${treeFontSize}" fill="${theme.ink}" xml:space="preserve">${treeMarkup}</text>
  <line x1="112" y1="1432" x2="968" y2="1432" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="1482" font-family="${theme.fontFamily}" font-size="18" fill="${theme.mutedInk}">${xml(categoryLabel)} · ${manifest.node_count} terms · ${manifest.association_count} associations · ${xml(manifest.export_id)}</text>
  <text x="112" y="1514" font-family="${theme.fontFamily}" font-size="16" fill="${theme.mutedInk}">evidence-qualified; no typed relation</text>
</svg>`;
}

export async function renderExplorationV2Png(manifest: ExplorationV2ExportManifestDto): Promise<Buffer> {
  const release = await renderSemaphore.acquire();
  try {
    const svg = renderExplorationV2Svg(manifest);
    return await sharp(Buffer.from(svg, "utf8"), { density: 144, limitInputPixels: 20_000_000 })
      .resize(1080, 1620, { fit: "fill" })
      .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
      .toBuffer();
  } finally {
    release();
  }
}

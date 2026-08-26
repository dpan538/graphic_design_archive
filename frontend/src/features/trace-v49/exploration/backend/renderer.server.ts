import sharp from "sharp";
import { EXPLORATION_THEME_TOKENS } from "./theme-tokens.ts";
import type { ExplorationThemeTokenSet } from "./types.ts";

function xml(value: unknown): string {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}
function safeNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}
function wrapLabel(label: string, maximumCodePoints: number): string[] {
  const words = label.split(/\s+/u).filter(Boolean);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const proposed = line ? `${line} ${word}` : word;
    if ([...proposed].length <= maximumCodePoints || !line) line = proposed;
    else { lines.push(line); line = word; }
  }
  if (line) lines.push(line);
  return lines.flatMap((item) => {
    const points = [...item];
    if (points.length <= maximumCodePoints) return [item];
    const chunks: string[] = [];
    for (let index = 0; index < points.length; index += maximumCodePoints) chunks.push(points.slice(index, index + maximumCodePoints).join(""));
    return chunks;
  });
}

export function renderExplorationSvg(manifest: any): string {
  const width = safeNumber(manifest.dimensions?.width, 1080);
  const height = safeNumber(manifest.dimensions?.height, 1620);
  const theme = EXPLORATION_THEME_TOKENS[manifest.theme_token_set as ExplorationThemeTokenSet];
  if (!theme || width !== 1080 || height !== 1620) throw new Error("EXPORT_RENDER_CONTRACT_MISMATCH");
  const nodes = manifest.map_region?.nodes ?? [];
  const nodeById = new Map<string, any>(nodes.map((item: any) => [item.vocabulary_id, item]));
  const mapX = (node: any) => 112 + safeNumber(node.projection?.normalised_x, 0.5) * 856;
  const mapY = (node: any) => 178 + safeNumber(node.projection?.normalised_y, 0.5) * 566;
  const edges = (manifest.map_region?.associations ?? []).map((association: any) => {
    const [a, b] = association.endpoint_vocabulary_ids;
    const source = nodeById.get(a);
    const target = nodeById.get(b);
    return source && target ? `<line x1="${mapX(source)}" y1="${mapY(source)}" x2="${mapX(target)}" y2="${mapY(target)}" stroke="${theme.connector}" stroke-width="3" />` : "";
  }).join("");
  const nodeMarkup = nodes.map((node: any) => {
    const x = mapX(node);
    const y = mapY(node);
    const lines = wrapLabel(String(node.canonical_label), 20).slice(0, 3);
    const text = lines.map((line, index) => `<tspan x="${x}" dy="${index === 0 ? -(lines.length - 1) * 11 : 22}">${xml(line)}</tspan>`).join("");
    return `<g><circle cx="${x}" cy="${y}" r="58" fill="${theme.nodeFill}" stroke="${theme.nodeStroke}" stroke-width="3"/><text x="${x}" y="${y + 7}" text-anchor="middle" font-family="${theme.fontFamily}" font-size="20" fill="${theme.ink}">${text}</text></g>`;
  }).join("");
  const treeLines = String(manifest.plain_text_tree?.plain_text_tree ?? "").split("\n");
  if (!nodes.length || !treeLines.some(Boolean)) throw new Error("EXPORT_EMPTY_ZONE");
  const treeMarkup = treeLines.map((line, index) => `<tspan x="112" dy="${index === 0 ? 0 : 42}">${xml(line)}</tspan>`).join("");
  const category = String(manifest.suggested_filename ?? "trace-exploration").split("-")[1] ?? "exploration";
  const sourceCount = safeNumber(manifest.provenance_summary?.source_count, 0);
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="${width}" height="${height}" fill="${theme.background}"/>
  <rect x="72" y="72" width="936" height="1476" rx="22" fill="${theme.panel}" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="132" font-family="${theme.fontFamily}" font-size="22" letter-spacing="2" fill="${theme.mutedInk}">TRACE EXPLORATION · ${xml(category.toUpperCase())}</text>
  <g aria-label="Qualified generic-association map">${edges}${nodeMarkup}</g>
  <line x1="112" y1="832" x2="968" y2="832" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="892" font-family="${theme.fontFamily}" font-size="20" letter-spacing="1.5" fill="${theme.mutedInk}">PLAIN-TEXT TREE</text>
  <text x="112" y="956" font-family="${theme.fontFamily}" font-size="30" fill="${theme.ink}" xml:space="preserve">${treeMarkup}</text>
  <line x1="112" y1="1432" x2="968" y2="1432" stroke="${theme.divider}" stroke-width="2"/>
  <text x="112" y="1490" font-family="${theme.fontFamily}" font-size="18" fill="${theme.mutedInk}">${xml(category)} · ${sourceCount} sources · ${xml(manifest.export_id)}</text>
</svg>`;
}

export async function renderExplorationPng(manifest: any): Promise<Buffer> {
  return sharp(Buffer.from(renderExplorationSvg(manifest), "utf8"), { density: 144, limitInputPixels: 20_000_000 })
    .resize(manifest.dimensions.width, manifest.dimensions.height, { fit: "fill" })
    .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
    .toBuffer();
}

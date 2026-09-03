import "server-only";

import registryJson from "../../../generated/visual-registry-v49/registry.json";
import manifestJson from "../../../generated/visual-registry-v49/manifest.json";
import { getPublicSearchIndex } from "@/features/search-v2/index.server";

/* The visual registry — the only source of MGDA_DISPLAYABLE_VISUAL. Hand-
   promoted with evidence (§3c/§3d); zero entries in v49. An Object page
   renders an image only for a record listed here. */

export type VisualRegistryEntry = { stableId: string; imageUrl: string; host: string; licence: string; attribution: string; sourceUrl: string; promotedAt: string; reviewer: string };

type Registry = { format: string; release_id: string; entries: readonly (readonly [string, string, string, string, string, string, string, string, unknown])[] };
type Manifest = { release_id: string; count: number };

let cached: ReadonlyMap<string, VisualRegistryEntry> | null = null;

export function getVisualRegistry(): ReadonlyMap<string, VisualRegistryEntry> {
  if (cached) return cached;
  const registry = registryJson as unknown as Registry;
  const manifest = manifestJson as unknown as Manifest;
  const search = getPublicSearchIndex();
  if (registry.format !== "gda-visual-registry-v1" || registry.release_id !== manifest.release_id || manifest.release_id !== search.manifest.release_id || registry.entries.length !== manifest.count) {
    throw new Error("visual registry failed its release or count gate");
  }
  const map = new Map<string, VisualRegistryEntry>();
  for (const [stableId, imageUrl, host, licence, attribution, sourceUrl, promotedAt, reviewer] of registry.entries) {
    if (!search.byId.has(stableId)) throw new Error(`visual registry lists ${stableId}, which is not a public document`);
    if (!/^https:\/\//.test(imageUrl)) throw new Error(`visual registry entry ${stableId} has a non-https image URL`);
    map.set(stableId, { stableId, imageUrl, host, licence, attribution, sourceUrl, promotedAt, reviewer });
  }
  cached = map;
  return cached;
}

export function visualRegistryEntryOf(stableId: string): VisualRegistryEntry | null {
  return getVisualRegistry().get(stableId) ?? null;
}

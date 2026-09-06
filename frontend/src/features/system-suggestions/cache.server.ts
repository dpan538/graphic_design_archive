import "server-only";

/* The guidance cache (release pass): one verified response per fact
   identity — surface · release/data version · context fingerprint · prompt
   version · language · model configuration — bounded, expiring, with
   in-flight requests for the same identity merged into one provider call
   and a LAST-GOOD copy kept longer so a provider failure can answer with
   the same facts' verified note rather than nothing. Nothing here stores a
   raw query: Search keys are fingerprints and expire in minutes. */

import type { SystemSuggestionsResponse } from "./types";

export interface GuidanceCacheKeyParts {
  readonly surface: string;
  readonly releaseVersion: string;
  readonly contextFingerprint: string;
  readonly promptVersion: string;
  readonly language: string;
  readonly modelConfigVersion: string;
}

interface Entry { readonly value: SystemSuggestionsResponse; readonly expiresAt: number; readonly storedAt: number }

const MAX_ENTRIES = 500;
const LAST_GOOD_TTL_MS = 6 * 60 * 60_000;
const entries = new Map<string, Entry>();
const lastGood = new Map<string, Entry>();
const inFlight = new Map<string, Promise<SystemSuggestionsResponse>>();
let stats = { hits: 0, misses: 0, merged: 0, lastGoodServed: 0, stored: 0 };

export function guidanceCacheKey(parts: GuidanceCacheKeyParts): string {
  return [parts.surface, parts.releaseVersion, parts.contextFingerprint, parts.promptVersion, parts.language, parts.modelConfigVersion].join("|");
}

function sweep(map: Map<string, Entry>, now: number): void {
  for (const [key, entry] of map) if (entry.expiresAt <= now) map.delete(key);
  while (map.size > MAX_ENTRIES) {
    const oldest = map.keys().next().value;
    if (oldest === undefined) break;
    map.delete(oldest);
  }
}

export function readGuidanceCache(key: string, now = Date.now()): SystemSuggestionsResponse | null {
  const entry = entries.get(key);
  if (entry && entry.expiresAt > now) { stats.hits += 1; return entry.value; }
  if (entry) entries.delete(key);
  stats.misses += 1;
  return null;
}

export function readLastGoodGuidance(key: string, now = Date.now()): SystemSuggestionsResponse | null {
  const entry = lastGood.get(key);
  if (entry && entry.expiresAt > now) { stats.lastGoodServed += 1; return entry.value; }
  if (entry) lastGood.delete(key);
  return null;
}

export function storeGuidance(key: string, value: SystemSuggestionsResponse, ttlMs: number, now = Date.now()): void {
  entries.delete(key);
  entries.set(key, { value, expiresAt: now + ttlMs, storedAt: now });
  lastGood.delete(key);
  lastGood.set(key, { value, expiresAt: now + LAST_GOOD_TTL_MS, storedAt: now });
  stats.stored += 1;
  sweep(entries, now);
  sweep(lastGood, now);
}

/* one provider call per identity at a time: later callers await the first */
export async function mergeInFlight(key: string, work: () => Promise<SystemSuggestionsResponse>): Promise<SystemSuggestionsResponse> {
  const pending = inFlight.get(key);
  if (pending) { stats.merged += 1; return pending; }
  const promise = work().finally(() => { inFlight.delete(key); });
  inFlight.set(key, promise);
  return promise;
}

export function guidanceCacheStatsForTest(): Readonly<typeof stats & { entries: number; lastGood: number; inFlight: number }> {
  return { ...stats, entries: entries.size, lastGood: lastGood.size, inFlight: inFlight.size };
}

export function resetGuidanceCacheForTest(): void {
  if (process.env.NODE_ENV === "production") throw new Error("cache reset is test-only");
  entries.clear();
  lastGood.clear();
  inFlight.clear();
  stats = { hits: 0, misses: 0, merged: 0, lastGoodServed: 0, stored: 0 };
}

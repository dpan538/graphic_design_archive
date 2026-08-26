import type { ExplorationActionRequest, ExplorationExportRequest, ExplorationMapRequest } from "./backend/types.ts";

export class TraceExplorationApiError extends Error {
  constructor(readonly status: number, readonly payload: unknown) {
    super(`TRACE Exploration API request failed with HTTP ${status}`);
  }
}
export interface TraceExplorationClientOptions { readonly baseUrl?: string; readonly fetchImpl?: typeof fetch; }

export function createTraceExplorationClient(options: TraceExplorationClientOptions = {}) {
  const base = (options.baseUrl ?? "/api/trace/v1/exploration").replace(/\/$/u, "");
  const fetchImpl = options.fetchImpl ?? fetch;
  async function request(path: string, init?: RequestInit): Promise<any> {
    const result = await fetchImpl(`${base}${path}`, init);
    if (!result.ok) throw new TraceExplorationApiError(result.status, await result.json());
    return result.json();
  }
  return Object.freeze({
    categories: () => request("/categories"),
    capabilities: () => request("/capabilities"),
    createMap: (input: ExplorationMapRequest) => request("/maps", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
    retrieveMap: (mapId: string, stateId?: string) => request(`/maps/${encodeURIComponent(mapId)}${stateId ? `?state_id=${encodeURIComponent(stateId)}` : ""}`),
    applyAction: (mapId: string, input: ExplorationActionRequest) => request(`/maps/${encodeURIComponent(mapId)}/actions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
    vocabulary: (vocabularyId: string) => request(`/vocabulary/${encodeURIComponent(vocabularyId)}`),
    association: (associationId: string) => request(`/associations/${encodeURIComponent(associationId)}`),
    exportManifest: (input: ExplorationExportRequest) => request("/exports/manifest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }),
    exportPng: async (input: ExplorationExportRequest) => {
      const result = await fetchImpl(`${base}/exports/png`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
      if (!result.ok) throw new TraceExplorationApiError(result.status, await result.json());
      return Object.freeze({ blob: await result.blob(), headers: result.headers });
    },
  });
}

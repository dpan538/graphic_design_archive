import type {
  ExplorationV2ActionRequest,
  ExplorationV2ApiError,
  ExplorationV2AssociationResponse,
  ExplorationV2CapabilitiesResponse,
  ExplorationV2CategoriesResponse,
  ExplorationV2ExportManifestDto,
  ExplorationV2ExportRequest,
  ExplorationV2MapDto,
  ExplorationV2MapRequest,
  ExplorationV2VocabularyResponse,
} from "./types.ts";

export interface TraceExplorationV2ClientOptions {
  readonly baseUrl?: string;
  readonly fetchImpl?: typeof fetch;
}

export interface TraceExplorationV2PngResponse {
  readonly blob: Blob;
  readonly headers: Headers;
}

export interface TraceExplorationV2SvgResponse {
  readonly svg: string;
  readonly headers: Headers;
}

export class TraceExplorationV2ApiError extends Error {
  constructor(
    readonly status: number,
    readonly payload: ExplorationV2ApiError | undefined,
  ) {
    super(payload?.message ?? `TRACE Exploration API request failed with HTTP ${status}`);
    this.name = "TraceExplorationV2ApiError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isApiError(value: unknown): value is ExplorationV2ApiError {
  return isRecord(value)
    && value.schema_version === "trace-exploration-api-error-v2"
    && typeof value.code === "string"
    && typeof value.message === "string"
    && typeof value.status === "number"
    && typeof value.retryable === "boolean"
    && typeof value.instance === "string"
    && typeof value.database_snapshot === "string";
}

async function readUnknownJson(response: Response): Promise<unknown> {
  try {
    return await response.json() as unknown;
  } catch {
    return undefined;
  }
}

export function createTraceExplorationV2Client(options: TraceExplorationV2ClientOptions = {}) {
  const base = (options.baseUrl ?? "/api/trace/v2/exploration").replace(/\/$/u, "");
  const fetchImpl = options.fetchImpl ?? fetch;

  async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetchImpl(`${base}${path}`, init);
    const payload = await readUnknownJson(response);
    if (!response.ok) throw new TraceExplorationV2ApiError(response.status, isApiError(payload) ? payload : undefined);
    return payload as T;
  }

  function postJson<T>(path: string, body: unknown): Promise<T> {
    return requestJson<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  return Object.freeze({
    categories: (): Promise<ExplorationV2CategoriesResponse> => requestJson("/categories"),
    capabilities: (): Promise<ExplorationV2CapabilitiesResponse> => requestJson("/capabilities"),
    createMap: (input: ExplorationV2MapRequest): Promise<ExplorationV2MapDto> => postJson("/maps", input),
    retrieveMap: (mapId: string, stateId?: string): Promise<ExplorationV2MapDto> => {
      const query = stateId ? `?state_id=${encodeURIComponent(stateId)}` : "";
      return requestJson(`/maps/${encodeURIComponent(mapId)}${query}`);
    },
    applyAction: (mapId: string, input: ExplorationV2ActionRequest): Promise<ExplorationV2MapDto> => (
      postJson(`/maps/${encodeURIComponent(mapId)}/actions`, input)
    ),
    vocabulary: (vocabularyId: string): Promise<ExplorationV2VocabularyResponse> => (
      requestJson(`/vocabulary/${encodeURIComponent(vocabularyId)}`)
    ),
    association: (associationId: string): Promise<ExplorationV2AssociationResponse> => (
      requestJson(`/associations/${encodeURIComponent(associationId)}`)
    ),
    exportManifest: (input: ExplorationV2ExportRequest): Promise<ExplorationV2ExportManifestDto> => (
      postJson("/exports/manifest", input)
    ),
    exportSvg: async (input: ExplorationV2ExportRequest): Promise<TraceExplorationV2SvgResponse> => {
      const response = await fetchImpl(`${base}/export/svg`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!response.ok) {
        const payload = await readUnknownJson(response);
        throw new TraceExplorationV2ApiError(response.status, isApiError(payload) ? payload : undefined);
      }
      if (response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase() !== "image/svg+xml") {
        throw new TraceExplorationV2ApiError(response.status, undefined);
      }
      return { svg: await response.text(), headers: response.headers };
    },
    exportPng: async (input: ExplorationV2ExportRequest): Promise<TraceExplorationV2PngResponse> => {
      const response = await fetchImpl(`${base}/exports/png`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!response.ok) {
        const payload = await readUnknownJson(response);
        throw new TraceExplorationV2ApiError(response.status, isApiError(payload) ? payload : undefined);
      }
      return { blob: await response.blob(), headers: response.headers };
    },
  });
}

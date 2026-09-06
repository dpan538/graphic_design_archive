import "server-only";

import { NextResponse } from "next/server";
import { renderExplorationScenePng } from "./render.server.ts";
import {
  applyExplorationViewAction,
  createExplorationView,
  createExplorationViewExportManifest,
  listExplorationStartingPoints,
  renderExplorationExport,
  retrieveExplorationView,
} from "./service.server.ts";
import { EXPLORATION_VIEW_API_VERSION, type ExplorationViewApiError, type ExplorationViewErrorCode, type ExplorationViewResult } from "./types.ts";

/* /api/trace/exploration-view/v1 — the view API (§7i), a thin HTTP layer
   over the service: starting-points · views · views/{map} · views/{map}/actions
   · exports/{manifest|svg|png}. JSON bodies are bounded; every failure is a
   JSON problem with the service's code. */

const MAX_BODY_BYTES = 16_384;
const HEADERS = {
  "Cache-Control": "private, no-store, max-age=0",
  "X-Content-Type-Options": "nosniff",
};

function problem(code: ExplorationViewErrorCode, message: string, status: number): Response {
  const body: ExplorationViewApiError = { schema_version: "trace-exploration-view-api-error-v1", api_version: EXPLORATION_VIEW_API_VERSION, code, message, status };
  return NextResponse.json(body, { status, headers: HEADERS });
}

function serviceResponse<T>(result: ExplorationViewResult<T>): Response {
  if (!result.ok) return problem(result.code, result.message, result.status);
  return NextResponse.json(result.data, { headers: HEADERS });
}

async function readJson(request: Request): Promise<unknown> {
  const text = await request.text();
  if (text.length > MAX_BODY_BYTES) throw new Error("REQUEST_LIMIT_EXCEEDED");
  return JSON.parse(text) as unknown;
}

export async function dispatchExplorationViewRequest(request: Request, path: readonly string[]): Promise<Response> {
  const method = request.method;
  try {
    if (path.length === 1 && path[0] === "starting-points" && (method === "GET" || method === "HEAD")) {
      return serviceResponse(listExplorationStartingPoints());
    }
    if (path.length === 1 && path[0] === "views" && method === "POST") {
      return serviceResponse(createExplorationView(await readJson(request)));
    }
    if (path.length === 2 && path[0] === "views" && (method === "GET" || method === "HEAD")) {
      const url = new URL(request.url);
      const variant = url.searchParams.get("variant");
      return serviceResponse(retrieveExplorationView(
        path[1] ?? "",
        url.searchParams.get("state") ?? undefined,
        url.searchParams.get("template") ?? undefined,
        variant === null ? undefined : Number(variant),
      ));
    }
    if (path.length === 3 && path[0] === "views" && path[2] === "actions" && method === "POST") {
      return serviceResponse(applyExplorationViewAction(path[1] ?? "", await readJson(request)));
    }
    if (path.length === 2 && path[0] === "exports" && method === "POST") {
      const body = await readJson(request);
      const result = createExplorationViewExportManifest(body);
      if (!result.ok) return problem(result.code, result.message, result.status);
      const { manifest, scene, furniture } = result.data;
      if (path[1] === "manifest") return NextResponse.json(manifest, { headers: HEADERS });
      if (path[1] === "svg") {
        return new NextResponse(renderExplorationExport(scene, manifest.form_id, furniture), { headers: { ...HEADERS, "Content-Type": "image/svg+xml; charset=utf-8", "X-TRACE-Export-Id": manifest.export_id, "X-TRACE-Render-Version": manifest.render_version, "X-TRACE-Export-Form": manifest.form_id } });
      }
      if (path[1] === "png") {
        try {
          const png = await renderExplorationScenePng(scene, manifest.form_id, furniture);
          return new NextResponse(new Uint8Array(png), {
            headers: {
              ...HEADERS,
              "Content-Type": "image/png",
              "Content-Length": String(png.byteLength),
              "Content-Disposition": `attachment; filename="${manifest.suggested_filename}"`,
              "X-TRACE-Export-Id": manifest.export_id,
              "X-TRACE-Render-Version": manifest.render_version,
              "X-TRACE-Export-Form": manifest.form_id,
            },
          });
        } catch (error) {
          if (error instanceof Error && error.message === "RENDER_CAPACITY_EXCEEDED") return problem("REQUEST_LIMIT_EXCEEDED", "Too many exports are rendering; retry shortly.", 429);
          throw error;
        }
      }
    }
    if (method === "OPTIONS") return new NextResponse(null, { status: 204, headers: { ...HEADERS, Allow: "GET, POST, OPTIONS" } });
    const known = (path.length === 1 && (path[0] === "starting-points" || path[0] === "views"))
      || (path.length === 2 && (path[0] === "views" || path[0] === "exports"))
      || (path.length === 3 && path[0] === "views" && path[2] === "actions");
    if (known) return problem("METHOD_NOT_ALLOWED", "The method is not allowed on this endpoint.", 405);
    return problem("STATE_NOT_FOUND", "The requested endpoint does not exist.", 404);
  } catch (error) {
    if (error instanceof Error && error.message === "REQUEST_LIMIT_EXCEEDED") return problem("REQUEST_LIMIT_EXCEEDED", "The request body is too large.", 413);
    if (error instanceof SyntaxError) return problem("INVALID_REQUEST", "The request body is not valid JSON.", 400);
    return problem("INTERNAL_DATA_INTEGRITY_FAILURE", "The exploration view is unavailable.", 503);
  }
}

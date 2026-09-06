import "server-only";

import sharp from "sharp";
import { EXPORT_SCALE, STAMP_FORMS } from "./forms.ts";
import type { ExplorationFormId, ExplorationScene, SceneText } from "./types.ts";
import { renderExplorationExportSvg } from "./render.ts";

/* the PNG: the export form rasterised at EXPORT_SCALE × its coordinate size */

let inFlight = 0;
const MAX_IN_FLIGHT = 4;

export async function renderExplorationScenePng(scene: ExplorationScene, formId: ExplorationFormId, furniture: readonly SceneText[]): Promise<Buffer> {
  if (inFlight >= MAX_IN_FLIGHT) throw new Error("RENDER_CAPACITY_EXCEEDED");
  inFlight += 1;
  try {
    const form = STAMP_FORMS[formId];
    const svg = renderExplorationExportSvg(scene, formId, furniture);
    return await sharp(Buffer.from(svg, "utf8"), { density: 72 * EXPORT_SCALE, limitInputPixels: 40_000_000 })
      .resize(form.width * EXPORT_SCALE, form.height * EXPORT_SCALE, { fit: "fill" })
      .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
      .toBuffer();
  } finally {
    inFlight -= 1;
  }
}

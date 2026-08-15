import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd(), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const requireText = (path, needle) => {
  if (!read(path).includes(needle)) throw new Error(`${path} is missing ${needle}`);
};
const forbid = (path, needle) => {
  if (read(path).includes(needle)) throw new Error(`${path} must not contain ${needle}`);
};

requireText("frontend/src/lib/read-platform/repository.ts", "interface ArchiveRepository");
requireText("frontend/package.json", "typecheck:runtime");
requireText("frontend/tsconfig.runtime-acceptance.json", "src/app/api/v1/[...path]/route.ts");
requireText("frontend/src/lib/read-platform/server/fixture.ts", "length: 32");
requireText("frontend/src/lib/read-platform/server/fixture.ts", "traceEligibleObjectCount: 0");
requireText("frontend/src/lib/read-platform/server/fixture.ts", "positiveVisualRightsCount: 0");
requireText("frontend/src/lib/read-platform/server/provider.ts", "fixture repository is forbidden in production");
requireText("frontend/src/lib/read-platform/pagination.ts", "researchManifestSha256");
requireText("frontend/src/lib/read-platform/server/postgres-repository.ts", "api_v1.sealed_surface");
for (const path of [
  "frontend/src/app/search/page.tsx",
  "frontend/src/app/folders/[type]/page.tsx",
  "frontend/src/app/folders/[type]/[slug]/page.tsx",
  "frontend/src/app/surfaces/[id]/page.tsx",
  "frontend/src/app/trace/page.tsx",
]) {
  forbid(path, "@/lib/archive-data");
  forbid(path, "trace-v48");
  forbid(path, "archive-search-v1");
}
const api = read("frontend/src/app/api/v1/[...path]/route.ts");
for (const blocked of ["remote_image_url", "raw payload", "held locator", "SELECT *"]) forbid("frontend/src/app/api/v1/[...path]/route.ts", blocked);
if (!api.includes("export function POST") || !api.includes("status: 405")) throw new Error("read API must reject writes");
console.log("READ_PLATFORM_CONTRACT=PASS DIRECT_DATA_COUPLING=0");

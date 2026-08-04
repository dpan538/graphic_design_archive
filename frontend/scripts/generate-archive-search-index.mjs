import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const inputPath = join(root, "src/data/public_surface_mock_v0.json");
const outputPath = join(root, "public/data/archive-search-v1.json");
const payload = JSON.parse(await readFile(inputPath, "utf8"));

const items = payload.surfaces.map((surface) => {
  const folderText = (surface.folders ?? []).map((folder) => folder.title).join(" · ");
  const tableText = (surface.tables ?? [])
    .filter((table) => ["SOURCE", "NORMALIZED", "CLASSIFICATION", "CITATIONS"].includes(table.kind))
    .flatMap((table) => table.rows.map(([label, value]) => `${table.kind} ${label}: ${value}`))
    .join(" · ");
  return [
    surface.surfaceId,
    surface.title,
    surface.creator,
    surface.dateText,
    surface.dateStart,
    surface.placeText,
    surface.objectType,
    surface.medium,
    surface.sourceName,
    surface.surfaceType,
    surface.image?.state ?? "IMG00",
    folderText,
    tableText,
  ];
});

const output = {
  version: "archive-search-v1",
  generatedFrom: "public_surface_mock_v0",
  count: items.length,
  schema: [
    "surfaceId", "title", "creator", "dateText", "dateStart", "placeText", "objectType",
    "medium", "sourceName", "surfaceType", "imageState", "folderText", "tableText",
  ],
  items,
};

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, JSON.stringify(output));
console.log(JSON.stringify({ outputPath, count: items.length }, null, 2));

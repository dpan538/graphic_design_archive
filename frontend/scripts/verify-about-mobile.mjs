import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const read = path => readFileSync(new URL("../" + path, import.meta.url), "utf8");
const page = read("src/app/about/page.tsx"), mobile = read("src/app/about/mobile/AboutMobile.tsx"), content = read("src/app/about/content.ts");
const checks = {
  server_device_split: page.includes("resolveView") && page.includes("AboutMobile"),
  authoritative_populations: ["15,923", "7,995", "7,928"].every(value => content.includes(value)),
  sections_preserved: ["purpose", "methodology", "visual", "scale", "contact", "source", "boundaries"].every(id => mobile.includes(`id="${id}"`)),
  citations: ["APA", "MLA", "Chicago", "Harvard"].every(style => content.includes(`style: "${style}"`)) && mobile.includes("navigator.clipboard"),
  official_origin: content.includes('"https://mgdarchive.com"'),
  source_entry: read("src/app/source/page.tsx").includes('focus="source"'),
  evidence_boundaries: mobile.includes("claimBoundaries") && content.includes("no image-display rights") && content.includes("System suggestions"),
  public_path_no_old_dashboard: !page.includes("MobileResearchDashboard") && !page.includes("trace-v48"),
};
console.log(JSON.stringify({candidate:"current-redesign",test_nature:"UNIT",checks},null,2));
assert(Object.values(checks).every(Boolean), "current About mobile contract");

import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

/* The device-split contract (§4a; owner 2026-09-06): the phone and the
   desktop are two trees that share only lib/ and content. A change under a
   mobile file can reach the desktop only through an import, a stylesheet,
   or a shared module — so this audit checks all three directions statically:
   no desktop file imports a mobile file or a mobile stylesheet; no mobile
   file imports a desktop file or the desktop nav; no shared module (lib,
   content, non-mobile site components, the global stylesheet) imports or
   names anything mobile; and the one shared scene keeps its desktop
   behaviour when the mobile-only prop is absent. */
const src = new URL("../src/", import.meta.url).pathname;
const walk = (dir) => readdirSync(dir).flatMap((name) => { const path = join(dir, name); return statSync(path).isDirectory() ? walk(path) : [path]; });
const files = walk(src).filter((path) => /\.(tsx?|css)$/.test(path));
const rel = (path) => relative(src, path);
const read = (path) => readFileSync(path, "utf8");
const isMobile = (path) => /\/mobile\//.test(path);
const isDesktop = (path) => /\/desktop\//.test(path) || /components\/site\/SiteNav\.(tsx|module\.css)$/.test(path);
const isShared = (path) => !isMobile(path) && !isDesktop(path) && !/\/page\.tsx$|\/layout\.tsx$|@modal/.test(path);
const importsOf = (source) => [...source.matchAll(/from\s+"([^"]+)"|import\(\s*"([^"]+)"\s*\)|@import\s+"([^"]+)"/g)].map((m) => m[1] ?? m[2] ?? m[3]);
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

for (const path of files) {
  const source = read(path);
  const imports = importsOf(source);
  if (isDesktop(path)) {
    check(!imports.some((i) => /\/mobile\/|site\/mobile|Mobile(Shell|\.module)|SiteNavMobile|TopButton/.test(i)), `${rel(path)} (desktop) imports nothing mobile`);
    check(!/data-nav="mobile"|shell\.shell/.test(source), `${rel(path)} (desktop) names no mobile shell or bar`);
  }
  if (isMobile(path)) {
    check(!imports.some((i) => /\/desktop\/|components\/site\/SiteNav"|SiteNav\.module/.test(i)), `${rel(path)} (mobile) imports nothing desktop`);
  }
  if (isShared(path) && /\.(tsx?)$/.test(path)) {
    check(!imports.some((i) => /\/mobile\/|site\/mobile/.test(i)), `${rel(path)} (shared) imports nothing mobile`);
  }
}
/* mobile stylesheets are imported only by mobile files and the mobile site components */
const mobileCss = files.filter((path) => path.endsWith(".module.css") && (isMobile(path) || /components\/site\/mobile\//.test(path)));
for (const css of mobileCss) {
  const base = css.split("/").pop();
  const importers = files.filter((path) => path.endsWith(".tsx") && importsOf(read(path)).some((i) => i.endsWith(base) || i.endsWith(base.replace(/\.css$/, ""))));
  check(importers.every((path) => isMobile(path) || /components\/site\/mobile\//.test(path)), `${rel(css)} is imported only by mobile files (${importers.map(rel).join(", ")})`);
}
/* the global stylesheet knows nothing of the phone */
const globals = read(join(src, "app/globals.css"));
check(!/data-nav="mobile"|\.shell\b|--bar-h|SiteNavMobile|TopButton/.test(globals), "globals.css carries no mobile rule or token");
/* every device-split page renders the mobile tree only inside its mobile branch */
const pages = files.filter((path) => path.endsWith("page.tsx") && /Mobile/.test(read(path)));
for (const page of pages) {
  const source = read(page);
  const splits = /resolveView\(/.test(source) && /view === "mobile"/.test(source);
  const guards = /isLikelyMobileTraceRequest\(\)/.test(source) && /TraceDesktopRequired/.test(source);
  check(splits || guards, `${rel(page)} splits on the device (resolveView branch, or the TRACE mobile guard)`);
}
/* the one shared scene: the desktop never passes the mobile-only prop, and without it the frame is the desktop's own */
const scene = read(join(src, "app/home/lib/ContributionScene.tsx"));
check(/fitWidth && aspect < 1\.35 \? 8\.15 \* \(1\.35 \/ aspect\) : 8\.15/.test(scene), "the scene's frame is 8.15 unless fitWidth is passed");
check(!/fitWidth/.test(read(join(src, "app/home/desktop/sections/ContributionSection.tsx"))), "the desktop never passes fitWidth");
/* the desktop's own status figures are the shared module's, unchanged in value */
check(/from "\.\.\/\.\.\/lib\/statusFigures"/.test(read(join(src, "app/home/desktop/sections/StatusSection.tsx"))), "the desktop status section reads the shared figures");
console.log(`Mobile / desktop coupling audit: ${checks} checks passed`);

import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

/* The mobile design contract (§4a; owner 2026-09-06): the mobile trees are
   their own files, carry the mobile bar (monogram + three icons, no
   wordmark) and the mobile shell tokens, never import the desktop nav or a
   desktop tree; About and Source split by device on the server; the mobile
   About carries every section, the research approach and the design
   rationale among them, with Source folded in; Search runs on the live API;
   the Index opening carries no annotation line; long object titles fold. */
const root = new URL("../src/", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

const walk = (dir) => readdirSync(dir).flatMap((name) => { const path = join(dir, name); return statSync(path).isDirectory() ? walk(path) : [path]; });
const srcDir = new URL(".", root).pathname;
const mobileFiles = walk(srcDir).filter((path) => /\/mobile\/[^/]+\.tsx$/.test(path));
check(mobileFiles.length >= 8, `mobile trees exist (${mobileFiles.length} files)`);
for (const path of mobileFiles) {
  const source = readFileSync(path, "utf8");
  check(!/components\/site\/SiteNav"|from "\.\.\/desktop\/|\/desktop\//.test(source), `${path.slice(srcDir.length)} imports no desktop nav or desktop tree`);
  check(!/@media \(max-width|@media \(min-width/.test(source), `${path.slice(srcDir.length)} switches nothing by width inline`);
}
const roots = ["app/home/mobile/HomeMobile.tsx", "app/directory/mobile/IndexMobile.tsx", "app/search/mobile/SearchMobile.tsx", "app/surfaces/[id]/mobile/ObjectMobile.tsx", "app/about/mobile/AboutMobile.tsx"];
for (const path of roots) {
  const source = read(path);
  check(source.includes("SiteNavMobile") && source.includes("MobileShell.module.css") && source.includes("shell.shell"), `${path} carries the mobile bar and the mobile shell`);
}
const bar = read("components/site/mobile/SiteNavMobile.tsx");
const barCode = bar.replace(/\/\*[\s\S]*?\*\//g, "");
check(!/>\s*Modern Graphic Design|wordmark/.test(barCode) && (barCode.match(/key: "(index|search|about)"/g) ?? []).length === 3 && !/key: "(trace|source)"/.test(barCode), "the mobile bar is the monogram and three icons: Index · Search · About (the wordmark only as the home link's accessible name)");
const desktopNav = read("components/site/SiteNav.tsx");
check(!/SiteNavVariant|mobileHide|variant === "mobile"|variant\?:/.test(desktopNav), "the desktop nav carries no mobile variant");
for (const page of ["app/about/page.tsx", "app/source/page.tsx"]) {
  const source = read(page);
  check(source.includes("resolveView(") && source.includes("AboutMobile"), `${page} splits by device on the server`);
}
check(read("app/source/page.tsx").includes('focus="source"'), "Source on the phone is the About tree opened at Source");
const about = read("app/about/mobile/AboutMobile.tsx");
for (const id of ["purpose", "methodology", "visual", "scale", "contact", "source", "boundaries"]) check(about.includes(`id="${id}"`), `mobile About carries the ${id} section`);
check(/rationaleLead|visualReferences/.test(about) && /methodProse|evidenceProtocol|pipelineStages/.test(about), "the design rationale and the research approach are on the mobile About");
check(/registerGroups|rightsColumns|evidenceStatusLegend|versionRecord/.test(about), "Source's register, rights, evidence status and version are folded into the mobile About");
check(/claimBoundaries/.test(about) && /System suggests/.test(read("app/about/content.ts")), "claim boundaries and the System suggests disclosure stand");
const shell = read("components/site/mobile/MobileShell.module.css");
check(/--paper: #fffdf9/.test(shell) && /--blue: #2b4cff/.test(shell), "the mobile shell is whiter and its spot colours more saturated");
const searchMobile = read("app/search/mobile/SearchMobile.tsx");
check(/useLiveSearch|useSearchGuidance|useSearchFacets/.test(searchMobile) && !/runSearch|suggestFor/.test(searchMobile), "mobile Search runs on the live API and the shared guidance");
check(!/from "\.\.\/lib\/fixture"/.test(read("app/search/mobile/SearchMobileFilters.tsx")), "mobile Search filters use the live dictionaries");
const index = read("app/directory/mobile/IndexMobile.tsx");
check(!/working directory|styles\.lede/.test(index) && /styles\.opening/.test(index), "the Index opening is a plate without an annotation line");
check(!/Designer not recorded|themes\.join/.test(read("app/directory/mobile/IndexMobileDirectory.tsx")), "Index rows are one light line");
check(read("app/surfaces/[id]/mobile/MobileRecord.tsx").includes("MobileTitle") && /line-clamp: 3/.test(read("app/surfaces/[id]/mobile/MobileTitle.module.css")), "long object titles fold to three lines by default");
console.log(`Mobile design contract: ${checks} checks passed`);

import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

/* The mobile design contract (§4a; owner 2026-09-06): the mobile trees are
   their own files, carry the mobile bar (monogram + three icons, no
   wordmark) and the mobile shell tokens, never import the desktop nav or a
   desktop tree; About and Source split by device on the server; the mobile
   About carries every section, the research approach and the design
   rationale among them, with Source folded in; Search runs on the live API;
   the Index opening carries no annotation line; long object titles fold.
   Homepage round (owner 2026-09-06): the phone's homepage is its own tree,
   reuses Contribution's two charts and Research status's three figures and
   three tables from home/lib, enters through Index and Search only, and
   carries no TRACE and no Source entry; Search is a page of its own on the
   phone; the one Top control is shared by About, Index and the homepage. */
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
check(!/styles\.opening(Num)|overflow: hidden/.test(read("app/directory/mobile/IndexMobile.tsx") + read("app/directory/mobile/IndexMobile.module.css").split("/* ---- One sticky control row")[0]) && /figureNum/.test(read("app/directory/mobile/IndexMobile.tsx")), "the Index opening carries two whole figures on the paper, nothing cropped");

/* ---- the homepage ---- */
const home = read("app/home/mobile/HomeMobile.tsx");
const homeCss = read("app/home/mobile/HomeMobile.module.css");
const stage = read("app/home/mobile/ContributionStage.tsx");
check(existsSync(new URL("app/home/lib/ContributionScene.tsx", root)) && existsSync(new URL("app/home/lib/statusFigures.ts", root)) && !existsSync(new URL("app/home/desktop/three/ContributionScene.tsx", root)), "the field scene and the status figures live in home/lib, read by both trees");
check(/import\("\.\.\/lib\/ContributionScene"\)/.test(stage) && /YEAR_TIERS/.test(stage) && /staticFrame=\{reduced\}/.test(stage), "the phone's Contribution reuses the year chart and the desktop's field scene");
check(/CONTRIBUTION_BODY/.test(stage) && /FIELD_TAGLINE/.test(stage) && !/contribText/.test(home), "the paragraph and the tagline sit on the pinned page with the second chart");
check(/PUBLIC\.ribbons|HELD\.ribbons/.test(home) && /RADIAL\.blocks/.test(home) && /stripCols/.test(home), "the phone's Research status reuses the ribbon sheet, the wheel and the year strip");
check(!/STATUS\.bands|STATUS\.sources|STATUS\.types|TableRow/.test(home), "the three tables are gone from the phone (owner, 2026-09-06)");
check(/STATUS_STABLE/.test(home) && /STATUS_OPEN/.test(home) && /<details key=\{list\.id\}/.test(home) && /Ranked by place/.test(home) && home.indexOf("<details") < home.indexOf("RANKED.map"), "the ranked places, Stable and Open fold");
check(/<PinnedFigure className=\{styles\.sheetWrap\}/.test(home) && /<PinnedFigure className=\{styles\.wheelWrap\}/.test(home) && /<PinnedFigure className=\{styles\.stripWrap\}/.test(home) && /ROWS\.map/.test(home) && /r\.cols\[b\]/.test(home) && /var\(--g\) \* \d+ - var\(--b\)/.test(homeCss) && /transform-origin: var\(--axis, 50%\) 50%/.test(homeCss) && /scaleX\(max\(0\.001, var\(--e\)\)\)/.test(homeCss) && /var\(--g\) \* 1\.25 - 0\.3/.test(homeCss) && /var\(--g\) \* 1\.15 - var\(--i\)/.test(homeCss), "each status figure is a pinned page that grows with the scroll and lets go when complete");
check(/SCENE_FROM \+ \(SCENE_TO - SCENE_FROM\) \* local/.test(stage) && !/GROW_MS|performance\.now/.test(stage), "the field is drawn by the scroll inside the pinned Contribution page");
check(!/STATUS_EXITS|ABOUT_EXIT|href="\/source"|href="\/trace"|\/trace"/.test(home) && !/TRACE/.test(home.replace(/\/\*[\s\S]*?\*\//g, "")), "the phone's homepage carries no TRACE and no Source entry");
check(/<Link/.test(bar) && /asOverlay/.test(read("app/@modal/(.)search/page.tsx")), "mobile Search uses the current intercepted ticket and keeps a direct page entry");
check(/IDENTITY_TAGLINE_SETTLED/.test(home) && /lead=\{markedLead\(IDENTITY_P1\)\}/.test(home) && /IDENTITY_MARKS/.test(home) && /\.hl \{/.test(homeCss) && /--black: #0a0a0c/.test(homeCss) && /color: var\(--sky\)/.test(homeCss) && /\.wipe \{/.test(homeCss) && /var\(--p, 0\)/.test(homeCss) && /<br \/>/.test(read("app/home/mobile/IdentityOpening.tsx")), "the opening is one pinned page in the desktop closing's colours: the line broken before 'for', the wipe to white and the two sentences all on the scroll");
check(!/IntersectionObserver|requestAnimationFrame/.test(read("app/home/mobile/useStageProgress.ts")) && /useStageProgress/.test(read("app/home/mobile/PinnedFigure.tsx")) && !existsSync(new URL("app/home/mobile/Reveal.tsx", root)), "stage progress reads the scroll position directly; the figures pin through the same hook");
check(!/addEventListener\("wheel"|scroll-snap|scrollTimeline|animation-timeline/.test(home + homeCss + stage), "no scroll-jacking and no exaggerated scroll choreography");
check(!/Unknown/.test(home), "the homepage prints no Unknown");
check(/top: var\(--bar-h\)/.test(homeCss) && /height: calc\(100dvh - var\(--bar-h\)\)/.test(homeCss) && /--bar-h: 87px/.test(shell), "the pinned stage clears the bar by the shell's bar token");
for (const path of ["app/home/mobile/HomeMobile.tsx", "app/directory/mobile/IndexMobile.tsx", "app/about/mobile/AboutMobile.tsx"]) check(read(path).includes("<TopButton />") && read(path).includes("components/site/mobile/TopButton"), `${path} carries the shared Top control`);
check(!/endTop|showTop/.test(read("app/about/mobile/AboutMobile.tsx")) && !/\.toTop \{/.test(read("app/about/mobile/AboutMobile.module.css")), "About keeps only the shared Top control, no end button");
const barCss = read("components/site/mobile/SiteNavMobile.module.css");
check(/padding: calc\(var\(--s-4\) \+ env\(safe-area-inset-top\)\) var\(--s-4\) var\(--s-4\);/.test(barCss) && /width: 52px;\n  height: 52px;/.test(barCss) && /size=\{28\}/.test(bar), "the bar's logo sits at equal margins, the tiles are 52 px and the icons 28 px");
console.log(`Mobile design contract: ${checks} checks passed`);

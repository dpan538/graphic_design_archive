import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");

const about = read("src/app/about/page.tsx");
const dashboard = read("src/components/archive/about/MobileResearchDashboard.tsx");
const citation = read("src/components/archive/about/ProjectCitationPanel.tsx");
const folderIndex = read("src/components/archive/drawer/FolderTypeSpeedIndex.tsx");
const css = read("src/app/globals.css");
const atlas = JSON.parse(read("public/data/trace-v48/atlas.json"));

const checks = {
  about_uses_frozen_v48_counts:
    atlas.version === "v48" &&
    atlas.counts.activeObjects === 15923 &&
    about.includes("traceAtlas.counts.activeObjects") &&
    about.includes("15,923 source-linked design") &&
    !about.includes("renders 1417 surfaces"),
  mobile_dashboard_is_mobile_only:
    about.includes("<MobileResearchDashboard") &&
    css.includes(".mobile-about-dashboard,\n.about-hero__mobile-copy") &&
    css.includes(".mobile-about-dashboard {\n    display: block;") &&
    dashboard.includes("Evidence before spectacle"),
  dashboard_keeps_inference_boundary:
    dashboard.includes("inferred influence edges") &&
    dashboard.includes("Association is never displayed as historical influence") &&
    atlas.counts.influenceEdges === 0,
  sources_and_design_research_default_collapsed:
    about.includes('<Accordion title="Largest active source routes" kicker="source register">') &&
    about.includes('<Accordion title="Design research register" kicker="references">') &&
    about.includes('<Accordion title="Project ledgers and rulebooks" kicker="references">'),
  repository_and_three_copyable_citations:
    citation.includes("https://github.com/dpan538/graphic_design_archive") &&
    ["APA", "MLA", "IEEE"].every((style) => citation.includes(`style: "${style}"`)) &&
    citation.includes("navigator.clipboard.writeText") &&
    citation.includes('aria-live="polite"'),
  filters_are_bottom_docked_and_available_to_all_folder_axes:
    folderIndex.indexOf('className="region-card-stack"') < folderIndex.indexOf("folder-type-filters") &&
    folderIndex.includes("{isRegion ? (") &&
    folderIndex.includes("<select value={period}") &&
    css.includes("grid-template: minmax(0, 1fr) auto / minmax(0, 1fr)") &&
    css.includes("grid-row: 2"),
  mobile_folder_wheel_is_windowed_and_keeps_adjacent_cards:
    folderIndex.includes("distance > 2") &&
    folderIndex.includes('className="region-card-stack__spacer"') &&
    folderIndex.includes("activeCard") &&
    folderIndex.includes("wheel.scrollTop") &&
    css.includes('.region-card-stack__card[data-distance="1"]') &&
    css.includes("flex: 0 0 8.9rem"),
  touch_palette_is_brighter_and_controls_are_round:
    css.includes("--canvas: #fffaf0") &&
    css.includes("--signal-blue: #145fec") &&
    css.includes("border-radius: 999px") &&
    css.includes("@keyframes mobile-reading-reveal"),
  architecture_reference_is_documented:
    about.includes("Unité d’Habitation") &&
    about.includes("structural reference rather than an image motif"),
};

const failed = Object.entries(checks).filter(([, ok]) => !ok).map(([name]) => name);
console.log(JSON.stringify({ version: atlas.version, checks, failed }, null, 2));
if (failed.length) process.exit(1);

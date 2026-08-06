import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.resolve(here, "..");
const [drawer, regionIndex, home, shell, css, traceCss] = await Promise.all([
  readFile(path.join(frontend, "src/components/archive/drawer/FolderDrawer.tsx"), "utf8"),
  readFile(path.join(frontend, "src/components/archive/drawer/FolderTypeSpeedIndex.tsx"), "utf8"),
  readFile(path.join(frontend, "src/app/page.tsx"), "utf8"),
  readFile(path.join(frontend, "src/components/archive/shell/ArchiveShell.tsx"), "utf8"),
  readFile(path.join(frontend, "src/app/globals.css"), "utf8"),
  readFile(
    path.join(frontend, "src/components/archive/trace/TraceExplorer.module.css"),
    "utf8",
  ),
]);

const checks = {
  desktop_is_research_coordinate_index:
    drawer.includes('className="research-coordinate-index"') &&
    drawer.includes('className="research-coordinate-index__rows"') &&
    drawer.includes("Every route preserves object and source evidence"),
  desktop_rows_keep_direct_routes:
    drawer.includes('className="research-coordinate-row"') &&
    drawer.includes("href={item.href}") &&
    drawer.includes('aria-label="Primary archive coordinates"'),
  desktop_removed_showcase_language_and_mechanics:
    !drawer.includes("Open the archive cabinet") &&
    !drawer.includes("drawer-front") &&
    !drawer.includes("useEffect") &&
    !drawer.includes("useRef") &&
    !drawer.includes("requestAnimationFrame"),
  desktop_navigation_is_visible_and_mobile_menu_is_collapsed:
    shell.includes('className="desktop-nav"') &&
    shell.includes('className="nav-menu mobile-nav-menu"') &&
    shell.includes('className="nav-icon nav-menu__trigger"') &&
    shell.includes("aria-expanded={menuOpen}") &&
    shell.includes('id="archive-global-menu"') &&
    ["About", "Index", "Folders", "TRACE", "Search"].every((label) =>
      shell.includes(`<span>${label}</span>`),
    ) &&
    css.includes(".desktop-nav {\n    display: none;") &&
    css.includes(".nav-menu {\n    display: block;"),
  top_left_wordmark_is_removed:
    !shell.includes('className="wordmark"') &&
    !css.includes(".wordmark {"),
  mobile_is_a_separate_vertical_wheel:
    drawer.includes('className="mobile-card-wheel"') &&
    drawer.includes('aria-label="Archive coordinate card wheel"') &&
    drawer.includes('className="mobile-card-wheel__viewport"') &&
    drawer.includes('className="wheel-card"') &&
    css.includes("scroll-snap-type: y mandatory"),
  mobile_wheel_has_progressive_orbit_motion:
    css.includes("animation-timeline: view(block)") &&
    css.includes("@keyframes mobile-card-orbit") &&
    css.includes("rotateX(-52deg)") &&
    css.includes("prefers-reduced-motion: reduce"),
  mobile_is_not_hover_or_box_dependent:
    drawer.includes("tap to open") &&
    css.includes(".research-coordinate-index {\n    display: none;") &&
    css.includes(".app:has(.mobile-card-wheel) .corner-stack") &&
    css.includes('.mobile-card-wheel__intro h1 {\n    display: none;') &&
    !drawer.includes("Scroll up / down"),
  mobile_cards_form_one_visible_stack:
    css.includes(".wheel-card + .wheel-card") &&
    css.includes("margin-top: -8.5rem") &&
    css.includes("z-index: 10"),
  mobile_hint_is_at_the_bottom:
    drawer.includes('className="mobile-card-wheel__hint"') &&
    drawer.indexOf('className="mobile-card-wheel__hint"') > drawer.indexOf('className="mobile-card-wheel__viewport"'),
  region_has_continent_period_filters_and_continuous_mobile_stack:
    regionIndex.includes("Continent") &&
    regionIndex.includes("All periods") &&
    regionIndex.includes('className="region-card-stack"') &&
    css.includes(".region-card-stack__card + .region-card-stack__card") &&
    css.includes("@keyframes region-card-wheel") &&
    css.includes("content-visibility: auto") &&
    css.includes("scroll-snap-type: y mandatory"),
  unresolved_region_route_is_not_mixed_into_active_stack:
    regionIndex.includes('item.macroLabel !== "Unresolved"') &&
    regionIndex.includes("review / unknown route isolated from the active stack"),
  warm_paper_palette_with_stronger_reading_contrast:
    css.includes("--canvas: #f5f0e3") &&
    css.includes("--paper: #fbf7eb") &&
    css.includes("--ink: #242925") &&
    css.includes("--ink-soft: #505650") &&
    css.includes("border-top: 0.18rem solid var(--folder-color)"),
  tactile_controls_and_state_cursor:
    css.includes("--cursor-neutral:") &&
    css.includes("--cursor-interactive:") &&
    css.includes("--cursor-emphasis:") &&
    css.includes(".nav-icon:active") &&
    css.includes("0 0.12rem 0 var(--line)"),
  trace_colour_is_reserved_but_legible:
    traceCss.includes("fill: var(--signal-blue)") &&
    traceCss.includes("fill: var(--signal-orange)") &&
    traceCss.includes("stroke: var(--signal-orange)") &&
    traceCss.includes("cursor: var(--cursor-emphasis)"),
  home_counts_are_clickable_and_emphatic:
    home.includes('<details className="home-archive-summary">') &&
    home.includes("<summary>") &&
    !home.includes("CountsCard") &&
    css.includes(".home-archive-summary summary strong") &&
    css.includes("font-size: 2.12rem"),
  home_uses_frozen_archive_object_language:
    home.includes("traceAtlas.counts.activeObjects") &&
    home.includes("active, source-linked records") &&
    !home.includes("<small>surfaces</small>"),
};

const failed = Object.entries(checks)
  .filter(([, passed]) => !passed)
  .map(([name]) => name);

console.log(JSON.stringify({ checks, failed }, null, 2));
if (failed.length) process.exit(1);

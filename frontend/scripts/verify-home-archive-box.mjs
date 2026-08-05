import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.resolve(here, "..");
const [drawer, home, css] = await Promise.all([
  readFile(path.join(frontend, "src/components/archive/drawer/FolderDrawer.tsx"), "utf8"),
  readFile(path.join(frontend, "src/app/page.tsx"), "utf8"),
  readFile(path.join(frontend, "src/app/globals.css"), "utf8"),
]);

const checks = {
  desktop_is_compact_cabinet_menu:
    drawer.includes('className="cabinet-menu"') &&
    drawer.includes('className="cabinet-menu__rows"') &&
    drawer.includes('className="cabinet-menu__drawer-front"'),
  desktop_rows_keep_direct_routes:
    drawer.includes('className="cabinet-row"') &&
    drawer.includes("href={item.href}") &&
    drawer.includes('aria-label="Primary archive coordinates"'),
  desktop_removed_engineered_auto_scroll:
    !drawer.includes("useEffect") &&
    !drawer.includes("useRef") &&
    !drawer.includes("requestAnimationFrame"),
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
    css.includes(".cabinet-menu {\n    display: none;") &&
    css.includes(".app:has(.mobile-card-wheel) .corner-stack") &&
    css.includes('.mobile-card-wheel__intro h1 {\n    display: none;'),
  restrained_archive_palette:
    css.includes("--canvas: #f2eee3") &&
    css.includes("--paper: #f8f4e8") &&
    css.includes("border-top: 0.18rem solid var(--folder-color)"),
  home_counts_are_summary_only:
    home.includes('className="home-archive-summary"') &&
    !home.includes("CountsCard") &&
    css.includes(".home-archive-summary"),
};

const failed = Object.entries(checks)
  .filter(([, passed]) => !passed)
  .map(([name]) => name);

console.log(JSON.stringify({ checks, failed }, null, 2));
if (failed.length) process.exit(1);

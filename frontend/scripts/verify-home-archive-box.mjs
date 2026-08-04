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
  archive_box_has_physical_frame:
    drawer.includes('className="archive-box-frame"') &&
    drawer.includes('className="archive-box-front"'),
  drawers_keep_direct_routes:
    drawer.includes("href={item.href}") && drawer.includes("aria-describedby={detailId}"),
  mobile_is_not_hover_dependent:
    drawer.includes("tap to open") &&
    css.includes(".folder-card .folder-action--touch") &&
    css.includes("max-height: none"),
  mobile_uses_native_snap_and_scroll_motion:
    css.includes("scroll-snap-type: x mandatory") &&
    css.includes("animation-timeline: view(inline)") &&
    css.includes("prefers-reduced-motion: reduce"),
  restrained_archive_color_mapping:
    css.includes("--canvas: #f2eee3") &&
    css.includes("--paper: #f8f4e8") &&
    css.includes("var(--folder-color) 3.5%"),
  home_counts_have_compact_mobile_fallback:
    home.includes('className="home-archive-counts"') &&
    css.includes(".home-archive-counts") &&
    css.includes(".home-archive-strip"),
};

const failed = Object.entries(checks)
  .filter(([, passed]) => !passed)
  .map(([name]) => name);

console.log(JSON.stringify({ checks, failed }, null, 2));
if (failed.length) process.exit(1);

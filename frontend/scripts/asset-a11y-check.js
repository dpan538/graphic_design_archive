const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:3000";
const CHROME_PATH =
  process.env.CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT_DIR =
  process.env.OUT_DIR || path.join(process.cwd(), ".asset-a11y-check");
const DEFAULT_PATHS = [
  "/",
  "/contents",
  "/about",
  "/folders/region",
  "/folders/region/japan",
  "/folders/medium/poster",
  "/surfaces/SURF-GAX1970R001",
  "/surfaces/SURF-MC1930R001",
];
const CHECK_PATHS = (process.env.CHECK_PATHS || DEFAULT_PATHS.join(","))
  .split(",")
  .map((item) => item.trim())
  .filter(Boolean);

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1000, scale: 1, zoom: 1 },
  { name: "mobile", width: 390, height: 844, scale: 2, zoom: 1 },
  { name: "zoom125", width: 1440, height: 1000, scale: 1, zoom: 1.25 },
];

function timestamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "Z");
}

function slugPath(input) {
  return input.replace(/^\//, "").replace(/[^a-z0-9]+/gi, "-") || "home";
}

async function waitForAssets(page) {
  await page.evaluate(async () => {
    const imgs = Array.from(document.images);
    await Promise.all(
      imgs.map((img) => {
        if (img.complete) return Promise.resolve();
        return new Promise((resolve) => {
          img.addEventListener("load", resolve, { once: true });
          img.addEventListener("error", resolve, { once: true });
        });
      }),
    );
    if (document.fonts?.ready) await document.fonts.ready;
  });
}

async function auditPage(page) {
  return page.evaluate(() => {
    const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    const fallbackThresholds = {
      body: 0.72 * rootFontSize,
      metadata: 0.62 * rootFontSize,
      micro: 0.56 * rootFontSize,
    };
    const thresholdsFor = (el) => {
      const leaf = el.closest?.(".leaf");
      const numberAttr = (name, fallback) => {
        const value = Number.parseFloat(leaf?.getAttribute(name) || "");
        return Number.isFinite(value) ? value * rootFontSize : fallback;
      };
      return {
        body: numberAttr("data-min-body-rem", fallbackThresholds.body),
        metadata: numberAttr("data-min-metadata-rem", fallbackThresholds.metadata),
        micro: numberAttr("data-min-micro-rem", fallbackThresholds.micro),
      };
    };
    const visible = (el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return (
        rect.width > 0 &&
        rect.height > 0 &&
        style.visibility !== "hidden" &&
        style.display !== "none" &&
        Number(style.opacity) !== 0
      );
    };
    const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
    const samples = (items, limit = 40) => items.slice(0, limit);
    const isDecorative = (el) =>
      el.getAttribute("aria-hidden") === "true" || el.dataset.decorative === "true";
    const roleFor = (el) => {
      const tag = el.tagName;
      const className = String(el.className || "");
      if (/label|kicker|meta|footer|badge|code|state|accession|marker|caption|context|source|rights|row|ledger/i.test(className)) {
        return "micro";
      }
      if (["TD", "TH", "DT", "FIGCAPTION", "A", "BUTTON", "SUMMARY"].includes(tag)) {
        return "metadata";
      }
      if (["P", "LI", "BLOCKQUOTE", "DD"].includes(tag)) return "body";
      return null;
    };
    const shortSelector = (el) => {
      const cls = String(el.className || "")
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 3)
        .join(".");
      return `${el.tagName.toLowerCase()}${cls ? `.${cls}` : ""}`;
    };

    const fontViolations = [];
    for (const el of Array.from(document.querySelectorAll("body *"))) {
      if (!visible(el) || isDecorative(el)) continue;
      if (!text(el)) continue;
      const role = roleFor(el);
      if (!role) continue;
      const size = parseFloat(getComputedStyle(el).fontSize);
      const thresholds = thresholdsFor(el);
      if (Number.isFinite(size) && size + 0.01 < thresholds[role]) {
        fontViolations.push({
          selector: shortSelector(el),
          role,
          px: Number(size.toFixed(2)),
          minPx: Number(thresholds[role].toFixed(2)),
          text: text(el).slice(0, 100),
        });
      }
    }

    const documentOverflow = {
      docScrollWidth: document.documentElement.scrollWidth,
      docClientWidth: document.documentElement.clientWidth,
      bodyScrollWidth: document.body.scrollWidth,
      bodyClientWidth: document.body.clientWidth,
    };
    const horizontalOverflow =
      Math.max(documentOverflow.docScrollWidth, documentOverflow.bodyScrollWidth) >
      Math.max(documentOverflow.docClientWidth, documentOverflow.bodyClientWidth) + 2;

    const focusableCandidates = Array.from(
      document.querySelectorAll(
        'a[href], button, summary, input, select, textarea, [tabindex]:not([tabindex="-1"])',
      ),
    );
    const focusables = focusableCandidates.filter(visible);

    const imageAltViolations = Array.from(document.querySelectorAll("img"))
      .filter((img) => visible(img) && !isDecorative(img))
      .filter((img) => !img.getAttribute("alt")?.trim())
      .map((img) => ({
        selector: shortSelector(img),
        src: (img.currentSrc || img.src || "").slice(0, 160),
      }));

    const emptyFrameViolations = Array.from(
      document.querySelectorAll(
        ".image-bay--empty-frame, .main-sheet-plate__empty, [data-image-state='IMG00']",
      ),
    )
      .filter(visible)
      .filter((el) => !/(IMG00|image|withheld|empty|source|rights)/i.test(text(el)))
      .map((el) => ({
        selector: shortSelector(el),
        text: text(el).slice(0, 100),
      }));

    const rectsIntersect = (a, b) =>
      a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

    const leafTextOverflowViolations = [];
    const hiddenOverflowViolations = [];
    const cjkBreakViolations = [];
    const img04FrameViolations = [];
    const overlapViolations = [];
    const leaves = Array.from(document.querySelectorAll(".leaf")).filter(visible);
    for (const leaf of leaves) {
      const leafRect = leaf.getBoundingClientRect();
      const level = leaf.getAttribute("data-level") || "unknown";
      const overflowPolicy = leaf.getAttribute("data-overflow-policy") || "none";
      const clippedContainers = Array.from(
        leaf.querySelectorAll(
          ".reading-note__card, .main-sheet, .appendix-sheet, .sub-sheet, .text-page, .archive-card, .source-slip",
        ),
      ).filter(visible);
      for (const el of clippedContainers) {
        const style = getComputedStyle(el);
        if (
          style.overflow !== "visible" &&
          (el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2)
        ) {
          hiddenOverflowViolations.push({
            selector: shortSelector(el),
            level,
            overflowPolicy,
            scrollHeight: el.scrollHeight,
            clientHeight: el.clientHeight,
            scrollWidth: el.scrollWidth,
            clientWidth: el.clientWidth,
          });
        }
      }
      const textEls = Array.from(
        leaf.querySelectorAll("p, h1, h2, h3, h4, li, dt, dd, th, td, span, strong, em, a, figcaption"),
      ).filter((el) => visible(el) && !isDecorative(el) && text(el));

      for (const el of textEls) {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        if (
          rect.left < leafRect.left - 1 ||
          rect.right > leafRect.right + 1 ||
          rect.top < leafRect.top - 1 ||
          rect.bottom > leafRect.bottom + 1
        ) {
          leafTextOverflowViolations.push({
            selector: shortSelector(el),
            text: text(el).slice(0, 100),
          });
        }
        if (
          /[\u3040-\u30ff\u3400-\u9fff]/.test(text(el)) &&
          (style.wordBreak === "break-all" ||
            style.writingMode !== "horizontal-tb" ||
            (rect.width < 42 && text(el).length > 3))
        ) {
          cjkBreakViolations.push({
            selector: shortSelector(el),
            wordBreak: style.wordBreak,
            writingMode: style.writingMode,
            width: Number(rect.width.toFixed(1)),
            text: text(el).slice(0, 100),
          });
        }
      }

      if (
        leaf.getAttribute("data-image-state") === "IMG04" ||
        leaf.getAttribute("data-level") === "IMG04"
      ) {
        const frame = Array.from(
          leaf.querySelectorAll(".image-bay, .main-sheet-plate, .main-sheet-plate__frame, .main-sheet-plate__empty, img"),
        ).find(visible);
        if (frame) {
          img04FrameViolations.push({
            selector: shortSelector(frame),
            text: text(frame).slice(0, 100),
          });
        }
      }

      const pageTurn = document.querySelector(".page-turn");
      if (pageTurn && visible(pageTurn) && rectsIntersect(pageTurn.getBoundingClientRect(), leafRect)) {
        overlapViolations.push({
          selector: ".page-turn",
          text: "page navigation overlaps leaf",
        });
      }
    }

    const parseColor = (value) => {
      const match = value.match(/rgba?\(([^)]+)\)/);
      if (!match) return null;
      const [r, g, b, a = 1] = match[1].split(",").map((v) => Number(v.trim()));
      if ([r, g, b, a].some((v) => Number.isNaN(v))) return null;
      return { r, g, b, a };
    };
    const luminance = ({ r, g, b }) => {
      const toLinear = (v) => {
        const x = v / 255;
        return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
    };
    const contrast = (fg, bg) => {
      const a = luminance(fg);
      const b = luminance(bg);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    };
    const backgroundFor = (el) => {
      let node = el;
      while (node && node.nodeType === 1) {
        const color = parseColor(getComputedStyle(node).backgroundColor);
        if (color && color.a > 0.01) return color;
        node = node.parentElement;
      }
      return { r: 246, g: 240, b: 222, a: 1 };
    };
    const contrastViolations = [];
    for (const el of Array.from(document.querySelectorAll("p, li, a, button, td, th, dt, dd, figcaption, summary, h1, h2, h3, h4"))) {
      if (!visible(el) || isDecorative(el) || !text(el)) continue;
      const fg = parseColor(getComputedStyle(el).color);
      const bg = backgroundFor(el);
      if (!fg || !bg) continue;
      const ratio = contrast(fg, bg);
      if (ratio < 3) {
        contrastViolations.push({
          selector: shortSelector(el),
          ratio: Number(ratio.toFixed(2)),
          text: text(el).slice(0, 100),
        });
      }
    }

    const errors = [];
    if (horizontalOverflow) {
      errors.push({
        type: "horizontal-overflow",
        ...documentOverflow,
      });
    }
    for (const item of samples(fontViolations)) errors.push({ type: "font-size", ...item });
    for (const item of samples(imageAltViolations)) errors.push({ type: "image-alt", ...item });
    for (const item of samples(emptyFrameViolations)) errors.push({ type: "empty-image-frame", ...item });
    for (const item of samples(leafTextOverflowViolations)) errors.push({ type: "leaf-text-overflow", ...item });
    for (const item of samples(hiddenOverflowViolations)) errors.push({ type: "hidden-overflow", ...item });
    for (const item of samples(img04FrameViolations)) errors.push({ type: "img04-frame", ...item });
    for (const item of samples(cjkBreakViolations)) errors.push({ type: "cjk-break", ...item });
    for (const item of samples(overlapViolations)) errors.push({ type: "overlap", ...item });
    for (const item of samples(contrastViolations)) errors.push({ type: "contrast", ...item });

    const warnings = [];
    if (focusableCandidates.length > 0 && focusables.length === 0) {
      warnings.push({
        type: "focusable",
        message: "Focusable controls exist but none appear visibly focusable.",
        candidateCount: focusableCandidates.length,
      });
    }

    return {
      ok: errors.length === 0,
      rootFontSize,
      focusableCandidateCount: focusableCandidates.length,
      focusableCount: focusables.length,
      errors,
      warnings,
      counts: {
        fontViolations: fontViolations.length,
        imageAltViolations: imageAltViolations.length,
        emptyFrameViolations: emptyFrameViolations.length,
        leafTextOverflowViolations: leafTextOverflowViolations.length,
        hiddenOverflowViolations: hiddenOverflowViolations.length,
        img04FrameViolations: img04FrameViolations.length,
        cjkBreakViolations: cjkBreakViolations.length,
        overlapViolations: overlapViolations.length,
        contrastViolations: contrastViolations.length,
      },
    };
  });
}

async function main() {
  const runId = timestamp();
  const runDir = path.join(OUT_DIR, runId);
  fs.mkdirSync(runDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    userDataDir: path.join("/private/tmp", `mgd-asset-a11y-${runId}`),
    args: [
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-background-networking",
      "--disable-sync",
    ],
  });

  const results = [];
  try {
    for (const checkPath of CHECK_PATHS) {
      for (const viewport of VIEWPORTS) {
        const page = await browser.newPage();
        await page.setViewport({
          width: viewport.width,
          height: viewport.height,
          deviceScaleFactor: viewport.scale,
        });
        const url = new URL(checkPath, BASE_URL).toString();
        const entry = { path: checkPath, viewport: viewport.name, url };
        try {
          await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
          if (viewport.zoom !== 1) {
            await page.evaluate((zoom) => {
              document.documentElement.style.zoom = String(zoom);
            }, viewport.zoom);
          }
          await waitForAssets(page);
          const screenshotPath = path.join(
            runDir,
            `${viewport.name}-${slugPath(checkPath)}.png`,
          );
          await page.screenshot({ path: screenshotPath, fullPage: false });
          entry.screenshot = screenshotPath;
          entry.audit = await auditPage(page);
        } catch (error) {
          entry.audit = {
            ok: false,
            errors: [{ type: "page-error", message: error.message }],
            warnings: [],
          };
        } finally {
          await page.close();
        }
        results.push(entry);
      }
    }
  } finally {
    await browser.close();
  }

  const report = {
    runId,
    baseUrl: BASE_URL,
    outDir: runDir,
    results,
    summary: {
      checked: results.length,
      failed: results.filter((item) => !item.audit?.ok).length,
      warnings: results.reduce((sum, item) => sum + (item.audit?.warnings?.length || 0), 0),
      errors: results.reduce((sum, item) => sum + (item.audit?.errors?.length || 0), 0),
    },
  };
  const reportPath = path.join(OUT_DIR, "report.json");
  const runReportPath = path.join(runDir, "report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  fs.writeFileSync(runReportPath, JSON.stringify(report, null, 2));

  console.log(
    JSON.stringify(
      {
        reportPath,
        runReportPath,
        summary: report.summary,
      },
      null,
      2,
    ),
  );

  if (report.summary.failed > 0) process.exit(2);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

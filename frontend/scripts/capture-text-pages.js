const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const DEFAULT_URL = "http://127.0.0.1:3037/text-pages";
const DEFAULT_OUT_DIR = "/private/tmp/mgd-text-page-captures";
const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const GROUPS = [
  ["image", '[data-text-group="image"]'],
  ["text", '[data-text-group="text"]'],
  ["horizontal", '[data-text-group="horizontal"]'],
  ["experimental", '[data-text-group="experimental"]'],
];

function timestamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "Z");
}

async function waitForImages(page) {
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
  return page.evaluate((groups) => {
    const pageIssues = [];
    const groupResults = groups.map(([name, selector]) => {
      const group = document.querySelector(selector);
      if (!group) {
        return { name, selector, exists: false, count: 0, pages: [] };
      }
      const pages = Array.from(group.querySelectorAll(".text-page")).map((node, index) => {
        const rect = node.getBoundingClientRect();
        const expectedRatio = node.classList.contains("text-page--h-geology-ledger") ||
          node.classList.contains("text-page--h-free-horizon") ||
          node.classList.contains("text-page--h-factory-card") ||
          node.classList.contains("text-page--h-schedule-ledger")
          ? 1.5
          : 210 / 297;
        const actualRatio = rect.width / rect.height;
        const overflowX = node.scrollWidth - node.clientWidth;
        const overflowY = node.scrollHeight - node.clientHeight;
        const images = Array.from(node.querySelectorAll("img")).map((img) => ({
          src: img.currentSrc || img.src,
          complete: img.complete,
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
        }));
        return {
          index,
          className: node.className,
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          actualRatio: Number(actualRatio.toFixed(4)),
          expectedRatio: Number(expectedRatio.toFixed(4)),
          ratioDelta: Number(Math.abs(actualRatio - expectedRatio).toFixed(4)),
          overflowX,
          overflowY,
          imageCount: images.length,
          brokenImages: images.filter((img) => !img.complete || img.naturalWidth === 0),
        };
      });
      return { name, selector, exists: true, count: pages.length, pages };
    });

    for (const group of groupResults) {
      if (!group.exists) pageIssues.push(`Missing group ${group.name}`);
      if (group.exists && group.count === 0) pageIssues.push(`Empty group ${group.name}`);
      for (const item of group.pages) {
        if (item.overflowX > 2 || item.overflowY > 2) {
          pageIssues.push(
            `${group.name} page ${item.index + 1} overflows ${item.overflowX}x${item.overflowY}`,
          );
        }
        if (item.ratioDelta > 0.015) {
          pageIssues.push(
            `${group.name} page ${item.index + 1} ratio ${item.actualRatio}, expected ${item.expectedRatio}`,
          );
        }
        if (item.brokenImages.length > 0) {
          pageIssues.push(`${group.name} page ${item.index + 1} has broken image`);
        }
      }
    }

    return { ok: pageIssues.length === 0, issues: pageIssues, groups: groupResults };
  }, GROUPS);
}

async function main() {
  const url = process.argv[2] || DEFAULT_URL;
  const outDir = process.argv[3] || DEFAULT_OUT_DIR;
  const runId = timestamp();
  const runDir = path.join(outDir, runId);
  fs.mkdirSync(runDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    userDataDir: path.join("/private/tmp", `mgd-asset-preview-${runId}`),
    args: [
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-background-networking",
      "--disable-sync",
      "--allow-file-access-from-files",
    ],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 2600, height: 1800, deviceScaleFactor: 2 });
    await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
    await waitForImages(page);

    const audit = await auditPage(page);
    const manifest = {
      runId,
      url,
      outDir: runDir,
      audit,
      captures: {},
    };

    await page.screenshot({
      path: path.join(runDir, "text-pages-full.png"),
      fullPage: true,
    });
    manifest.captures.full = path.join(runDir, "text-pages-full.png");

    for (const [name, selector] of GROUPS) {
      const element = await page.$(selector);
      if (!element) continue;
      const filePath = path.join(runDir, `text-pages-${name}.png`);
      await element.screenshot({ path: filePath });
      manifest.captures[name] = filePath;
    }

    const manifestPath = path.join(runDir, "manifest.json");
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

    if (!audit.ok) {
      console.error(JSON.stringify({ manifestPath, issues: audit.issues }, null, 2));
      process.exit(2);
    }

    console.log(JSON.stringify({ manifestPath, captures: manifest.captures }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

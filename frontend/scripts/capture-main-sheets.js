const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const DEFAULT_URL = "http://127.0.0.1:3038/main-sheets";
const DEFAULT_OUT_DIR = "/private/tmp/mgd-main-sheet-captures";
const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const GROUP_SELECTOR = '[data-main-sheet-group="group-01"]';

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
  return page.evaluate((selector) => {
    const issues = [];
    const group = document.querySelector(selector);
    if (!group) return { ok: false, issues: ["Missing main sheet group"], pages: [] };

    const pages = Array.from(group.querySelectorAll(".main-sheet")).map((node, index) => {
      const rect = node.getBoundingClientRect();
      const expectedRatio = 210 / 297;
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
        layout: node.getAttribute("data-main-sheet"),
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

    if (pages.length !== 4) issues.push(`Expected 4 main sheets, found ${pages.length}`);
    for (const item of pages) {
      if (item.overflowX > 2 || item.overflowY > 2) {
        issues.push(`${item.layout} overflows ${item.overflowX}x${item.overflowY}`);
      }
      if (item.ratioDelta > 0.015) {
        issues.push(`${item.layout} ratio ${item.actualRatio}, expected ${item.expectedRatio}`);
      }
      if (item.brokenImages.length > 0) {
        issues.push(`${item.layout} has broken image`);
      }
    }

    return { ok: issues.length === 0, issues, pages };
  }, GROUP_SELECTOR);
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
    userDataDir: path.join("/private/tmp", `mgd-main-sheet-preview-${runId}`),
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
    await page.setViewport({ width: 2500, height: 1600, deviceScaleFactor: 2 });
    await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
    await page.waitForSelector(".main-sheet", { timeout: 30000 });
    await waitForImages(page);

    const audit = await auditPage(page);
    const manifest = {
      runId,
      url,
      outDir: runDir,
      audit,
      captures: {},
    };

    const group = await page.$(GROUP_SELECTOR);
    if (group) {
      const groupPath = path.join(runDir, "main-sheets-group-01.png");
      await group.screenshot({ path: groupPath });
      manifest.captures.group01 = groupPath;
    }

    const fullPath = path.join(runDir, "main-sheets-full.png");
    await page.screenshot({ path: fullPath, fullPage: true });
    manifest.captures.full = fullPath;

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

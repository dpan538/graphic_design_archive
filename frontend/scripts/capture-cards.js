const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const DEFAULT_URL = "http://127.0.0.1:3036/cards/dense";
const DEFAULT_OUT_DIR = "/private/tmp/mgd-card-captures";
const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const GROUP_SELECTOR = '[data-card-group="dense"]';

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
    if (!group) return { ok: false, issues: ["Missing dense card group"], cards: [] };

    const cards = Array.from(group.querySelectorAll(".archive-card")).map((node, index) => {
      const rect = node.getBoundingClientRect();
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
        overflowX,
        overflowY,
        imageCount: images.length,
        brokenImages: images.filter((img) => !img.complete || img.naturalWidth === 0),
      };
    });

    if (cards.length !== 6) issues.push(`Expected 6 rendered card articles, found ${cards.length}`);
    for (const item of cards) {
      if (item.overflowX > 2 || item.overflowY > 2) {
        issues.push(`${item.className} overflows ${item.overflowX}x${item.overflowY}`);
      }
      if (item.brokenImages.length > 0) {
        issues.push(`${item.className} has broken image`);
      }
    }

    return { ok: issues.length === 0, issues, cards };
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
    userDataDir: path.join("/private/tmp", `mgd-card-preview-${runId}`),
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
    await page.setViewport({ width: 1760, height: 1180, deviceScaleFactor: 2 });
    await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
    await page.waitForSelector(GROUP_SELECTOR, { timeout: 30000 });
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
    const groupPath = path.join(runDir, "cards-dense-group.png");
    await group.screenshot({ path: groupPath });
    manifest.captures.group = groupPath;

    const fullPath = path.join(runDir, "cards-dense-full.png");
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

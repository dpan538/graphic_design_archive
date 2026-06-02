const puppeteer = require("puppeteer-core");
const fs = require("fs");
const path = require("path");

async function main() {
  const [, , inputPath, outputPath, widthArg = "1800", heightArg = "2400"] = process.argv;

  if (!inputPath || !outputPath) {
    throw new Error("Usage: node capture-file-page.js <input-html> <output-png> [width] [height]");
  }

  const executablePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });

  const browser = await puppeteer.launch({
    executablePath,
    headless: "new",
    userDataDir: "/private/tmp/mgd-asset-preview-browser-profile",
    args: [
      "--allow-file-access-from-files",
      "--disable-web-security",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-background-networking",
      "--disable-sync",
    ],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({
      width: Number(widthArg),
      height: Number(heightArg),
      deviceScaleFactor: 2,
    });

    const url = `file://${path.resolve(inputPath)}`;
    await page.goto(url, { waitUntil: "networkidle0" });
    await page.screenshot({
      path: path.resolve(outputPath),
      fullPage: true,
    });
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

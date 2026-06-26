import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const rootDir = process.cwd();
const require = createRequire(path.join(rootDir, "frontend", "package.json"));
const { chromium, devices } = require("playwright");

const FRONTEND_URL = process.env.README_FRONTEND_URL || "http://localhost:8080";
const BACKEND_URL = process.env.README_BACKEND_URL || "http://localhost:8000";
const PROMETHEUS_URL = process.env.README_PROMETHEUS_URL || "http://localhost:9090";

const assetsDir = path.join(rootDir, "docs", "assets", "readme");
const screenshotsDir = path.join(assetsDir, "screenshots");
const videoDir = path.join(assetsDir, "video");
const thumbnailsDir = path.join(assetsDir, "thumbnails");
const tmpDir = path.join(assetsDir, ".tmp");

const desktopViewport = { width: 1440, height: 1000 };
const videoViewport = { width: 1280, height: 720 };

async function ensureDirs() {
  await fs.mkdir(screenshotsDir, { recursive: true });
  await fs.mkdir(videoDir, { recursive: true });
  await fs.mkdir(thumbnailsDir, { recursive: true });
  await fs.rm(tmpDir, { recursive: true, force: true });
  await fs.mkdir(tmpDir, { recursive: true });
}

async function ffmpeg(args) {
  await execFileAsync("ffmpeg", ["-hide_banner", "-loglevel", "error", ...args], {
    cwd: rootDir,
  });
}

async function pngToWebp(pngPath, webpPath, quality = "82") {
  await ffmpeg(["-y", "-i", pngPath, "-q:v", quality, webpPath]);
}

async function screenshotWebp(page, name, options = {}) {
  const pngPath = path.join(tmpDir, `${name}.png`);
  const webpPath = path.join(screenshotsDir, `${name}.webp`);
  await page.screenshot({
    path: pngPath,
    fullPage: options.fullPage ?? true,
    animations: "disabled",
  });
  await pngToWebp(pngPath, webpPath, options.quality || "82");
  return webpPath;
}

async function waitForApp(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForFunction(() => document.readyState !== "loading", null, {
    timeout: 30_000,
  });
  await page.waitForTimeout(1200);
}

async function goto(page, url) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  await waitForApp(page);
}

async function safeSelectFirstServer(page) {
  const firstSelect = page.locator("select").first();
  if ((await firstSelect.count()) === 0) return false;
  await firstSelect.selectOption("1").catch(async () => {
    await firstSelect.selectOption({ index: 1 });
  });
  await page.waitForTimeout(4500);
  return true;
}

async function safeSearch(page) {
  const searchInput = page
    .locator('input[placeholder*="название"], input[placeholder*="предмет"], input[aria-label*="Поиск"]')
    .first();
  if ((await searchInput.count()) === 0) return false;
  await searchInput.fill("маска");
  await page.waitForTimeout(2500);
  return true;
}

async function maybeOpenFirstLavka(page) {
  const link = page
    .locator('a:has-text("Перейти в лавку"), a:has-text("Открыть лавку")')
    .first();
  if ((await link.count()) === 0 || !(await link.isVisible().catch(() => false))) {
    return false;
  }
  await link.click();
  await waitForApp(page);
  return true;
}

async function captureStaticScreens(browser) {
  const context = await browser.newContext({
    viewport: desktopViewport,
    deviceScaleFactor: 1,
    colorScheme: "dark",
  });
  const page = await context.newPage();

  await goto(page, `${FRONTEND_URL}/`);
  await screenshotWebp(page, "00-hero-preview", { fullPage: false, quality: "84" });
  await screenshotWebp(page, "01-home", { fullPage: true });

  await safeSelectFirstServer(page);
  await screenshotWebp(page, "02-marketplace", { fullPage: true });

  await safeSearch(page);
  await screenshotWebp(page, "03-search-and-filters", { fullPage: true });

  const openedLavka = await maybeOpenFirstLavka(page);
  if (openedLavka) {
    await screenshotWebp(page, "04-lavka-detail", { fullPage: true });
  } else {
    await screenshotWebp(page, "04-marketplace-result-state", { fullPage: true });
  }

  await goto(page, `${FRONTEND_URL}/config-generator`);
  await screenshotWebp(page, "05-config-generator", { fullPage: true });

  await goto(page, `${FRONTEND_URL}/login`);
  await screenshotWebp(page, "06-auth", { fullPage: true });

  await goto(page, `${BACKEND_URL}/openapi.json`);
  await screenshotWebp(page, "07-openapi-spec", { fullPage: false });

  await goto(page, `${BACKEND_URL}/health`);
  await screenshotWebp(page, "08-health-checks", { fullPage: false });

  try {
    await goto(page, `${PROMETHEUS_URL}/targets`);
    await screenshotWebp(page, "09-monitoring", { fullPage: true });
  } catch {
    const metricsPage = await context.newPage();
    try {
      await goto(metricsPage, `${BACKEND_URL}/metrics/health`);
      await screenshotWebp(metricsPage, "09-monitoring", { fullPage: false });
    } finally {
      await metricsPage.close();
    }
  }

  await context.close();

  const mobileContext = await browser.newContext({
    ...devices["iPhone 14"],
    colorScheme: "dark",
  });
  const mobile = await mobileContext.newPage();
  await goto(mobile, `${FRONTEND_URL}/`);
  await screenshotWebp(mobile, "10-mobile", { fullPage: true, quality: "82" });

  await mobileContext.close();
}

async function captureVideo(browser) {
  const context = await browser.newContext({
    viewport: videoViewport,
    deviceScaleFactor: 1,
    colorScheme: "dark",
    recordVideo: {
      dir: tmpDir,
      size: videoViewport,
    },
  });
  const page = await context.newPage();

  await goto(page, `${FRONTEND_URL}/`);
  await page.waitForTimeout(1000);
  await safeSelectFirstServer(page);
  await page.waitForTimeout(1200);
  await safeSearch(page);
  await page.waitForTimeout(1200);
  await maybeOpenFirstLavka(page);
  await page.waitForTimeout(1400);
  await goto(page, `${FRONTEND_URL}/config-generator`);
  await page.waitForTimeout(1400);
  await goto(page, `${BACKEND_URL}/openapi.json`);
  await page.waitForTimeout(1400);

  const video = page.video();
  await context.close();
  if (!video) return null;

  const recordedPath = await video.path();
  const mp4Path = path.join(videoDir, "arizona-lavka-demo.mp4");
  const gifPath = path.join(videoDir, "arizona-lavka-demo.gif");
  const thumbnailPath = path.join(thumbnailsDir, "demo-thumbnail.webp");

  await ffmpeg([
    "-y",
    "-i",
    recordedPath,
    "-vf",
    "fps=30,scale=1280:-2:flags=lanczos",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
    "-an",
    mp4Path,
  ]);

  await ffmpeg([
    "-y",
    "-ss",
    "00:00:02",
    "-i",
    mp4Path,
    "-frames:v",
    "1",
    "-q:v",
    "82",
    thumbnailPath,
  ]);

  await ffmpeg([
    "-y",
    "-i",
    mp4Path,
    "-vf",
    "fps=8,scale=900:-1:flags=lanczos",
    "-loop",
    "0",
    gifPath,
  ]);

  const gifStat = await fs.stat(gifPath);
  if (gifStat.size > 10 * 1024 * 1024) {
    await fs.rm(gifPath, { force: true });
  }

  return mp4Path;
}

async function main() {
  await ensureDirs();

  const chromeExecutable =
    process.env.README_CHROME_EXECUTABLE ||
    ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"].find(
      (candidate) => fsSync.existsSync(candidate),
    );

  const browser = await chromium.launch({
    headless: true,
    executablePath: chromeExecutable,
    args: ["--disable-dev-shm-usage"],
  });

  try {
    await captureStaticScreens(browser);
    await captureVideo(browser);
  } finally {
    await browser.close();
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

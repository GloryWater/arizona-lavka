import { createRequire } from "node:module";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const rootDir = process.cwd();
const require = createRequire(path.join(rootDir, "frontend", "package.json"));
const { chromium } = require("playwright");

const FRONTEND_URL = process.env.README_FRONTEND_URL || "http://localhost:8080";
const DEMO_ADMIN_EMAIL = process.env.DEMO_ADMIN_EMAIL;
const DEMO_ADMIN_PASSWORD = process.env.DEMO_ADMIN_PASSWORD;

if (!DEMO_ADMIN_EMAIL || !DEMO_ADMIN_PASSWORD) {
  throw new Error("DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD are required");
}

const adminDir = path.join(rootDir, "docs", "assets", "readme", "screenshots", "admin");
const tmpDir = path.join(adminDir, ".tmp");
const viewport = { width: 1440, height: 1000 };

async function ffmpeg(args) {
  await execFileAsync("ffmpeg", ["-hide_banner", "-loglevel", "error", ...args], {
    cwd: rootDir,
  });
}

async function ensureDirs() {
  await fs.mkdir(adminDir, { recursive: true });
  await fs.rm(tmpDir, { recursive: true, force: true });
  await fs.mkdir(tmpDir, { recursive: true });
}

async function toWebp(pngPath, webpPath, quality = "84") {
  await ffmpeg(["-y", "-i", pngPath, "-q:v", quality, webpPath]);
}

async function waitForApp(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForFunction(() => document.readyState !== "loading", null, {
    timeout: 30_000,
  });
  await page.waitForTimeout(1200);
}

async function goto(page, pathname) {
  await page.goto(new URL(pathname, FRONTEND_URL).toString(), {
    waitUntil: "domcontentloaded",
    timeout: 60_000,
  });
  await waitForApp(page);
}

async function maskSensitiveText(page) {
  await page.evaluate(() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const emailPattern = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi;
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (node.nodeValue && emailPattern.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(emailPattern, "<DEMO_ADMIN_EMAIL>");
      }
    }
  });
}

async function screenshot(page, name, options = {}) {
  await maskSensitiveText(page);
  const pngPath = path.join(tmpDir, `${name}.png`);
  const webpPath = path.join(adminDir, `${name}.webp`);
  await page.screenshot({
    path: pngPath,
    fullPage: options.fullPage ?? true,
    animations: "disabled",
  });
  await toWebp(pngPath, webpPath, options.quality || "84");
}

async function login(page) {
  await goto(page, "/login");
  await screenshot(page, "01-admin-login", { fullPage: true });

  await page.getByTestId("username-input").fill(DEMO_ADMIN_EMAIL);
  await page.getByTestId("password-input").fill(DEMO_ADMIN_PASSWORD);
  await page.getByTestId("submit-button").click();
  await page.waitForURL("**/", { timeout: 30_000 }).catch(() => {});
  await waitForApp(page);
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
    const context = await browser.newContext({
      viewport,
      deviceScaleFactor: 1,
      colorScheme: "dark",
    });
    const page = await context.newPage();

    await login(page);

    await goto(page, "/admin");
    await page.getByRole("heading", { name: "Админ-панель" }).waitFor({ timeout: 30_000 });
    await screenshot(page, "02-admin-dashboard", { fullPage: true });

    await goto(page, "/admin/users");
    await page.getByRole("heading", { name: "Пользователи" }).waitFor({ timeout: 30_000 });
    await screenshot(page, "03-admin-users", { fullPage: true });

    await goto(page, "/admin/settings");
    await page.getByRole("heading", { name: "Настройки системы" }).waitFor({ timeout: 30_000 });
    await screenshot(page, "04-admin-settings", { fullPage: true });

    await context.close();
  } finally {
    await browser.close();
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

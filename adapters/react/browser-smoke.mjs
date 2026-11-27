import assert from "node:assert/strict";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { createServer } from "vite";

const root = dirname(fileURLToPath(import.meta.url));
const server = await createServer({
  configFile: false,
  root,
  logLevel: "error",
  server: { host: "127.0.0.1", port: 0, strictPort: false },
});
let browser;
try {
  await server.listen();
  const address = server.httpServer?.address();
  if (!address || typeof address === "string") {
    throw new Error("Vite did not expose a local browser-smoke address.");
  }

  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const browserErrors = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
  });

  await page.goto(`http://127.0.0.1:${address.port}/browser-smoke.html`, {
    waitUntil: "networkidle",
  });
  await page.locator("[data-cudl-root]").waitFor();

  assert.equal(await page.locator("h1").textContent(), "CUDL browser smoke");
  assert.equal(await page.locator("h1").getAttribute("data-cudl-source-line"), "2");
  assert.equal(await page.locator("#counter").textContent(), "Clicks: 0");
  await page.locator("#counter").click();
  assert.equal(await page.locator("#counter").textContent(), "Clicks: 1");
  assert.equal(
    await page.locator('[data-cudl-component="unknown-widget"]').textContent(),
    "Fallback",
  );
  assert.equal(await page.locator("a").getAttribute("href"), null);
  assert.deepEqual(browserErrors, []);

  console.log("CUDL React adapter browser smoke passed (Chromium, host state, fallback and URL safety).");
} finally {
  await browser?.close();
  await server.close();
}

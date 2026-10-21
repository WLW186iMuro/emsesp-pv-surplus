// Renders the card in headless Chromium, takes screenshots and checks interactions.
// Usage: node tests/card_check.mjs <output-dir>
import { createRequire } from "module";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const require = createRequire("/opt/npm-tools/node_modules/");
const { chromium } = require("playwright");

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] || here;
const url = pathToFileURL(path.join(here, "card_harness.html")).href;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 620, height: 1400 }, deviceScaleFactor: 2 });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(url);

const shots = [
  ["running", { open: false }, "card_running.png"],
  ["pending", { open: true }, "card_pending_settings.png"],
  ["running", { dark: true }, "card_running_dark.png"],
  ["pending", { lang: "en" }, "card_pending_en.png"],
];
for (const [name, opts, file] of shots) {
  await page.evaluate(([n, o]) => window.mount(n, o), [name, opts]);
  await page.waitForTimeout(150);
  const card = page.locator("emsesp-pv-surplus-card");
  await card.screenshot({ path: path.join(out, file) });
}

// Interactions
await page.evaluate(() => window.mount("pending", { open: true }));
await page.evaluate(() => { window.calls = []; });
const root = page.locator("emsesp-pv-surplus-card");
await root.locator('button[data-mode="manual"]').click();
await root.locator('ha-switch[data-toggle="observe"]').click();
const inp = root.locator('input[data-field="on_threshold_w"]');
await inp.fill("1700");
await inp.press("Enter");
await inp.blur();
const t = root.locator('input[data-field="window_start"]');
await t.fill("09:30");
await t.blur();
await root.locator('button[data-press="reset_lock"]').click();
const calls = await page.evaluate(() => window.calls);
console.log(JSON.stringify(calls, null, 1));

// Mobile width
await page.setViewportSize({ width: 360, height: 1400 });
await page.evaluate(() => window.mount("running", { open: true }));
await page.waitForTimeout(150);
await page.locator("emsesp-pv-surplus-card").screenshot({ path: path.join(out, "card_mobile.png") });
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
console.log("horizontal overflow on mobile:", overflow);

console.log("errors:", errors.length ? errors : "none");
await browser.close();

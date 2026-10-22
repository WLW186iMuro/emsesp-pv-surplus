// Rendert eine Bildvorlage zu PNG.
// Aufruf: node tools/bilder/render.mjs <vorlage.html> <ausgabe.png> <breite> <höhe> [skalierung]
//   Facebook (quer): node tools/bilder/render.mjs tools/bilder/facebook-quer.html bild.png 1200 630 2
//   Social Preview:  node tools/bilder/render.mjs tools/bilder/social-preview.html docs/social-preview.png 1280 640 1
// Benötigt Playwright mit Chromium (npm i -D playwright, oder NODE_PATH auf eine vorhandene Installation).
import { createRequire } from "module";
import path from "path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const [src, out, w, h, scale = "1"] = process.argv.slice(2);
if (!src || !out || !w || !h) {
  console.error("Aufruf: node render.mjs <vorlage.html> <ausgabe.png> <breite> <höhe> [skalierung]");
  process.exit(1);
}
const width = Number(w), height = Number(h);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: Number(scale) });
await page.goto("file://" + path.resolve(src));
await page.waitForTimeout(400);
const size = await page.evaluate(() => ({ w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight }));
if (size.w > width || size.h > height) console.warn(`Achtung: Inhalt ragt über den Rand (${size.w}×${size.h})`);
await page.screenshot({ path: out });
await browser.close();
console.log(`${out}: ${width * Number(scale)}×${height * Number(scale)}`);

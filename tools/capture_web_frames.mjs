// Capture consecutive frames from a web build while the character walks, for
// check_drawn_stability.py. Rendering problems (shimmer, wobble, tearing) only
// show up between frames, so a single screenshot cannot find them.
//
//   npm install playwright-core          # once, anywhere on PATH
//   node tools/capture_web_frames.mjs build/web out/frames
//   python tools/check_drawn_stability.py out/frames
//
// CHROME overrides the browser path.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const [buildDir, outDir, query = '?skip-intro'] = process.argv.slice(2);
if (!buildDir || !outDir) {
  console.error('usage: node tools/capture_web_frames.mjs <build dir> <output dir> [?query]');
  process.exit(2);
}
const FRAMES = 14;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm',
  '.pck': 'application/octet-stream', '.png': 'image/png', '.json': 'application/json', '.ogg': 'audio/ogg' };

const server = http.createServer((req, res) => {
  const file = path.join(buildDir, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    // The engine needs cross-origin isolation when built with threads.
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream',
      'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Embedder-Policy': 'require-corp' });
    res.end(data);
  });
}).listen(8799);

fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--enable-gpu', '--ignore-gpu-blocklist'],
});
// Deliberately not a whole multiple of 320x200: at an integer scale the art
// lands on exact device pixels and nothing wobbles even when it should, so a
// round window size hides exactly the problem this is looking for.
const page = await browser.newPage({ viewport: { width: 1200, height: 760 } });
const problems = [];
page.on('pageerror', e => problems.push(e.message));
await page.goto(`http://localhost:8799/index.html${query}`);
await page.waitForTimeout(6000);

// Name entry, character select, then the story pages and the menu's "Play game".
await page.keyboard.type('MIA');
await page.keyboard.press('Enter');
await page.waitForTimeout(1500);
for (let i = 0; i < 6; i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(2200); }
await page.keyboard.press('p');
await page.waitForTimeout(4000);
await page.keyboard.press('Enter');
await page.waitForTimeout(3000);

await page.keyboard.down('ArrowRight');
for (let i = 0; i < FRAMES; i++) {
  await page.screenshot({ path: path.join(outDir, `frame_${String(i).padStart(2, '0')}.png`) });
  await page.waitForTimeout(60);
}
await page.keyboard.up('ArrowRight');

console.log(`captured ${FRAMES} frames into ${outDir}`);
if (problems.length) console.error('page errors: ' + problems.join(' | '));
await browser.close();
server.close();
process.exit(problems.length ? 1 : 0);

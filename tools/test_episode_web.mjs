// Browser smoke for exported episode URL selection, menus and play.
// PLAYWRIGHT_MODULE can point to an installed playwright-core module URL.
// node tools/test_episode_web.mjs build/episode-port testing/output/episode-web
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const [buildDir = 'build/episode-port', outDir = 'testing/output/episode-web'] = process.argv.slice(2);
const build = path.resolve(buildDir);
await fs.mkdir(outDir, { recursive: true });
const types = { '.html':'text/html', '.js':'application/javascript', '.wasm':'application/wasm', '.png':'image/png', '.json':'application/json' };
const server = http.createServer(async (req, res) => {
  const filename = path.resolve(build, '.' + new URL(req.url, 'http://localhost').pathname);
  if (!filename.startsWith(build + path.sep)) { res.writeHead(403); res.end(); return; }
  try {
    const data = await fs.readFile(filename);
    res.writeHead(200, {'Content-Type':types[path.extname(filename)] || 'application/octet-stream',
      'Cross-Origin-Opener-Policy':'same-origin', 'Cross-Origin-Embedder-Policy':'require-corp'});
    res.end(data);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
const results = [];
try {
  browser = await chromium.launch({executablePath:process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args:['--enable-gpu', '--ignore-gpu-blocklist']});
  for (const episode of [1, 2, 3]) {
    const context = await browser.newContext({viewport:{width:1000, height:650}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (message.text().includes('SCRIPT ERROR:') || message.text().startsWith('ERROR:')) errors.push(message.text());
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/index.html?${episode === 1 ? "" : `episode=${episode}&`}skip-intro&mute-original-audio`);
    await page.locator('#status').waitFor({state:'hidden', timeout:45000});
    await page.waitForTimeout(1500);
    await page.locator('#canvas').click();
    await page.keyboard.type('WEBPORT');
    for (let i = 0; i < 7; i++) {
      await page.keyboard.press('Enter');
      await page.waitForTimeout(200);
    }
    await page.screenshot({path:path.join(outDir, `wr${episode}_menu.png`)});
    await page.keyboard.press('p');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
    await page.keyboard.down('ArrowUp');
    await page.keyboard.down('ArrowRight');
    await page.waitForTimeout(800);
    await page.keyboard.up('ArrowRight');
    await page.keyboard.up('ArrowUp');
    await page.screenshot({path:path.join(outDir, `wr${episode}_play.png`)});
    results.push({episode, errors});
    await context.close();
  }
  await fs.writeFile(path.join(outDir, 'report.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results));
  if (results.some(result => result.errors.length)) process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}

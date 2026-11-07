// Render chart SVGs to PNG at 2x, with the site's fonts (Lora, IBM Plex Sans) loaded.
// Usage: node render_svgs.js file1.svg [file2.svg ...]   (writes file1.png beside each)
const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2, colorScheme: 'light' });
  for (const f of process.argv.slice(2)) {
    const svg = fs.readFileSync(f, 'utf8');
    const page = await ctx.newPage();
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8">
      <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400..700&family=IBM+Plex+Sans:wght@400;500;600&display=block" rel="stylesheet">
      <style>html,body{margin:0;background:#f5f4ef}svg{display:block}</style></head><body>${svg}</body></html>`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const ok = await page.evaluate(() => document.fonts.check('600 17px Lora') && document.fonts.check('13px "IBM Plex Sans"'));
    await page.locator('svg').first().screenshot({ path: f.replace(/\.svg$/, '.png') });
    console.log(f.replace(/.*\//, ''), ok ? 'fonts ok' : 'FONTS MISSING');
    await page.close();
  }
  await browser.close();
})();

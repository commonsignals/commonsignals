// Capture third-party page screenshots for the toolkit article.
// Usage: node capture.js [ID ...]   (no IDs = all shots)
// Writes PNGs and capture-log.json to the article's screenshots/ folder.
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const OUT = path.resolve(__dirname, '../../_incoming/how-to-communicate-about-ai-safety-2026-11/screenshots');
const PAD = 24;

// Each locate() runs in the page and returns {x, y, width, height} in document coordinates,
// or null if the target can't be isolated (the script then falls back to a viewport capture).
const HELPERS = `
  window.__find = (t, root) => {
    const w = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const tag = n.parentElement.tagName;
      if (['SCRIPT', 'STYLE', 'TITLE', 'NOSCRIPT'].includes(tag)) continue;
      if (typeof t === 'string' ? n.nodeValue.includes(t) : t.test(n.nodeValue)) {
        const r = n.parentElement.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) return n.parentElement;
      }
    }
    return null;
  };
  window.__up = (el, pred, max = 12) => { for (let i = 0; el && i < max; i++, el = el.parentElement) if (pred(el)) return el; return null; };
  window.__box = (...els) => {
    const rs = els.filter(Boolean).map(e => e.getBoundingClientRect());
    const x1 = Math.min(...rs.map(r => r.left)), y1 = Math.min(...rs.map(r => r.top));
    const x2 = Math.max(...rs.map(r => r.right)), y2 = Math.max(...rs.map(r => r.bottom));
    return { x: x1 + scrollX, y: y1 + scrollY, width: x2 - x1, height: y2 - y1 };
  };
`;

const SHOTS = [
  { id: 'S01', name: 'climate-outreach-three-dos', url: 'https://climateoutreach.org/btc/2025/toolkit/toolkit-climate-change-and-nature/',
    anchor: 'Three do',
    locate: () => { const h = __find('Three do'); const c = __up(h, e => e.querySelectorAll('li').length >= 4); return c && __box(c); } },
  { id: 'S02', name: 'controlai-homepage', url: 'https://controlai.org/', viewport: true },
  { id: 'S03', name: 'controlai-take-action', url: 'https://act.controlai.org/', anchor: 'taken part',
    locate: () => { const h = __find("There's a way"); const c = __find('taken part'); const bar = c && c.nextElementSibling; return h && c && __box(h, c, bar, __find('lawmakers support')); } },
  { id: 'S05', name: 'controlai-artificial-guarantees-gpt41', url: 'https://controlai.org/artificial-guarantees', anchor: 'GPT-4.1',
    locate: () => { const h = __find('OpenAI launches GPT-4.1'); const c = __up(h, e => e.innerText.includes('What They Say')); return c && __box(c); } },
  { id: 'S06', name: 'controlai-uk-asi-bill', url: 'https://controlai.org/uk-asi-bill', anchor: 'UK Artificial Superintelligence Security Bill',
    locate: () => { const h = __find('UK Artificial Superintelligence Security Bill'); const c = __up(h, e => e.querySelectorAll('li').length >= 1 || /85\+/.test(e.innerText)); return c && c.getBoundingClientRect().height < 700 ? __box(c) : __box(h); } },
  { id: 'S07', name: 'controlai-deepfakes-campaign', url: 'https://controlai.org/past-campaigns/campaign-against-deepfakes', anchor: 'group of 64',
    locate: () => { const h = __find('Campaign against Deepfakes'); const p = __up(__find('group of 64'), e => e.tagName === 'P'); return h && p && __box(h, p); } },
  { id: 'S08', name: 'pauseai-not-just-your-job', url: 'https://pauseai.info/ai-not-just-coming-for-your-job', anchor: 'AI is not just coming for your job',
    locate: () => { const h = document.querySelector('article h1'); const p = document.querySelector('article p'); return h && p && __box(h, p); } },
  { id: 'S09', name: 'pauseai-email-builder', url: 'https://pauseai.info/email-builder', anchor: 'Email Builder',
    // No <form> element: the builder is a run of choice buttons. Heading down to the last unselected action button.
    locate: () => { const h = document.querySelector('main h1').parentElement; const btns = [...document.querySelectorAll('main button')].filter(b => /Organize a debate/.test(b.innerText)); return h && btns.length && __box(h, btns[0]); } },
  { id: 'S10', name: 'pauseai-deepmind-broken-promises', url: 'https://pauseai.info/google-deepmind-broken-promises', anchor: "Broken Promises",
    // Title through the commitments and the paragraph saying Google ignored them.
    locate: () => { const h = document.querySelector('article h1'); const p = __up(__find('Google effectively ignored'), e => e.tagName === 'P'); return h && p && __box(h, p); } },
  { id: 'S12', name: 'pauseai-homepage-72', url: 'https://pauseai.info/', anchor: 'slowed down',
    // The number is a <number-flow> web component that animates up when scrolled into view.
    ready: async (p) => {
      await p.waitForFunction(() => { const nf = __find('slowed down')?.closest('a')?.querySelector('number-flow-svelte');
        const t = nf && ((nf.getAttribute('aria-label') || '') + (nf.shadowRoot ? nf.shadowRoot.textContent : '') + nf.textContent); return t && /72/.test(t); }, null, { timeout: 10000 }).catch(() => {});
      await p.waitForTimeout(3000);
    },
    locate: () => { const a = __find('slowed down').closest('a'); return a && __box(a); } },
  { id: 'S13', name: 'fli-superintelligence-statement', url: 'https://superintelligence-statement.org/', anchor: 'We call for',
    locate: () => {
      const s = __find('We call for'); const label = __find(/^\s*Statement\s*$/);
      const card = __up(s, e => e.innerText.includes('strong public buy-in') && e.innerText.includes('Statement'));
      const counts = [...document.querySelectorAll('span,p')].filter(e => /^\s*signatures\s*$/.test(e.innerText));
      const near = counts.map(e => e.parentElement).filter(e => e.getBoundingClientRect().top > s.getBoundingClientRect().top)[0];
      const tabs = near && __up(near, e => { const r = e.getBoundingClientRect(); return r.width > 500 && r.width < 1100 && r.height < 140; });
      return __box(label || card, card, tabs || near);
    } },
  { id: 'S18', name: 'americans-on-ai-concerned-over-time', url: 'https://www.americanson.ai/', anchor: 'Concerned, over time', chart: true,
    locate: () => { const f = __find('Concerned, over time').closest('figure'); return f && __box(f); } },
  { id: 'S19', name: 'americans-on-ai-ours-to-shape', url: 'https://www.americanson.ai/', anchor: 'Ours to shape or inevitable', chart: true,
    locate: () => { const f = __find('Ours to shape or inevitable').closest('figure'); return f && __box(f); } },
  { id: 'S20', name: 'ada-lovelace-key-findings', url: 'https://www.adalovelaceinstitute.org/policy-briefing/great-expectations/', anchor: 'Key findings',
    locate: () => {
      const h = [...document.querySelectorAll('h2,h3')].find(e => e.innerText.trim() === 'Key findings');
      const out = [h];
      for (let e = h.nextElementSibling; e && !/^H[1-3]$/.test(e.tagName); e = e.nextElementSibling) out.push(e);
      return __box(...out);
    } },
];

async function dismissConsent(page) {
  // Prefer the option that rejects non-essential cookies. Never accept.
  const reject = /^(only necessary|necessary only|reject( all)?( cookies)?|decline( all)?|deny|essential only|use necessary cookies only|refuse)$/i;
  const found = await page.evaluate((src) => {
    const re = new RegExp(src, 'i');
    for (const b of document.querySelectorAll('button, a[role=button], [role=button]')) {
      const t = (b.innerText || '').trim();
      const r = b.getBoundingClientRect();
      if (re.test(t) && r.width > 0 && r.height > 0) { b.setAttribute('data-cs-reject', '1'); return t; }
    }
    return null;
  }, reject.source);
  if (found) {
    await page.locator('[data-cs-reject]').first().click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(800);
    return `clicked "${found}"`;
  }
  // Shadow-DOM banners: Playwright locators pierce shadow roots.
  for (let attempt = 0; attempt < 2; attempt++) {
    const loc = page.locator('button, a[role=button], [role=button]').filter({ hasText: reject });
    const n = await loc.count();
    for (let i = 0; i < n; i++) {
      const b = loc.nth(i);
      if (await b.isVisible()) {
        const t = (await b.innerText({ timeout: 2000 }).catch(() => '')).trim();
        await b.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(800);
        return `clicked "${t}"`;
      }
    }
    await page.waitForTimeout(2000);
  }
  // No reject option: hide fixed banners that look like cookie notices.
  const hidden = await page.evaluate(() => {
    let k = 0;
    for (const e of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(e);
      if (!['fixed', 'sticky'].includes(cs.position)) continue;
      const sig = (e.id + ' ' + e.className + ' ' + (e.getAttribute('aria-label') || '')).toLowerCase();
      if (/cookie|consent|gdpr|cmplz|(^|[\s_-])cky-|onetrust|termly/.test(sig) || /\bcookies?\b/i.test(e.innerText.slice(0, 300)) && e.getBoundingClientRect().height < 400) {
        e.style.setProperty('display', 'none', 'important'); k++;
      }
    }
    return k;
  });
  return hidden ? `hid ${hidden} banner element(s) with CSS` : 'no banner';
}

async function settle(page) {
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2000);
}

(async () => {
  const only = process.argv.slice(2);
  fs.mkdirSync(OUT, { recursive: true });
  const logPath = path.join(OUT, 'capture-log.json');
  const log = fs.existsSync(logPath) ? JSON.parse(fs.readFileSync(logPath, 'utf8')) : {};
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2, colorScheme: 'light' });
  await ctx.addInitScript(HELPERS);

  for (const s of SHOTS) {
    if (only.length && !only.includes(s.id)) continue;
    const page = await ctx.newPage();
    page.setDefaultTimeout(30000);
    const entry = { id: s.id, url: s.url, file: `${s.id}-${s.name}.png` };
    try {
      await page.goto(s.url, { waitUntil: 'networkidle', timeout: 60000 }).catch(e => { entry.warn = 'networkidle timeout'; });
      await page.waitForTimeout(2000);
      entry.consent = await dismissConsent(page);
      const file = path.join(OUT, entry.file);
      if (s.viewport) {
        await page.evaluate(() => scrollTo(0, 0));
        await settle(page);
        await page.screenshot({ path: file });
        entry.method = 'viewport';
      } else {
        // Scroll through so lazy content and scroll-triggered animations run, then bring the target into view.
        await page.evaluate(async () => { for (let y = 0; y < Math.min(document.documentElement.scrollHeight, 25000); y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); });
        const anchor = await page.evaluateHandle(t => __find(t), s.anchor);
        if (anchor.asElement()) await anchor.asElement().scrollIntoViewIfNeeded().catch(() => {});
        await settle(page);
        if (s.chart) await page.waitForFunction(t => { const f = __find(t)?.closest('figure'); return f && (f.querySelector('svg path, svg rect, canvas')); }, s.anchor, { timeout: 20000 });
        if (s.ready) await s.ready(page);
        // Fixed or sticky bars (site navs) get stamped mid-image in stitched captures; hide them.
        let box = await page.evaluate(`(${s.locate.toString()})()`).catch(e => { entry.locateError = e.message; return null; });
        if (box && box.width > 0 && box.height > 0) {
          // Hide fixed bars, and sticky ones outside the target, after locating (hidden text has no innerText).
          await page.evaluate((b) => { for (const e of document.querySelectorAll('body *')) { const p = getComputedStyle(e).position; if (p !== 'fixed' && p !== 'sticky') continue;
            const r = e.getBoundingClientRect(); const y = r.top + scrollY; const inside = p === 'sticky' && y < b.y + b.height && y + r.height > b.y;
            if (!inside) e.style.setProperty('visibility', 'hidden', 'important'); } }, box);
          const docW = await page.evaluate(() => document.documentElement.scrollWidth);
          const docH = await page.evaluate(() => document.documentElement.scrollHeight);
          const x = Math.max(0, Math.floor(box.x - PAD)), y = Math.max(0, Math.floor(box.y - PAD));
          const clip = { x, y, width: Math.min(docW, Math.ceil(box.x + box.width + PAD)) - x, height: Math.min(docH, Math.ceil(box.y + box.height + PAD)) - y };
          await page.screenshot({ path: file, clip, fullPage: true });
          entry.method = 'element'; entry.clip = clip;
        } else {
          await page.evaluate(t => { const e = __find(t); if (e) scrollTo(0, e.getBoundingClientRect().top + scrollY - 80); }, s.anchor);
          await page.waitForTimeout(1000);
          await page.screenshot({ path: file });
          entry.method = 'viewport'; entry.fallback = 'could not isolate element; viewport scrolled to the text';
        }
      }
      entry.captured_at = new Date().toISOString();
      entry.pageText = await page.evaluate(() => document.title);
      console.log(s.id, entry.method, entry.consent, entry.clip ? `${entry.clip.width}x${entry.clip.height}` : '', entry.fallback || '');
    } catch (e) {
      entry.error = e.message.split('\n')[0];
      console.log(s.id, 'ERROR', entry.error);
    }
    log[s.id] = entry;
    fs.writeFileSync(logPath, JSON.stringify(log, null, 2));
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(logPath, JSON.stringify(log, null, 2));
})();

const els = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  els.forEach((el) => io.observe(el));
} else {
  els.forEach((el) => el.classList.add('in'));
}

const navToggle = document.getElementById('navToggle');
const navDrawer = document.getElementById('navDrawer');
if (navToggle && navDrawer) {
  navDrawer.inert = true;
  navToggle.addEventListener('click', () => {
    const open = navDrawer.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    navDrawer.inert = !open;
  });
  navDrawer.querySelectorAll('a').forEach((a) => {
    a.addEventListener('click', () => {
      navDrawer.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
      navDrawer.inert = true;
    });
  });
}

const path = window.location.pathname.replace(/\/index\.html$/, '/');
document.querySelectorAll('.nav-links a, .nav-drawer a').forEach((a) => {
  const href = a.getAttribute('href');
  if (href === path || (href === '/' && path === '/')) {
    a.setAttribute('aria-current', 'page');
  }
});

// Submits to Substack via a real form POST targeting a hidden iframe, since
// a scripted fetch() is blocked by CORS and a server-side proxy is blocked
// by Substack's Cloudflare bot challenge. The response lands in a
// cross-origin iframe we can't read, so success/error here is optimistic,
// not confirmed -- Substack's own confirmation email is the real signal.
document.querySelectorAll('.subscribe-box').forEach((subscribeForm) => {
  const emailInput = subscribeForm.querySelector('input[type="email"]');
  const websiteInput = subscribeForm.querySelector('.hp-field input');
  const statusEl = subscribeForm.querySelector('.subscribe-status');
  const submitBtn = subscribeForm.querySelector('.subscribe-submit');
  if (!emailInput || !statusEl || !submitBtn) return;

  subscribeForm.addEventListener('submit', (e) => {
    statusEl.removeAttribute('data-state');

    if (websiteInput && websiteInput.value) {
      e.preventDefault();
      statusEl.textContent = "You're on the list. Thanks!";
      statusEl.setAttribute('data-state', 'ok');
      subscribeForm.reset();
      return;
    }

    statusEl.textContent = 'Submitting...';
    submitBtn.disabled = true;
    setTimeout(() => {
      statusEl.textContent = 'Thanks! Check your inbox to confirm your subscription.';
      statusEl.setAttribute('data-state', 'ok');
      submitBtn.disabled = false;
      subscribeForm.reset();
    }, 1200);
  });
});

const tocLinks = document.querySelectorAll('.article-toc a');
if (tocLinks.length && 'IntersectionObserver' in window) {
  const headings = Array.from(tocLinks)
    .map((a) => document.getElementById(a.getAttribute('href').slice(1)))
    .filter(Boolean);
  const tocIO = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      tocLinks.forEach((a) => a.classList.remove('active'));
      const match = document.querySelector(`.article-toc a[href="#${entry.target.id}"]`);
      if (match) match.classList.add('active');
    });
  }, { rootMargin: '-15% 0px -70% 0px' });
  headings.forEach((h) => tocIO.observe(h));
}

// Delegated (not querySelectorAll'd once at load) because comment.js inserts
// a .share-copy citation button into the page after this script has run.
// Copies location.href by default; a button with data-copy-text copies that
// text instead. The "copied" label is derived from the button's own default
// label ("Copy X" -> "X copied") rather than hard-coded, so this works for
// any future .share-copy button without editing this file again.
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.share-copy');
  if (!btn) return;
  const label = btn.querySelector('.share-copy-label');
  if (label && btn.dataset.defaultLabel === undefined) btn.dataset.defaultLabel = label.textContent;
  const defaultText = btn.dataset.defaultLabel || '';
  const copiedSubject = defaultText.replace(/^Copy /, '');
  const copiedLabel = copiedSubject ? copiedSubject.charAt(0).toUpperCase() + copiedSubject.slice(1) + ' copied' : 'Copied';
  clearTimeout(btn._resetTimer);
  try {
    await navigator.clipboard.writeText(btn.dataset.copyText || location.href);
    if (label) label.textContent = copiedLabel;
    btn.setAttribute('data-copied', 'true');
  } catch {
    if (label) label.textContent = 'Could not copy';
  }
  btn._resetTimer = setTimeout(() => {
    if (label) label.textContent = defaultText;
    btn.removeAttribute('data-copied');
  }, 2000);
});

// Site search, shared by the header search panel and the 404 page. Pages
// are scored against search-index.json (built by scripts/build-sitemap.py):
// a word in the title counts 3, in the URL 2, in the description 1.
window.CSSearch = (() => {
  const STOP = { html: 1, index: 1, the: 1, and: 1, of: 1, a: 1, to: 1, in: 1, on: 1, www: 1, com: 1, org: 1 };
  let indexPromise;

  const words = (s) => s.toLowerCase().split(/[^a-z0-9]+/).filter((w) => w && !STOP[w]);

  const load = () => {
    indexPromise = indexPromise || fetch('/search-index.json').then((r) => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
    return indexPromise;
  };

  const find = (pages, query) => {
    const q = words(query);
    if (!q.length) return null;
    return pages.map((p) => {
      const t = p.t.toLowerCase(), u = p.u.toLowerCase(), d = p.d.toLowerCase();
      let score = 0;
      q.forEach((w) => {
        if (t.indexOf(w) > -1) score += 3;
        if (u.indexOf(w) > -1) score += 2;
        if (d.indexOf(w) > -1) score += 1;
      });
      return { p, score };
    }).filter((h) => h.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
      .map((h) => h.p);
  };

  // Wires an input to a results list and a status line. Enter opens the top
  // result. Pass eager: true to load the index straight away rather than on
  // first focus.
  const bind = ({ input, list, status, eager }) => {
    let pages = null;
    let hits = [];
    const render = () => {
      list.textContent = '';
      if (!pages) return;
      const found = find(pages, input.value);
      hits = found || [];
      if (!found) { status.textContent = ''; return; }
      status.textContent = hits.length
        ? hits.length + (hits.length === 1 ? ' page matches.' : ' pages match.')
        : 'Nothing matches that. Try another word, or browse the sitemap.';
      hits.forEach((p) => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = p.u;
        a.textContent = p.t;
        li.appendChild(a);
        if (p.d) {
          const d = document.createElement('p');
          d.textContent = p.d;
          li.appendChild(d);
        }
        list.appendChild(li);
      });
    };
    const start = () => load()
      .then((data) => { pages = data; render(); })
      .catch(() => { status.textContent = 'Search is unavailable right now. Browse the sitemap instead.'; });
    input.addEventListener('input', render);
    input.addEventListener('focus', start, { once: true });
    input.form && input.form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (hits.length) window.location.href = hits[0].u;
    });
    if (eager) start();
  };

  return { words, bind };
})();

const searchToggle = document.getElementById('searchToggle');
const siteSearch = document.getElementById('siteSearch');
if (searchToggle && siteSearch) {
  const searchInput = siteSearch.querySelector('input[type="search"]');
  window.CSSearch.bind({
    input: searchInput,
    list: siteSearch.querySelector('.search-results'),
    status: siteSearch.querySelector('.search-status'),
  });

  const setSearch = (open) => {
    siteSearch.hidden = !open;
    searchToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      if (navDrawer && navDrawer.classList.contains('open')) {
        navDrawer.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
        navDrawer.inert = true;
      }
      searchInput.focus();
    }
  };

  searchToggle.addEventListener('click', () => setSearch(siteSearch.hidden));
  if (navToggle) navToggle.addEventListener('click', () => { if (!siteSearch.hidden) setSearch(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !siteSearch.hidden) { setSearch(false); searchToggle.focus(); }
  });
  document.addEventListener('click', (e) => {
    if (!siteSearch.hidden && !e.target.closest('header.site')) setSearch(false);
  });
}

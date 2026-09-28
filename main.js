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

// Glossary term links open in a new tab so readers keep their place. Only
// links with a #term anchor change; the plain /glossary nav link does not,
// and the glossary page's own links are left alone.
if (!/^\/glossary(\.html)?$/.test(window.location.pathname)) {
  document.querySelectorAll('a[href^="/glossary#"], a[href^="https://commonsignals.org/glossary#"]').forEach((a) => {
    a.target = '_blank';
    a.rel = 'noopener';
    if (!a.querySelector('.sr-only')) {
      const note = document.createElement('span');
      note.className = 'sr-only';
      note.textContent = ' (opens in new tab)';
      a.appendChild(note);
    }
  });
}

// Glossary hover cards: desktop only (a fine pointer that can hover), and only
// on pages that opt in with <body data-glossary-cards>. The card is a
// disclosure panel rather than role="tooltip" because it holds a link, and
// follows WCAG 2.1 SC 1.4.13: it can be hovered, dismissed with Escape, and
// never closes on a timer while hovered or focused. Touch devices get no card;
// their term links keep opening the glossary in a new tab, as above.
if (document.body.hasAttribute('data-glossary-cards') &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
  const TERM_LINK = 'a[href^="/glossary#"], a[href^="https://commonsignals.org/glossary#"]';
  const OPEN_DELAY = 300;
  const GRACE = 200;
  const GAP = 6;

  const card = document.createElement('div');
  card.id = 'glossary-card';
  card.className = 'glossary-card';
  card.setAttribute('role', 'group');
  card.setAttribute('aria-labelledby', 'glossary-card-term');
  card.hidden = true;
  card.innerHTML = '<p class="glossary-card-term" id="glossary-card-term"></p>' +
    '<p class="glossary-card-def"></p>' +
    '<a class="glossary-card-link" target="_blank" rel="noopener">Read glossary entry<span class="sr-only"> (opens in new tab)</span></a>';
  document.body.appendChild(card);
  const cardTerm = card.querySelector('.glossary-card-term');
  const cardDef = card.querySelector('.glossary-card-def');
  const cardLink = card.querySelector('.glossary-card-link');

  document.querySelectorAll(TERM_LINK).forEach((a) => {
    if (card.contains(a)) return;
    a.setAttribute('aria-controls', card.id);
    a.setAttribute('aria-expanded', 'false');
  });

  let terms = null;       // /glossary.json, fetched once per page view and keyed by id
  let trigger = null;     // the link whose card is open
  let pending = null;     // a link waiting out the open delay or the fetch
  let suppressed = null;  // closed with Escape; stays shut until the pointer or focus leaves it
  let hovering = false;
  let openTimer;
  let closeTimer;
  const opened = new Set();

  const termId = (a) => decodeURIComponent(a.getAttribute('href').split('#')[1] || '');
  // The card's own "Read glossary entry" link also points at /glossary#, so skip it.
  const termLink = (el) => {
    const a = el.closest ? el.closest(TERM_LINK) : null;
    return a && !card.contains(a) ? a : null;
  };

  // A failed fetch resolves to no terms, so no card appears and links still work.
  const loadTerms = () => {
    terms = terms || fetch('/glossary.json')
      .then((r) => {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then((rows) => Object.fromEntries(rows.map((t) => [t.id, t])))
      .catch(() => ({}));
    return terms;
  };

  // Below the link, or above it when there isn't room below, and kept inside
  // the viewport horizontally. A link that wraps is measured by the line the
  // card sits next to.
  const place = (a) => {
    const rects = a.getClientRects();
    const first = rects[0];
    const last = rects[rects.length - 1];
    card.style.left = '0px';
    card.style.top = '0px';
    const { width, height } = card.getBoundingClientRect();
    const below = last.bottom + GAP + height <= window.innerHeight || first.top - GAP - height < 0;
    const line = below ? last : first;
    const vw = document.documentElement.clientWidth;
    const left = Math.min(Math.max(line.left, 8), vw - width - 8);
    const top = below ? line.bottom + GAP : line.top - GAP - height;
    card.dataset.placement = below ? 'below' : 'above';
    card.style.left = `${Math.round(left + window.scrollX)}px`;
    card.style.top = `${Math.round(top + window.scrollY)}px`;
  };

  const close = () => {
    clearTimeout(openTimer);
    clearTimeout(closeTimer);
    pending = null;
    if (!trigger) return;
    trigger.setAttribute('aria-expanded', 'false');
    trigger = null;
    card.hidden = true;
  };

  const open = (a) => {
    loadTerms().then((byId) => {
      if (pending !== a) return;
      pending = null;
      const id = termId(a);
      const t = byId[id];
      if (!t) return;
      if (trigger && trigger !== a) trigger.setAttribute('aria-expanded', 'false');
      trigger = a;
      cardTerm.textContent = t.term;
      cardDef.textContent = t.definition;
      cardLink.href = `/glossary#${id}`;
      card.style.visibility = 'hidden';
      card.hidden = false;
      place(a);
      card.style.visibility = '';
      a.setAttribute('aria-expanded', 'true');
      if (window.posthog && !opened.has(id)) {
        opened.add(id);
        window.posthog.capture('glossary_card_opened', { term: id, page: location.pathname });
      }
    });
  };

  const request = (a, delay) => {
    clearTimeout(closeTimer);
    if (a === trigger || a === pending) return;
    clearTimeout(openTimer);
    pending = a;
    loadTerms();
    openTimer = setTimeout(() => open(a), delay);
  };

  // Keyboard focus on the link or in the card keeps it open; a mouse click
  // also focuses the link, so only :focus-visible counts.
  const focusHolds = () => card.contains(document.activeElement) ||
    (trigger && document.activeElement === trigger && trigger.matches(':focus-visible'));

  const closeSoon = () => {
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {
      if (!hovering && !focusHolds()) close();
    }, GRACE);
  };

  document.addEventListener('pointerover', (e) => {
    if (e.pointerType === 'touch') return;
    const a = termLink(e.target);
    if (a) {
      hovering = true;
      if (a !== suppressed) request(a, OPEN_DELAY);
    } else if (card.contains(e.target)) {
      hovering = true;
      clearTimeout(closeTimer);
    }
  });

  document.addEventListener('pointerout', (e) => {
    if (e.pointerType === 'touch') return;
    const from = termLink(e.target) || (card.contains(e.target) ? card : null);
    if (!from) return;
    const to = e.relatedTarget;
    if (to && (from.contains(to) || card.contains(to) || (trigger && trigger.contains(to)))) return;
    hovering = false;
    if (from === suppressed) suppressed = null;
    if (pending) {
      clearTimeout(openTimer);
      pending = null;
    }
    if (trigger) closeSoon();
  });

  document.addEventListener('focusin', (e) => {
    const a = termLink(e.target);
    if (suppressed && a !== suppressed) suppressed = null;
    if (a && a !== suppressed && a.matches(':focus-visible')) {
      request(a, 0);
    } else if (!a && !card.contains(e.target)) {
      // Focus moved on before the data arrived: drop the waiting card too.
      if (pending && !hovering) {
        clearTimeout(openTimer);
        pending = null;
      }
      if (trigger && !hovering) close();
    }
  });

  // The next thing to Tab to after the link, skipping the card itself.
  const nextFocusable = (from) => {
    const all = Array.from(document.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]'))
      .filter((el) => !card.contains(el) && el.tabIndex >= 0 && el.getClientRects().length);
    return all[all.indexOf(from) + 1];
  };

  document.addEventListener('keydown', (e) => {
    if (!trigger) return;
    const a = trigger;
    if (e.key === 'Escape') {
      suppressed = a;
      const focusInCard = card.contains(document.activeElement);
      close();
      if (focusInCard) a.focus();
      return;
    }
    if (e.key !== 'Tab') return;
    // The card sits at the end of <body>, so Tab is walked into and out of it
    // by hand to keep it next to its link in the reading order.
    if (!e.shiftKey && document.activeElement === a) {
      e.preventDefault();
      cardLink.focus();
    } else if (e.shiftKey && document.activeElement === cardLink) {
      e.preventDefault();
      a.focus();
    } else if (!e.shiftKey && document.activeElement === cardLink) {
      const next = nextFocusable(a);
      close();
      if (next) {
        e.preventDefault();
        next.focus();
      }
    }
  });

  window.addEventListener('resize', close);
}

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

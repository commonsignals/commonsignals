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

document.querySelectorAll('.subscribe-box').forEach((subscribeForm) => {
  const emailInput = subscribeForm.querySelector('input[type="email"]');
  const websiteInput = subscribeForm.querySelector('.hp-field input');
  const statusEl = subscribeForm.querySelector('.subscribe-status');
  const submitBtn = subscribeForm.querySelector('.subscribe-submit');
  if (!emailInput || !statusEl || !submitBtn) return;

  subscribeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    statusEl.textContent = '';
    statusEl.removeAttribute('data-state');

    // Honeypot: bots fill every field. Pretend success without submitting.
    if (websiteInput && websiteInput.value) {
      statusEl.textContent = "You're on the list. Thanks!";
      statusEl.setAttribute('data-state', 'ok');
      subscribeForm.reset();
      return;
    }

    submitBtn.disabled = true;

    try {
      const res = await fetch('/subscribe', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email: emailInput.value.trim(), website: websiteInput ? websiteInput.value : '' }),
      });
      let data = {};
      try { data = await res.json(); } catch {}
      if (res.ok) {
        statusEl.textContent = "You're on the list. Thanks!";
        statusEl.setAttribute('data-state', 'ok');
        subscribeForm.reset();
      } else {
        statusEl.textContent = data.error || data.message || 'Something went wrong. Please try again.';
        statusEl.setAttribute('data-state', 'error');
      }
    } catch {
      statusEl.textContent = 'Something went wrong. Please try again.';
      statusEl.setAttribute('data-state', 'error');
    } finally {
      submitBtn.disabled = false;
    }
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

document.querySelectorAll('.share-copy').forEach((btn) => {
  const label = btn.querySelector('.share-copy-label');
  const defaultText = label ? label.textContent : '';
  let resetTimer;
  btn.addEventListener('click', async () => {
    clearTimeout(resetTimer);
    try {
      await navigator.clipboard.writeText(location.href);
      if (label) label.textContent = 'Link copied';
      btn.setAttribute('data-copied', 'true');
    } catch {
      if (label) label.textContent = 'Could not copy link';
    }
    resetTimer = setTimeout(() => {
      if (label) label.textContent = defaultText;
      btn.removeAttribute('data-copied');
    }, 2000);
  });
});

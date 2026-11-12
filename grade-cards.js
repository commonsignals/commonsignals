// Evidence-grade hover cards. Every .grade label (Established, Tested, Observed) gets a card
// with the grade's definition, worded exactly as in the toolkit's "How we grade AI safety
// evidence" section: change both together. The card reuses the glossary card's look
// (.glossary-card in styles.css). It opens on hover and keyboard focus, and on tap for touch
// screens; Escape, a tap elsewhere or moving away closes it.
(function () {
  const GRADES = {
    established: {
      term: 'Established',
      def: 'Findings replicated across multiple studies and fields, such as public health and climate communications.',
    },
    tested: {
      term: 'Tested',
      def: 'Findings from a single controlled experiment, dial test, or representative survey focused directly on AI.',
    },
    observed: {
      term: 'Observed',
      def: 'Real-world patterns noticed in focus groups, comment-thread studies, and campaign reports.',
    },
  };
  const KEY_URL = '/how-to-communicate-about-ai-safety#how-we-grade-ai-safety-evidence';

  function init() {
    const labels = Array.from(document.querySelectorAll('.grade')).filter((el) => gradeOf(el));
    if (!labels.length) return;

    const style = document.createElement('style');
    style.textContent =
      '.grade[data-grade-card] { cursor: help; }' +
      '.grade[data-grade-card] .grade-word { text-decoration: underline dotted var(--teal-text); text-decoration-thickness: 2px; text-underline-offset: 0.22em; }' +
      '.grade[data-grade-card]:hover .grade-word, .grade[data-grade-card]:focus-visible .grade-word { text-decoration-color: var(--teal); }' +
      '.grade[data-grade-card]:focus { outline: none; }' +
      '.grade[data-grade-card]:focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; border-radius: 3px; }';
    document.head.appendChild(style);

    const card = document.createElement('div');
    card.className = 'glossary-card grade-card';
    card.id = 'grade-card';
    card.setAttribute('role', 'tooltip');
    card.hidden = true;
    card.innerHTML = '<p class="glossary-card-term"></p><p class="glossary-card-def"></p>' +
      '<a class="glossary-card-link">How we grade evidence</a>';
    card.querySelector('.glossary-card-link').href = KEY_URL;
    document.body.appendChild(card);
    const cardTerm = card.querySelector('.glossary-card-term');
    const cardDef = card.querySelector('.glossary-card-def');

    const canHover = window.matchMedia('(hover: hover) and (pointer: fine)');
    let current = null;
    let hideTimer = null;

    labels.forEach((el) => {
      el.setAttribute('data-grade-card', '');
      el.setAttribute('tabindex', '0');
      // Underline only the grade's word, not the dot or a bracket inside the label.
      Array.from(el.childNodes).forEach((n) => {
        if (n.nodeType === 3 && /[A-Za-z]/.test(n.nodeValue)) {
          const m = n.nodeValue.match(/^(\W*)([A-Za-z]+)(.*)$/s);
          if (!m) return;
          const word = document.createElement('span');
          word.className = 'grade-word';
          word.textContent = m[2];
          const frag = document.createDocumentFragment();
          if (m[1]) frag.appendChild(document.createTextNode(m[1]));
          frag.appendChild(word);
          if (m[3]) frag.appendChild(document.createTextNode(m[3]));
          el.replaceChild(frag, n);
        }
      });
      el.addEventListener('mouseenter', () => show(el));
      el.addEventListener('mouseleave', scheduleHide);
      el.addEventListener('focus', () => show(el));
      el.addEventListener('blur', (e) => { if (!card.contains(e.relatedTarget)) hide(); });
      el.addEventListener('click', () => {
        // Touch screens have no hover: a tap opens the card, a second tap closes it.
        // With a mouse, hover already opened it, so a click keeps it open.
        if (canHover.matches) { show(el); return; }
        if (current === el && !card.hidden) hide(); else show(el);
      });
    });

    card.addEventListener('mouseenter', () => clearTimeout(hideTimer));
    card.addEventListener('mouseleave', scheduleHide);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !card.hidden) {
        const back = current;
        hide();
        if (back) back.focus();
      }
    });
    document.addEventListener('click', (e) => {
      if (!card.hidden && !card.contains(e.target) && !(current && current.contains(e.target))) hide();
    });
    window.addEventListener('resize', () => { if (!card.hidden && current) place(current); });

    function show(el) {
      clearTimeout(hideTimer);
      const g = GRADES[gradeOf(el)];
      if (current && current !== el) current.removeAttribute('aria-describedby');
      current = el;
      cardTerm.textContent = g.term;
      cardDef.textContent = g.def;
      card.hidden = false;
      el.setAttribute('aria-describedby', 'grade-card');
      place(el);
    }
    function hide() {
      clearTimeout(hideTimer);
      card.hidden = true;
      if (current) current.removeAttribute('aria-describedby');
      current = null;
    }
    function scheduleHide() {
      clearTimeout(hideTimer);
      hideTimer = setTimeout(hide, 180);
    }
    function place(el) {
      const r = el.getBoundingClientRect();
      const { width, height } = card.getBoundingClientRect();
      const gap = 8, margin = 8;
      const below = window.innerHeight - r.bottom >= height + gap + margin || r.top < height + gap + margin;
      card.dataset.placement = below ? 'below' : 'above';
      const top = below ? r.bottom + gap : r.top - gap - height;
      let left = r.left;
      left = Math.min(left, document.documentElement.clientWidth - width - margin);
      left = Math.max(left, margin);
      card.style.top = (top + window.scrollY) + 'px';
      card.style.left = (left + window.scrollX) + 'px';
    }
  }

  function gradeOf(el) {
    for (const k of Object.keys(GRADES)) if (el.classList.contains('grade-' + k)) return k;
    return null;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

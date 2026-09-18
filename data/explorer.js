/* Shared explorer logic for /data/studies/<slug>/index.html. Fetches that
 * study's study.json + codebook.json + comments.csv, builds facets from the
 * codebook, and renders a filterable list of comments. No dependencies:
 * includes its own small CSV parser, same reasoning as scripts/data-export.py
 * having none.
 */
(function () {
  'use strict';

  const STUB_CODER = 'not_coded_empty_stub';
  const PAGE_SIZE = 50;

  // The three dimensions shared across every study in the series exist with
  // the same value set everywhere, but studies disagree on label casing and
  // order (see data/studies/README.md). Canonicalise display here rather
  // than trust each study's own label string verbatim.
  const CANONICAL_LABELS = {
    stance: { agree: 'Agree', disagree: 'Disagree', mixed: 'Mixed', unclear: 'Unclear', na: 'No position' },
    format_reaction: { none: 'None', praise: 'Praise', mock: 'Mock', condescended: 'Condescended', imitates: 'Imitates' },
    emotion: { neutral: 'Neutral', fear: 'Fear', anger: 'Anger', resignation: 'Resignation', humour: 'Humour', hope: 'Hope' },
  };
  const CANONICAL_ORDER = {
    stance: ['agree', 'mixed', 'disagree', 'unclear', 'na'],
    format_reaction: ['none', 'praise', 'mock', 'condescended', 'imitates'],
    emotion: ['neutral', 'fear', 'anger', 'resignation', 'humour', 'hope'],
  };
  // Preferred facet display order; anything not listed (a study's own group
  // columns, extra flags) is appended after, in codebook order.
  const FACET_ORDER = ['stance', 'frame', 'format_reaction', 'emotion'];

  function slugFromPath() {
    const parts = location.pathname.split('/').filter(Boolean);
    let last = parts[parts.length - 1];
    if (last && last.endsWith('.html')) last = parts[parts.length - 2];
    return last;
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function hi(s, q) {
    if (!q) return esc(s);
    const i = s.toLowerCase().indexOf(q);
    if (i < 0) return esc(s);
    return esc(s.slice(0, i)) + '<mark>' + esc(s.slice(i, i + q.length)) + '</mark>' + esc(s.slice(i + q.length));
  }

  // Minimal RFC4180 CSV parser: quoted fields, doubled-quote escaping,
  // commas and newlines inside quotes. comments.csv needs all three.
  function parseCSV(text) {
    const rows = [];
    let row = [];
    let field = '';
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else { inQuotes = false; }
        } else {
          field += c;
        }
      } else if (c === '"') {
        inQuotes = true;
      } else if (c === ',') {
        row.push(field); field = '';
      } else if (c === '\r') {
        // skip, \n (or \r\n) ends the row
      } else if (c === '\n') {
        row.push(field); rows.push(row); row = []; field = '';
      } else {
        field += c;
      }
    }
    if (field !== '' || row.length) { row.push(field); rows.push(row); }
    const header = rows.shift() || [];
    return rows
      .filter((r) => !(r.length === 1 && r[0] === ''))
      .map((r) => {
        const obj = {};
        header.forEach((h, idx) => { obj[h] = r[idx] !== undefined ? r[idx] : ''; });
        return obj;
      });
  }

  function setStickyOffsets() {
    const header = document.querySelector('header.site');
    const finder = document.querySelector('.exp-finder');
    if (header) document.documentElement.style.setProperty('--exp-header-h', header.offsetHeight + 'px');
    if (finder) document.documentElement.style.setProperty('--exp-finder-h', finder.offsetHeight + 'px');
  }

  async function init() {
    const slug = slugFromPath();
    const base = `/data/studies/${slug}/`;
    const heroEl = document.getElementById('expHero');
    const listEl = document.getElementById('expList');
    let study, codebook, rows;
    try {
      [study, codebook, rows] = await Promise.all([
        fetch(base + 'study.json').then((r) => { if (!r.ok) throw new Error('study.json ' + r.status); return r.json(); }),
        fetch(base + 'codebook.json').then((r) => { if (!r.ok) throw new Error('codebook.json ' + r.status); return r.json(); }),
        fetch(base + 'comments.csv').then((r) => { if (!r.ok) throw new Error('comments.csv ' + r.status); return r.text(); }).then(parseCSV),
      ]);
    } catch (err) {
      listEl.innerHTML = `<p class="exp-empty">Could not load this study's data (${esc(err.message)}). Try the raw files directly: <a href="${base}study.json">study.json</a>, <a href="${base}comments.csv">comments.csv</a>.</p>`;
      return;
    }

    renderHero(study, codebook);

    const dims = codebook.dimensions || [];
    const facetDims = dims.filter((d) => d.kind === 'single' || d.kind === 'flag' || d.kind === 'group');
    facetDims.sort((a, b) => {
      const ia = FACET_ORDER.indexOf(a.key);
      const ib = FACET_ORDER.indexOf(b.key);
      if (ia === -1 && ib === -1) return 0;
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });

    const stubRows = rows.filter((r) => r.coder === STUB_CODER);
    const comments = rows.filter((r) => r.coder !== STUB_CODER);

    buildFacets(facetDims, comments);

    const q = document.getElementById('expSearch');
    const clear = document.getElementById('expClear');
    const count = document.getElementById('expCount');
    let visibleCount = PAGE_SIZE;

    function currentQuery() { return q.value.trim().toLowerCase(); }

    function selectedValues(key) {
      return Array.from(document.querySelectorAll(`.exp-facet-options input[data-key="${key}"]:checked`)).map((el) => el.value);
    }

    function matches(row, query) {
      if (query) {
        const hay = row.text.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      for (const dim of facetDims) {
        const selected = selectedValues(dim.key);
        if (!selected.length) continue;
        if (dim.kind === 'flag') {
          if (!selected.includes(row[dim.key])) return false;
        } else {
          if (!selected.includes(row[dim.key])) return false;
        }
      }
      return true;
    }

    function renderResults() {
      const query = currentQuery();
      clear.hidden = !query;
      const shown = comments.filter((r) => matches(r, query));

      count.textContent = shown.length + ' of ' + comments.length + ' comments';

      if (!shown.length) {
        const subject = encodeURIComponent('Data explorer: ' + (study.slug || ''));
        listEl.innerHTML = `<p class="exp-empty">Nothing matches <strong>${esc(q.value)}</strong> and the current filters. <a href="mailto:hello@commonsignals.org?subject=${subject}">Tell us if that looks wrong</a>.</p>`;
        return;
      }

      const toRender = shown.slice(0, visibleCount);
      const stubNote = stubRows.length
        ? `<p class="exp-stub-note">+${stubRows.length} uncoded stub replies (no text captured, e.g. GIF or sticker-only) not shown.</p>`
        : '';

      listEl.innerHTML = stubNote + toRender.map((r) => renderComment(r, query, codebook)).join('') +
        (shown.length > toRender.length
          ? `<p class="exp-loadmore"><button type="button" class="btn btn-ghost" id="expLoadMore">Show ${Math.min(PAGE_SIZE, shown.length - toRender.length)} more (${shown.length - toRender.length} left)</button></p>`
          : '');

      const loadMore = document.getElementById('expLoadMore');
      if (loadMore) loadMore.addEventListener('click', () => { visibleCount += PAGE_SIZE; renderResults(); });

      setStickyOffsets();
    }

    q.addEventListener('input', () => { visibleCount = PAGE_SIZE; renderResults(); });
    clear.addEventListener('click', () => { q.value = ''; visibleCount = PAGE_SIZE; renderResults(); q.focus(); });
    document.querySelectorAll('.exp-facet-options input').forEach((el) => {
      el.addEventListener('change', () => { visibleCount = PAGE_SIZE; renderResults(); });
    });

    renderResults();
    setStickyOffsets();
    window.addEventListener('resize', setStickyOffsets);
    if ('ResizeObserver' in window) {
      const header = document.querySelector('header.site');
      if (header) new ResizeObserver(setStickyOffsets).observe(header);
    }

    if (location.hash) {
      const target = document.getElementById(location.hash.slice(1));
      if (target) target.scrollIntoView();
    }
  }

  function renderHero(study, codebook) {
    const heroEl = document.getElementById('expHero');
    const h1 = heroEl.querySelector('h1');
    if (h1) h1.textContent = study.title;
    const meta = document.getElementById('expMeta');
    if (meta) {
      meta.innerHTML = `<strong>${study.counts.coded}</strong> comments coded &middot; <strong>${study.counts.clear_position_base}</strong> take a clear position &middot; ${esc(study.platform)} &middot; spot-check ${study.spot_check && study.spot_check.sample != null ? `${study.spot_check.agreed}/${study.spot_check.sample} agreed` : 'not recorded'}`;
    }
    document.title = study.title + ': Common Signals data explorer';
  }

  // Some studies' codebooks write flag labels as raw shorthand (METR/Cotra:
  // "m_messenger_credentials"), others write them out properly (Soares:
  // "Mentions messenger credentials"). Humanise anything that still looks
  // like an identifier rather than replace every study's hand-written copy.
  function dimLabel(dim) {
    const label = dim.label || dim.key;
    if (!/_/.test(label)) return label;
    return dim.key
      .replace(/^mentions_/, '')
      .replace(/_/g, ' ')
      .replace(/^./, (c) => c.toUpperCase());
  }

  function labelFor(dim, value) {
    if (CANONICAL_LABELS[dim.key] && CANONICAL_LABELS[dim.key][value]) return CANONICAL_LABELS[dim.key][value];
    const v = (dim.values || []).find((v) => v.value === value);
    return v ? v.label : value;
  }

  function valuesFor(dim, comments) {
    if (dim.kind === 'flag') {
      return [{ value: 'true', label: dimLabel(dim) }];
    }
    let vals = (dim.values || []).map((v) => v.value);
    if (CANONICAL_ORDER[dim.key]) {
      vals = CANONICAL_ORDER[dim.key].filter((v) => vals.includes(v));
    }
    return vals.map((value) => ({ value, label: labelFor(dim, value) }));
  }

  function countFor(key, value, comments) {
    let n = 0;
    for (const r of comments) if (r[key] === value) n++;
    return n;
  }

  function buildFacets(facetDims, comments) {
    const container = document.getElementById('expFacets');
    if (!container) return;
    container.innerHTML = facetDims.map((dim) => {
      const options = valuesFor(dim, comments);
      const optionsHtml = options.map((opt) => {
        const n = countFor(dim.key, opt.value, comments);
        if (!n) return '';
        return `<label><input type="checkbox" data-key="${esc(dim.key)}" value="${esc(opt.value)}"> ${esc(opt.label)} <span class="n">(${n})</span></label>`;
      }).join('');
      if (!optionsHtml) return '';
      return `<details class="exp-facet"><summary>${esc(dimLabel(dim))} <span class="n">${options.length}</span></summary><div class="exp-facet-options">${optionsHtml}</div></details>`;
    }).join('');
  }

  function renderComment(r, query, codebook) {
    const dimsByKey = Object.fromEntries((codebook.dimensions || []).map((d) => [d.key, d]));
    const tags = [];
    if (r.stance) {
      const label = labelFor(dimsByKey.stance || { key: 'stance' }, r.stance);
      tags.push(`<span class="exp-tag stance-${esc(r.stance)}">${esc(label)}</span>`);
    }
    if (r.frame && dimsByKey.frame) {
      const v = (dimsByKey.frame.values || []).find((v) => v.value === r.frame);
      tags.push(`<span class="exp-tag">${esc(v ? v.label : r.frame)}</span>`);
    }
    if (r.format_reaction && r.format_reaction !== 'none' && dimsByKey.format_reaction) {
      tags.push(`<span class="exp-tag">${esc(labelFor(dimsByKey.format_reaction, r.format_reaction))}</span>`);
    }
    if (r.emotion && dimsByKey.emotion) {
      tags.push(`<span class="exp-tag">${esc(labelFor(dimsByKey.emotion, r.emotion))}</span>`);
    }
    for (const dim of codebook.dimensions || []) {
      if (dim.kind === 'flag' && r[dim.key] === 'true') {
        tags.push(`<span class="exp-tag">${esc(dimLabel(dim))}</span>`);
      }
      if (dim.kind === 'group' && r[dim.key]) {
        const v = (dim.values || []).find((v) => v.value === r[dim.key]);
        tags.push(`<span class="exp-tag meta">${esc(v ? v.label : r[dim.key])}</span>`);
      }
    }
    if (r.likes) tags.push(`<span class="exp-tag meta">${esc(r.likes)} likes</span>`);
    if (r.published_at) tags.push(`<span class="exp-tag meta">${esc(r.published_at.slice(0, 10))}</span>`);

    return `<article class="exp-comment" id="${esc(r.id)}">
      <p class="text">${hi(r.text, query)}</p>
      <div class="exp-tags">${tags.join('')}</div>
    </article>`;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

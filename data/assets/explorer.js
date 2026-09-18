/* Study explorer (/data/<slug>/): search, facets, sort, Comments/Quotes
 * toggle and CSV export, all reading from and writing to the URL query
 * string. Generic over any study's codebook.json; proven out on
 * cotra-episode-2026-09 only for now. Depends on core.js.
 */
(function (CS) {
  'use strict';

  const FACET_ORDER = ['stance', 'frame', 'format_reaction', 'emotion'];
  const LIKES_BANDS = [
    { value: '0', label: '0', test: (n) => n === 0 },
    { value: '1-4', label: '1 to 4', test: (n) => n >= 1 && n <= 4 },
    { value: '5-19', label: '5 to 19', test: (n) => n >= 5 && n <= 19 },
    { value: '20-99', label: '20 to 99', test: (n) => n >= 20 && n <= 99 },
    { value: '100+', label: '100 or more', test: (n) => n >= 100 },
  ];

  function likesBandValue(n) {
    if (n === null || n === undefined) return null;
    const band = LIKES_BANDS.find((b) => b.test(n));
    return band ? band.value : null;
  }

  const THREAD_POSITION_DIM = {
    key: '__thread_position',
    label: 'Top level or reply',
    kind: 'synthetic',
    values: [
      { value: 'top_level', label: 'Top level' },
      { value: 'reply', label: 'Reply' },
    ],
    valueOf: (r) => (r.parent_id ? 'reply' : 'top_level'),
  };

  function likesBandDim() {
    return {
      key: '__likes_band',
      label: 'Likes',
      kind: 'synthetic',
      values: LIKES_BANDS.map((b) => ({ value: b.value, label: b.label })),
      valueOf: (r) => likesBandValue(r.likes),
    };
  }

  function codebookDimsAsFacets(codebook) {
    const dims = (codebook.dimensions || []).filter((d) => d.kind === 'single' || d.kind === 'flag');
    dims.sort((a, b) => {
      const ia = FACET_ORDER.indexOf(a.key);
      const ib = FACET_ORDER.indexOf(b.key);
      if (ia === -1 && ib === -1) return 0;
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
    // Flag columns are real JSON booleans in data.json, but facet values are
    // always strings (URL query params, and facetValueOptions' "true" for a
    // flag); compare as strings here so a boolean never fails a strict-
    // equality Array.includes/Map.has check against its string form.
    return dims.map((d) => Object.assign({}, d, {
      valueOf: d.kind === 'flag' ? (r) => String(r[d.key]) : (r) => r[d.key],
    }));
  }

  function buildAllDims(codebook, comments) {
    const dims = codebookDimsAsFacets(codebook);
    dims.push(THREAD_POSITION_DIM);
    const hasLikes = comments.some((c) => c.likes !== null && c.likes !== undefined);
    if (hasLikes) dims.push(likesBandDim());
    return dims;
  }

  function facetValueOptions(dim) {
    if (dim.kind === 'flag') return [{ value: 'true', label: CS.dimLabel(dim) }];
    return (dim.values || []).map((v) => ({ value: v.value, label: v.label }));
  }

  function stateFromURL(allDims) {
    const params = new URLSearchParams(location.search);
    const state = {
      q: (params.get('q') || '').trim().toLowerCase(),
      selected: {},
      sort: params.get('sort') || 'thread',
      view: params.get('view') === 'quotes' ? 'quotes' : 'comments',
    };
    for (const dim of allDims) {
      const raw = params.get(dim.key);
      if (raw) state.selected[dim.key] = raw.split(',').filter(Boolean);
    }
    return state;
  }

  function syncURL(state, allDims) {
    const params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    for (const dim of allDims) {
      const sel = state.selected[dim.key];
      if (sel && sel.length) params.set(dim.key, sel.join(','));
    }
    if (state.sort !== 'thread') params.set('sort', state.sort);
    if (state.view !== 'comments') params.set('view', state.view);
    const qs = params.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
  }

  function activeFacetKeys(state, allDims) {
    return allDims.filter((d) => (state.selected[d.key] || []).length).map((d) => d.key);
  }

  function rowMatchesDim(row, dim, selected) {
    if (!selected || !selected.length) return true;
    return selected.includes(dim.valueOf(row));
  }

  function matches(row, state, allDims, excludeKey) {
    if (state.q && !row.text.toLowerCase().includes(state.q)) return false;
    for (const dim of allDims) {
      if (dim.key === excludeKey) continue;
      if (!rowMatchesDim(row, dim, state.selected[dim.key])) return false;
    }
    return true;
  }

  function sortRows(rows, sort) {
    if (sort === 'likes') {
      return rows.slice().sort((a, b) => (b.likes ?? -1) - (a.likes ?? -1));
    }
    if (sort === 'date') {
      return rows.slice().sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
    }
    return rows;
  }

  function describeFilter(state, allDims) {
    const parts = [];
    if (state.q) parts.push(`text contains "${state.q}"`);
    for (const dim of allDims) {
      const sel = state.selected[dim.key] || [];
      if (!sel.length) continue;
      const labels = dim.kind === 'flag' ? [CS.dimLabel(dim)] : sel.map((v) => CS.labelFor(dim, v));
      parts.push(`${CS.dimLabel(dim)}: ${labels.join(' or ')}`);
    }
    return parts.length ? parts.join(' and ') : 'none (all comments)';
  }

  function csvField(v) {
    if (v === null || v === undefined) return '';
    const s = typeof v === 'boolean' ? String(v) : String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function toCSV(rows, columns) {
    const lines = [columns.map(csvField).join(',')];
    for (const r of rows) lines.push(columns.map((c) => csvField(r[c])).join(','));
    return lines.join('\r\n');
  }

  function downloadText(filename, text, mime) {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function setStickyOffsets() {
    const header = document.querySelector('header.site');
    if (header) document.documentElement.style.setProperty('--study-header-h', header.offsetHeight + 'px');
  }

  function renderComment(r, query, dimsByKey, slug) {
    const chips = [];
    if (r.stance) chips.push(CS.chipHTML(dimsByKey.stance, r.stance));
    if (r.frame) chips.push(CS.chipHTML(dimsByKey.frame, r.frame));
    const likes = CS.likesLabel(r.likes);
    const hi = (s, q) => {
      if (!q) return CS.esc(s);
      const i = s.toLowerCase().indexOf(q);
      if (i < 0) return CS.esc(s);
      return CS.esc(s.slice(0, i)) + '<mark>' + CS.esc(s.slice(i, i + q.length)) + '</mark>' + CS.esc(s.slice(i + q.length));
    };
    return `<article class="study-comment">
      <p class="text">${hi(r.text, query)}</p>
      <div class="study-comment-meta">
        ${chips.join('')}
        ${likes ? `<span class="likes">${CS.esc(likes)}</span>` : ''}
        <span>${CS.esc(CS.formatDate(r.published_at))}</span>
        <a class="view-link" href="/data/${encodeURIComponent(slug)}/c/${encodeURIComponent(r.id)}">View comment &rarr;</a>
      </div>
    </article>`;
  }

  function renderQuotesGroup(dim, rows) {
    const groups = new Map();
    for (const opt of facetValueOptions(dim)) groups.set(opt.value, { label: opt.label, rows: [] });
    for (const r of rows) {
      const v = dim.valueOf(r);
      if (groups.has(v)) groups.get(v).rows.push(r);
    }
    let html = '';
    for (const [, group] of groups) {
      if (!group.rows.length) continue;
      html += `<section class="study-quote-group">
        <h3>${CS.esc(group.label)} <span class="n">(${group.rows.length})</span></h3>
        <ul class="study-quotes-list">
          ${group.rows.map((r) => {
            const likes = CS.likesLabel(r.likes);
            return `<li>${CS.esc(r.text)}${likes ? `<span class="likes">${CS.esc(likes)}</span>` : ''}</li>`;
          }).join('')}
        </ul>
      </section>`;
    }
    return html || '<p class="study-empty">No quotes in the current filter.</p>';
  }

  async function init() {
    const slug = CS.slugFromPath();
    const listEl = document.getElementById('expList');
    let data;
    try {
      data = await CS.loadStudyData(slug);
    } catch (err) {
      listEl.innerHTML = CS.fetchErrorHTML(err, slug);
      return;
    }

    const { study, codebook, comments } = data;
    const dimsByKey = CS.dimsByKey(codebook);
    const allDims = buildAllDims(codebook, comments);

    document.title = study.title + ': Common Signals data explorer';
    const h1 = document.getElementById('studyTitle');
    if (h1) h1.textContent = study.title;
    const metaEl = document.getElementById('studyMeta');
    if (metaEl) {
      metaEl.innerHTML = `<strong>${study.counts.coded.toLocaleString()}</strong> comments coded &middot; <strong>${study.counts.clear_position_base.toLocaleString()}</strong> take a clear position &middot; ${CS.esc(study.platform)}`;
      if ((study.changelog || []).length) {
        metaEl.insertAdjacentHTML('afterend', CS.changelogHTML(study.changelog, study.version));
      }
    }
    document.querySelectorAll('[data-study-slug]').forEach((el) => { el.textContent = slug; });
    document.querySelectorAll('a[data-study-link]').forEach((el) => {
      el.setAttribute('href', el.getAttribute('data-study-link').replace('SLUG', encodeURIComponent(slug)));
    });
    if (study.article_url) {
      const articleLink = document.getElementById('articleLink');
      if (articleLink) { articleLink.href = study.article_url; articleLink.hidden = false; }
    }

    let state = stateFromURL(allDims);

    const qInput = document.getElementById('expSearch');
    const countEl = document.getElementById('expCount');
    const sortSelect = document.getElementById('expSort');
    const viewComments = document.getElementById('viewComments');
    const viewQuotes = document.getElementById('viewQuotes');
    const quotesNote = document.getElementById('quotesNote');
    const exportBtn = document.getElementById('expExport');
    const facetsEl = document.getElementById('expFacets');

    qInput.value = state.q;
    sortSelect.value = state.sort;

    const hasLikes = comments.some((c) => c.likes !== null && c.likes !== undefined);
    if (!hasLikes) {
      const likesOption = sortSelect.querySelector('option[value="likes"]');
      if (likesOption) likesOption.remove();
      if (state.sort === 'likes') { state.sort = 'thread'; sortSelect.value = 'thread'; }
    }

    function render() {
      syncURL(state, allDims);

      const activeKeys = activeFacetKeys(state, allDims);
      const singleActiveDim = activeKeys.length === 1 ? allDims.find((d) => d.key === activeKeys[0]) : null;
      const quotesAvailable = !!singleActiveDim;
      if (!quotesAvailable && state.view === 'quotes') state.view = 'comments';

      viewComments.setAttribute('aria-pressed', String(state.view === 'comments'));
      viewQuotes.setAttribute('aria-pressed', String(state.view === 'quotes'));
      viewQuotes.disabled = !quotesAvailable;
      quotesNote.hidden = quotesAvailable;
      if (!quotesAvailable) quotesNote.textContent = 'Select exactly one facet filter (and only one) to view quotes.';

      // Facets: each dimension's option counts are computed against the set
      // that already applies every OTHER active filter, so unchecking one
      // option never makes its siblings' counts vanish.
      facetsEl.innerHTML = allDims.map((dim) => {
        const base = comments.filter((r) => matches(r, state, allDims, dim.key));
        const counts = {};
        for (const r of base) {
          const v = dim.valueOf(r);
          counts[v] = (counts[v] || 0) + 1;
        }
        const selected = state.selected[dim.key] || [];
        const options = facetValueOptions(dim).map((opt) => {
          const n = counts[opt.value] || 0;
          const checked = selected.includes(opt.value) ? ' checked' : '';
          return `<label class="${n ? '' : 'zero'}"><input type="checkbox" data-key="${CS.esc(dim.key)}" value="${CS.esc(opt.value)}"${checked}> ${CS.esc(opt.label)} <span class="n">(${n})</span></label>`;
        }).join('');
        const open = selected.length ? ' open' : '';
        return `<details class="study-facet"${open}><summary>${CS.esc(CS.dimLabel(dim))}</summary><div class="study-facet-options">${options}</div></details>`;
      }).join('');
      facetsEl.querySelectorAll('input[type="checkbox"]').forEach((el) => {
        el.addEventListener('change', () => {
          const key = el.getAttribute('data-key');
          const val = el.value;
          const cur = new Set(state.selected[key] || []);
          if (el.checked) cur.add(val); else cur.delete(val);
          state.selected[key] = Array.from(cur);
          render();
        });
      });

      const filtered = sortRows(comments.filter((r) => matches(r, state, allDims)), state.sort);
      countEl.textContent = `${filtered.length.toLocaleString()} of ${comments.length.toLocaleString()} comments`;

      if (!filtered.length) {
        listEl.innerHTML = '<p class="study-empty">Nothing matches the current search and filters.</p>';
      } else if (state.view === 'quotes' && singleActiveDim) {
        listEl.innerHTML = renderQuotesGroup(singleActiveDim, filtered);
      } else {
        listEl.innerHTML = filtered.map((r) => renderComment(r, state.q, dimsByKey, slug)).join('');
      }

      exportBtn.onclick = () => {
        const columns = Object.keys(comments[0] || {});
        const filterDesc = describeFilter(state, allDims);
        const preamble = `Study: ${study.slug}. Filter: ${filterDesc}. Exported: ${new Date().toISOString().slice(0, 10)}.`;
        const csv = csvField(preamble) + '\r\n\r\n' + toCSV(filtered, columns);
        downloadText(`${study.slug}-filtered-${new Date().toISOString().slice(0, 10)}.csv`, csv, 'text/csv;charset=utf-8');
      };
    }

    qInput.addEventListener('input', () => { state.q = qInput.value.trim().toLowerCase(); render(); });
    sortSelect.addEventListener('change', () => { state.sort = sortSelect.value; render(); });
    viewComments.addEventListener('click', () => { state.view = 'comments'; render(); });
    viewQuotes.addEventListener('click', () => { if (!viewQuotes.disabled) { state.view = 'quotes'; render(); } });

    render();
    setStickyOffsets();
    window.addEventListener('resize', setStickyOffsets);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window.CS);

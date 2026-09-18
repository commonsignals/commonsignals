/* Comment detail page (/data/<slug>/c/<id>). The id is a URL path segment;
 * Cloudflare Pages rewrites any such path to this same shell (see
 * /_redirects), so the id is read from location.pathname, not a query
 * string. Depends on core.js.
 */
(function (CS) {
  'use strict';

  function idFromPath() {
    const parts = location.pathname.split('/').filter(Boolean);
    const i = parts.indexOf('c');
    return i >= 0 ? decodeURIComponent(parts[i + 1] || '') : '';
  }

  function codesForRow(row, codebook) {
    const dims = codebook.dimensions || [];
    const codes = [];
    for (const dim of dims) {
      if (dim.kind === 'single' && row[dim.key]) {
        codes.push({ dim, value: row[dim.key] });
      } else if (dim.kind === 'flag' && row[dim.key] === true) {
        codes.push({ dim, value: 'true' });
      }
    }
    return codes;
  }

  async function init() {
    const slug = CS.slugFromPath();
    const id = idFromPath();
    const mainEl = document.getElementById('cmtMain');
    const backLink = document.getElementById('backLink');
    if (backLink) backLink.href = `/data/${encodeURIComponent(slug)}/`;

    let data;
    try {
      data = await CS.loadStudyData(slug);
    } catch (err) {
      mainEl.innerHTML = CS.fetchErrorHTML(err, slug);
      return;
    }

    const { study, codebook, comments } = data;
    const byId = new Map(comments.map((r) => [r.id, r]));
    const row = byId.get(id);

    document.title = `Comment: ${study.title}`;

    if (!row) {
      mainEl.innerHTML = `<p class="study-empty">No comment with id <code>${CS.esc(id)}</code> in this study. <a href="/data/${encodeURIComponent(slug)}/">Back to the explorer</a>.</p>`;
      return;
    }

    const codesPanel = document.getElementById('cmtCodesPanel');
    const dimsByKey = CS.dimsByKey(codebook);

    let parentHTML = '';
    if (row.parent_id) {
      const parent = byId.get(row.parent_id);
      parentHTML = `<div class="parent-quote">
        <span class="label">Parent comment</span>
        <p>${CS.esc(parent ? parent.text : '(not found in this study)')}</p>
        ${parent ? `<a href="/data/${encodeURIComponent(slug)}/c/${encodeURIComponent(parent.id)}">View parent comment &rarr;</a>` : ''}
      </div>`;
    }

    const codes = codesForRow(row, codebook);
    const chipsHTML = codes.map((c) => CS.chipHTML(c.dim, c.value)).join('');

    const likes = CS.likesLabel(row.likes);
    const threadNote = row.parent_id ? 'reply' : 'top level';
    const permalink = location.origin + location.pathname;

    mainEl.innerHTML = `
      ${parentHTML}
      <p class="comment-text">${CS.esc(row.text)}</p>
      <p class="comment-facts">
        ${likes ? `<strong>${CS.esc(likes)}</strong> &middot; ` : ''}
        Published <strong>${CS.esc(CS.formatDate(row.published_at))}</strong> &middot;
        Depth <strong>${CS.esc(row.depth)}</strong> (${threadNote})
      </p>
      <div class="comment-codes">${chipsHTML}</div>
      <p class="permalink">Permalink: <a href="${CS.esc(permalink)}">${CS.esc(permalink)}</a></p>
      <div class="study-slot" data-slot="similar-comments">Similar comments (phase 4)</div>
      <div class="study-slot" data-slot="copy-citation">Copy citation (phase 4)</div>
    `;

    const h1 = document.getElementById('cmtTitle');
    if (h1) h1.textContent = 'Comment on ' + study.title;

    if (codesPanel) {
      codesPanel.innerHTML = `<h2>Codes on this comment</h2><dl>${
        codes.map((c) => {
          const def = CS.valueDef(c.dim, c.value);
          const label = def ? def.label : c.value;
          const definition = def && def.definition ? def.definition : 'No definition recorded.';
          return `<dt>${CS.esc(CS.dimLabel(c.dim))}: ${CS.esc(label)}</dt><dd>${CS.esc(definition)}</dd>`;
        }).join('') || '<dd>No codes recorded.</dd>'
      }</dl>`;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window.CS);

/* Codebook page (/data/<slug>/codebook/): renders codebook.json in full.
 * Depends on core.js.
 */
(function (CS) {
  'use strict';

  function renderDimension(dim) {
    const shared = dim.shared
      ? '<span class="shared-tag">Shared across the series</span>'
      : '<span class="shared-tag not-shared">Specific to this study</span>';
    const values = dim.values || [];
    let body;
    if (!values.length) {
      body = '<p class="study-dim-note">Descriptive field: not a coded value with its own definitions.</p>';
    } else {
      body = `<dl class="study-dim-values">${values.map((v) => `
        <div class="study-dim-value">
          <dt>${CS.esc(v.label)}</dt>
          <dd>${CS.esc(v.definition || 'No definition recorded.')}${v.example ? `<span class="example">e.g. "${CS.esc(v.example)}"</span>` : ''}</dd>
        </div>`).join('')}</dl>`;
    }
    return `<article class="study-dim">
      <h3>${CS.esc(CS.dimLabel(dim))} ${shared}</h3>
      ${body}
    </article>`;
  }

  async function init() {
    const slug = CS.slugFromPath();
    const dimsEl = document.getElementById('cbDimensions');
    let data;
    try {
      data = await CS.loadStudyData(slug);
    } catch (err) {
      dimsEl.innerHTML = CS.fetchErrorHTML(err, slug);
      return;
    }

    const { study, codebook } = data;
    document.title = `Codebook: ${study.title}`;
    const h1 = document.getElementById('cbTitle');
    if (h1) h1.textContent = 'Codebook: ' + study.title;

    const claimEl = document.getElementById('cbClaim');
    if (claimEl) claimEl.textContent = codebook.central_claim;
    const noteEl = document.getElementById('cbStanceNote');
    if (noteEl) noteEl.textContent = codebook.stance_note;

    dimsEl.innerHTML = (codebook.dimensions || []).map(renderDimension).join('');

    const downloadEl = document.getElementById('cbDownload');
    if (downloadEl) downloadEl.href = `/data/studies/${encodeURIComponent(slug)}/codebook.md`;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window.CS);

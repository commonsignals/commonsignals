/* Cross-study compare view (/data/compare/). Reads only the studies index
 * and each study's existing data.json; no new data collection, and no
 * frame comparison anywhere (frame vocabularies differ by study and are
 * not comparable). Depends on core.js.
 */
(function (CS) {
  'use strict';

  // Which stance values count as "positioned" is inferred the same way
  // scripts/data-export.py's validator does: a value counts if its own
  // string appears in the codebook's stance_note (which defines exactly
  // the positioned values, e.g. "agree = ...; disagree = ...; mixed = ...").
  function positionedValues(codebook) {
    const stanceDim = codebook.dimensions.find((d) => d.key === 'stance');
    const note = codebook.stance_note || '';
    return new Set((stanceDim.values || []).filter((v) => note.includes(v.value)).map((v) => v.value));
  }

  function tally(comments, key, allowed) {
    const counts = {};
    for (const c of comments) {
      const v = c[key];
      if (!v) continue;
      if (allowed && !allowed.has(v)) continue;
      counts[v] = (counts[v] || 0) + 1;
    }
    return counts;
  }

  function barsHTML(values, counts, base) {
    return values.map((v) => {
      const n = counts[v.value] || 0;
      const pct = base ? (100 * n / base) : 0;
      return `<div class="cmp-bar-row">
        <span class="cmp-bar-label">${CS.esc(v.label)}</span>
        <div class="cmp-bar-track"><div class="cmp-bar-fill" style="width:${pct.toFixed(1)}%"></div></div>
        <span class="cmp-bar-pct">${pct.toFixed(1)}% <span class="cmp-bar-n">(${n.toLocaleString()})</span></span>
      </div>`;
    }).join('');
  }

  function studyBlockHTML(entry, dimKey) {
    const { study, codebook, comments } = entry;
    const dim = codebook.dimensions.find((d) => d.key === dimKey);
    if (!dim) return '';

    let base, counts, baseNote, values;
    if (dimKey === 'stance') {
      const positioned = positionedValues(codebook);
      base = study.counts.clear_position_base;
      counts = tally(comments, 'stance', positioned);
      values = (dim.values || []).filter((v) => positioned.has(v.value));
      baseNote = `${base.toLocaleString()} of ${study.counts.coded.toLocaleString()} coded take a clear position`;
    } else {
      base = study.counts.coded;
      counts = tally(comments, dimKey, null);
      values = dim.values || [];
      baseNote = `Out of ${base.toLocaleString()} coded`;
    }

    return `<div class="cmp-study-block">
      <h3><a href="/data/${encodeURIComponent(study.slug)}/">${CS.esc(study.title)}</a></h3>
      ${barsHTML(values, counts, base)}
      <p class="cmp-base-note">${CS.esc(baseNote)}</p>
    </div>`;
  }

  const DIMENSIONS = [
    {
      key: 'stance',
      label: 'Stance',
      intro: "Percentages use each study's own clear-position base (agree, disagree and mixed only, excluding na and unclear), shown against that study's total coded count for context.",
    },
    {
      key: 'emotion',
      label: 'Emotion',
      intro: "Percentages use each study's total coded count. The category list is identical across all five studies.",
    },
    {
      key: 'format_reaction',
      label: 'Format reaction',
      intro: "Percentages use each study's total coded count. Four studies (Soares, Cotra, METR, Coxon) share one category list (none, mock, condescended, imitates, praise). The Amanpour segment uses a narrower, interview-specific list (none, praise, criticism), since it is reacting to a broadcast interview rather than a reel, thread or podcast episode. Read its bars as their own thing, not a like-for-like slice of the other four's categories.",
    },
  ];

  async function init() {
    const root = document.getElementById('cmpDimensions');
    const loading = document.getElementById('cmpLoading');

    let indexData;
    try {
      indexData = await CS.fetchJSON('/data/studies/index.json');
    } catch (err) {
      if (loading) loading.textContent = 'Could not load the studies index (' + err.message + ').';
      return;
    }

    let loaded;
    try {
      loaded = await Promise.all(indexData.studies.map((s) => CS.loadStudyData(s.slug)));
    } catch (err) {
      if (loading) loading.textContent = 'Could not load one of the studies (' + err.message + ').';
      return;
    }

    if (loading) loading.remove();

    root.innerHTML = DIMENSIONS.map((d) => `
      <section class="cmp-dimension">
        <h2>${CS.esc(d.label)}</h2>
        <p class="cmp-dimension-intro">${CS.esc(d.intro)}</p>
        <div class="cmp-study-grid">
          ${loaded.map((entry) => studyBlockHTML(entry, d.key)).join('')}
        </div>
      </section>
    `).join('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window.CS);

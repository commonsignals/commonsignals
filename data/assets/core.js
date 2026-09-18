/* Shared helpers for the study explorer, comment detail and codebook pages
 * under /data/<slug>/. Every page derives its slug from location.pathname
 * and fetches /data/<slug>/data.json, so none of this hardcodes a study.
 */
window.CS = window.CS || {};
(function (CS) {
  'use strict';

  CS.STUB_CODER = 'not_coded_empty_stub';

  CS.esc = function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  };

  CS.slugFromPath = function slugFromPath() {
    const parts = location.pathname.split('/').filter(Boolean);
    const i = parts.indexOf('data');
    return i >= 0 ? parts[i + 1] : undefined;
  };

  CS.fetchJSON = function fetchJSON(url) {
    return fetch(url, { cache: 'no-cache' }).then((r) => {
      if (!r.ok) throw new Error(url + ' ' + r.status);
      return r.json();
    });
  };

  CS.loadStudyData = function loadStudyData(slug) {
    return CS.fetchJSON(`/data/${encodeURIComponent(slug)}/data.json`);
  };

  CS.dimsByKey = function dimsByKey(codebook) {
    return Object.fromEntries((codebook.dimensions || []).map((d) => [d.key, d]));
  };

  CS.valueDef = function valueDef(dim, value) {
    if (!dim) return null;
    return (dim.values || []).find((v) => v.value === value) || null;
  };

  CS.labelFor = function labelFor(dim, value) {
    const v = CS.valueDef(dim, value);
    return v ? v.label : value;
  };

  // Some codebooks write flag labels as raw shorthand (e.g. "m_messenger_
  // credentials"); humanise anything identifier-shaped rather than print it
  // verbatim. Labels that are already prose (e.g. "Stance") pass through.
  CS.dimLabel = function dimLabel(dim) {
    const label = dim.label || dim.key;
    if (!/^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$/.test(label)) return label;
    return dim.key
      .replace(/^mentions_/, '')
      .replace(/_/g, ' ')
      .replace(/^./, (c) => c.toUpperCase());
  };

  CS.formatDate = function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  // "September 2026", matching the month-and-year precision the site's own
  // article citations use (never a specific day).
  CS.formatMonthYear = function formatMonthYear(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString('en-GB', { year: 'numeric', month: 'long' });
  };

  CS.likesLabel = function likesLabel(n) {
    if (n === null || n === undefined) return null;
    return n === 1 ? '1 like' : `${n.toLocaleString()} likes`;
  };

  let tipCounter = 0;
  // A chip for one assigned code. Shows the value's own definition on hover
  // or focus; falls back to a plain, non-interactive chip when there is no
  // definition to show (e.g. this study's emotion values carry none).
  CS.chipHTML = function chipHTML(dim, value, opts) {
    opts = opts || {};
    const def = CS.valueDef(dim, value);
    const label = def ? def.label : (dim ? CS.dimLabel(dim) : value);
    const definition = def && def.definition ? def.definition : '';
    const cls = ['code-chip'].concat(opts.className ? [opts.className] : []).join(' ');
    if (!definition) return `<span class="${cls}">${CS.esc(label)}</span>`;
    const tipId = 'tip' + (tipCounter++);
    return `<span class="${cls}" tabindex="0" aria-describedby="${tipId}">${CS.esc(label)}<span class="code-chip-tip" role="tooltip" id="${tipId}">${CS.esc(definition)}</span></span>`;
  };

  // A <details> block, closed by default (per contract, one click to expand,
  // not buried), listing a study's version history from study.json's
  // changelog (oldest first, as stored). Used on both a study's own explorer
  // page and its card on /data/, so a revised study's history (a recode, a
  // superseded run) is visible in both places without opening study.json.
  CS.changelogHTML = function changelogHTML(changelog, version) {
    if (!changelog || !changelog.length) return '';
    const items = changelog.map((c) =>
      `<li><strong>v${CS.esc(c.version)}</strong>, ${CS.esc(CS.formatDate(c.date))}: ${CS.esc(c.note)}</li>`
    ).join('');
    const label = version ? `Changelog (version ${CS.esc(version)})` : 'Changelog';
    return `<details class="study-changelog"><summary>${label}</summary><ul>${items}</ul></details>`;
  };

  CS.fetchErrorHTML = function fetchErrorHTML(err, slug) {
    const subject = encodeURIComponent('Data explorer: ' + (slug || ''));
    return `<p class="study-empty">Could not load this study's data (${CS.esc(err.message)}). Try the raw files directly: <a href="/data/studies/${CS.esc(slug)}/study.json">study.json</a>, <a href="/data/studies/${CS.esc(slug)}/comments.csv">comments.csv</a>, or <a href="mailto:hello@commonsignals.org?subject=${subject}">tell us if that looks wrong</a>.</p>`;
  };
})(window.CS);

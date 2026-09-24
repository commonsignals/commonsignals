// Britain Talks AI / America Talks AI survey runtime.
// No cookies, no analytics, no third-party scripts or fonts. Everything
// respondent-facing comes from instrument.json and messages/<country>.json;
// nothing is hard-coded here beyond structural chrome (buttons, progress bar).
(function () {
  "use strict";

  const country = document.body.getAttribute("data-country");
  const root = document.getElementById("survey-app");
  const params = new URLSearchParams(window.location.search);
  const isTest = params.get("test") === "1";
  const study = isTest ? "test" : (params.get("study") || "test");
  const prolificPid = params.get("PROLIFIC_PID") || null;
  const prolificSession = params.get("SESSION_ID") || null;
  const source = prolificPid ? "prolific" : "direct";

  const STORAGE_KEY = `survey:${study}:${country}`;

  // --- Small seeded RNG so a resumed session reproduces the same order ----
  function hashSeed(str) {
    let h = 1779033703 ^ str.length;
    for (let i = 0; i < str.length; i++) {
      h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }
    return () => {
      h = Math.imul(h ^ (h >>> 16), 2246822507);
      h = Math.imul(h ^ (h >>> 13), 3266489909);
      h ^= h >>> 16;
      return h >>> 0;
    };
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function shuffle(arr, rng) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* ignore, start fresh */ }
    return null;
  }
  function saveLocal() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) { /* storage unavailable; server save still runs */ }
  }
  function clearLocal() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
  }

  let state = loadState();
  if (!state || state.completed) {
    const responseId = uuid();
    state = {
      responseId,
      seed: hashSeed(responseId)(),
      answers: {},
      timings: {},
      order: {},
      screenIndex: 0,
      condition: null,
      comprehensionPass: null,
      screenedOut: false,
      completed: false,
      startedAtMs: Date.now(),
    };
  }
  state.answers.A2 = prolificPid || state.answers.A2 || null;

  // --- Text helpers ---------------------------------------------------------
  function localize(value) {
    if (value === null || value === undefined) return value;
    if (typeof value === "string") return value;
    if (typeof value === "object" && (value.uk || value.us)) return value[country] ?? value.uk ?? value.us;
    return value;
  }
  function fillTemplate(text, fills) {
    if (typeof text !== "string" || !fills) return text;
    return text.replace(/\{(\w+)\}/g, (m, key) => (key in fills ? fills[key] : m));
  }
  function countryOf(item) {
    return item.country && item.country[country] ? item.country[country] : null;
  }
  function itemPrompt(item) {
    let prompt = localize(item.prompt);
    const c = countryOf(item);
    if (c) prompt = fillTemplate(prompt, c);
    return prompt;
  }
  function itemOptions(item, instrument) {
    const c = countryOf(item);
    if (c && c.options) return c.options;
    if (item.options) return item.options;
    if (item.options_from) {
      const src = instrument.itemsByCode[item.options_from];
      let opts = (src.rows || []).map((r) => ({ value: r.code, label: localize(r.label) }));
      if (item.extra_options) opts = opts.concat(item.extra_options);
      return opts;
    }
    if (item.options_from === undefined && item.code === "H2") {
      // handled specially below via options_from: "H1_selected"
    }
    return [];
  }

  // --- Screen-out conditions --------------------------------------------------
  function screenoutCondition(name, value) {
    if (name === "lt_18") return Number(value) < 18;
    if (name === "eq_disagree") return value === "disagree";
    return false;
  }

  let instrument, messages, studyInfo;

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === "class") node.className = attrs[k];
      else if (k === "html") node.innerHTML = attrs[k];
      else node.setAttribute(k, attrs[k]);
    }
    (children || []).forEach((c) => c && node.appendChild(typeof c === "string" ? document.createTextNode(c) : c));
    return node;
  }

  function fatalScreen(message) {
    root.innerHTML = "";
    root.appendChild(el("div", { class: "survey-fatal" }, [
      el("p", {}, [message]),
    ]));
  }

  // --- Build the ordered list of screens --------------------------------------
  function buildScreens() {
    const rng = mulberry32(state.seed);
    const screens = [];
    for (const item of instrument.items) {
      if (item.type === "info" || item.type === "info_header") {
        screens.push({ type: "text_screen", item });
        continue;
      }
      if (item.type === "hidden") continue; // auto-filled, not shown
      if (item.type === "consent") {
        screens.push({ type: "single", item });
        continue;
      }
      const c = countryOf(item);
      if (c && c.skip) continue;

      if (item.type === "grid" || item.type === "slider_grid") {
        let rows = item.rows || [];
        if (item.code === "G2" && rows.some((r) => r.label === null)) continue; // unfrozen, skip
        if (item.randomize) rows = shuffle(rows, rng);
        const size = item.screens_of || rows.length;
        for (let i = 0; i < rows.length; i += size) {
          screens.push({
            type: item.type, item,
            rows: rows.slice(i, i + size),
            page: Math.floor(i / size) + 1,
            totalPages: Math.ceil(rows.length / size),
          });
        }
        continue;
      }
      if (item.type === "grid_two_step") {
        let rows = (item.rows || []).filter((r) => r.label !== null);
        if (!rows.length) continue;
        if (item.randomize) rows = shuffle(rows, rng);
        screens.push({ type: "grid_two_step", item, rows });
        continue;
      }
      if (item.type === "grid_dynamic") {
        screens.push({ type: "grid_dynamic", item });
        continue;
      }
      screens.push({ type: item.type, item });
    }
    return screens;
  }

  function evalRouting(item) {
    if (!item.routing) return true;
    const r = item.routing;
    if (r.show_if) {
      const v = state.answers[r.show_if.code];
      if (r.show_if.in) return r.show_if.in.includes(v);
      if ("eq" in r.show_if) return v === r.show_if.eq;
    }
    if (r.hide_if) {
      const v = state.answers[r.hide_if.code];
      if ("eq" in r.hide_if) return v !== r.hide_if.eq;
      if (r.hide_if.in) return !r.hide_if.in.includes(v);
    }
    return true;
  }

  function isRequired(screen) {
    if (screen.item.required === false) return false;
    if (screen.type === "text_screen") return false;
    return true;
  }

  function answered(screen) {
    const item = screen.item;
    if (screen.type === "grid" || screen.type === "slider_grid") {
      return screen.rows.every((r) => state.answers[r.code] !== undefined && state.answers[r.code] !== null && state.answers[r.code] !== "");
    }
    if (screen.type === "grid_two_step") {
      return screen.rows.every((r) => {
        const heard = state.answers[`${r.code}_heard`];
        if (heard === "Never heard of them") return true;
        return heard !== undefined && state.answers[`${r.code}_trust`] !== undefined;
      });
    }
    if (screen.type === "grid_dynamic") {
      const slots = item.slot_codes;
      return slots.every((s) => state.answers[s] !== undefined && state.answers[s] !== "");
    }
    if (!isRequired(screen)) return true;
    const v = state.answers[item.code];
    if (screen.type === "multi") return Array.isArray(v) && v.length > 0;
    return v !== undefined && v !== null && v !== "";
  }

  // --- Rendering ---------------------------------------------------------------
  let screens = [];
  let pointer = 0;

  function computeNextDisabled(screen) {
    let disabled = isRequired(screen) && !answered(screen);
    // Mid-grid carousel: don't enable Next until every row of this page is answered.
    if ((screen.type === "grid" || screen.type === "slider_grid") && window.innerWidth < 700) {
      disabled = !answered(screen);
    }
    return disabled;
  }
  function refreshNextButton() {
    const btn = root.querySelector(".survey-next");
    const screen = screens[pointer];
    if (btn && screen) btn.disabled = computeNextDisabled(screen);
  }

  function progressPct() {
    return Math.min(100, Math.round((pointer / Math.max(1, screens.length - 1)) * 100));
  }

  function chrome(contentNode, opts) {
    root.innerHTML = "";
    const bar = el("div", { class: "survey-progress" }, [
      el("div", { class: "survey-progress-fill", style: `width:${progressPct()}%` }),
    ]);
    root.appendChild(bar);
    if (isTest) {
      root.appendChild(el("p", { class: "survey-testbadge" }, [
        `Test mode — study=${study}${state.condition !== null ? `, condition ${state.condition}` : ""}`,
      ]));
    }
    const form = el("form", { class: "survey-screen", novalidate: "novalidate" }, [contentNode]);
    const nav = el("div", { class: "survey-nav" });
    const noBack = opts && opts.noBack;
    if (pointer > 0 && !noBack) {
      const back = el("button", { type: "button", class: "btn btn-ghost survey-back" }, ["Back"]);
      back.addEventListener("click", () => { pointer--; render(); });
      nav.appendChild(back);
    }
    const next = el("button", { type: "submit", class: "btn btn-primary survey-next" }, [opts && opts.nextLabel || "Next"]);
    if (opts && opts.nextDisabled) next.disabled = true;
    nav.appendChild(next);
    form.appendChild(nav);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (opts && opts.onSubmit) opts.onSubmit();
    });
    root.appendChild(form);
    if (opts && opts.afterRender) opts.afterRender(form);
  }

  function radioGroup(name, options, current, onChange) {
    const wrap = el("div", { class: "survey-options", role: "radiogroup" });
    options.forEach((opt, i) => {
      const id = `${name}_${i}`;
      const input = el("input", { type: "radio", name, id, value: opt.value });
      if (current === opt.value) input.checked = true;
      input.addEventListener("change", () => onChange(opt.value));
      const label = el("label", { for: id, class: "survey-option" }, [input, el("span", {}, [opt.label])]);
      wrap.appendChild(label);
    });
    return wrap;
  }

  function checkGroup(name, options, current, onChange, exclusiveValue, max) {
    const wrap = el("div", { class: "survey-options" });
    let selected = Array.isArray(current) ? current.slice() : [];
    options.forEach((opt, i) => {
      const id = `${name}_${i}`;
      const input = el("input", { type: "checkbox", name, id, value: opt.value });
      input.checked = selected.includes(opt.value);
      input.addEventListener("change", () => {
        if (input.checked) {
          if (opt.value === exclusiveValue) selected = [opt.value];
          else selected = selected.filter((v) => v !== exclusiveValue).concat(opt.value);
          if (max && selected.length > max) {
            selected.shift();
          }
        } else {
          selected = selected.filter((v) => v !== opt.value);
        }
        onChange(selected);
        render();
      });
      const label = el("label", { for: id, class: "survey-option" }, [input, el("span", {}, [opt.label])]);
      wrap.appendChild(label);
    });
    return wrap;
  }

  function sliderInput(name, min, max, current, onChange) {
    const value = current !== undefined && current !== null && current !== "" ? current : Math.round((min + max) / 2);
    const input = el("input", {
      type: "range", name, id: name, min, max, step: 1, value,
      "aria-valuemin": min, "aria-valuemax": max,
    });
    const out = el("output", { for: name, class: "survey-slider-value" }, [String(value)]);
    input.addEventListener("input", () => {
      out.textContent = input.value;
      onChange(Number(input.value));
    });
    return el("div", { class: "survey-slider" }, [input, out]);
  }

  function renderGridResponsive(rows, scale, getVal, setVal, extraLabel) {
    const wrap = el("div", { class: "survey-grid" });
    // Table layout for wider screens; CSS hides/shows based on width.
    const table = el("table", { class: "survey-grid-table" });
    const thead = el("thead", {}, [el("tr", {}, [el("th", {}, [""])].concat(scale.map((s) => el("th", {}, [s]))))]);
    table.appendChild(thead);
    const tbody = el("tbody");
    rows.forEach((row) => {
      const tr = el("tr", {}, [el("th", { scope: "row" }, [localize(row.label)])]);
      scale.forEach((s) => {
        const id = `${row.code}_${slugify(s)}`;
        const input = el("input", { type: "radio", name: row.code, id, value: s });
        if (getVal(row.code) === s) input.checked = true;
        input.addEventListener("change", () => { setVal(row.code, s); render(); });
        tr.appendChild(el("td", {}, [el("label", { for: id, class: "sr-only" }, [`${localize(row.label)}: ${s}`]), input]));
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);

    // One-statement-per-screen carousel for narrow screens.
    const subIndex = state._gridSub || 0;
    const idx = Math.min(subIndex, rows.length - 1);
    const row = rows[idx];
    const carousel = el("div", { class: "survey-grid-carousel" }, [
      el("p", { class: "survey-grid-progress" }, [`Statement ${idx + 1} of ${rows.length}`]),
      el("p", { class: "survey-grid-statement" }, [localize(row.label)]),
      radioGroup(row.code, scale.map((s) => ({ value: s, label: s })), getVal(row.code), (v) => {
        setVal(row.code, v);
        if (idx < rows.length - 1) state._gridSub = idx + 1;
        render();
      }),
    ]);
    if (idx > 0) {
      const prevRow = el("button", { type: "button", class: "btn btn-ghost survey-grid-prev" }, ["Previous statement"]);
      prevRow.addEventListener("click", () => { state._gridSub = idx - 1; render(); });
      carousel.appendChild(prevRow);
    }
    wrap.appendChild(carousel);
    return wrap;
  }
  function slugify(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  }

  function render() {
    if (pointer >= screens.length) return finish();
    const screen = screens[pointer];
    const item = screen.item;

    if (!evalRouting(item)) {
      pointer += state.__dir === "back" ? -1 : 1;
      return render();
    }

    if (item.code !== state._lastGridItem) state._gridSub = 0;
    state._lastGridItem = item.code;

    const noBack = pointer >= screens.findIndex((s) => s.item.code === instrument.no_back_from) && screens.findIndex((s) => s.item.code === instrument.no_back_from) !== -1;

    const nextDisabled = computeNextDisabled(screen);

    let content;
    switch (screen.type) {
      case "text_screen":
        content = el("div", { class: "survey-text" }, itemPrompt(item).split("\n\n").map((p) => el("p", {}, [p])));
        break;

      case "single": {
        const opts = itemOptions(item, instrument);
        content = el("div", {}, [
          el("h2", { class: "survey-prompt" }, [itemPrompt(item)]),
          radioGroup(item.code, opts, state.answers[item.code], (v) => {
            state.answers[item.code] = v;
            const term = opts.find((o) => o.value === v && o.terminate);
            if (term) triggerScreenout("eq_disagree");
            else refreshNextButton();
          }),
          item.type === "consent" ? el("p", { class: "survey-privacy-link" }, [
            "Read our ", el("a", { href: "/survey/privacy/", target: "_blank", rel: "noopener" }, ["privacy notice for this survey"]), ".",
          ]) : null,
        ].filter(Boolean));
        break;
      }

      case "multi": {
        let opts = item.options || [];
        if (item.options_template) {
          opts = item.options_template.map((o) => ({ value: localize(o), label: localize(o) }));
        }
        if (item.options_from === "H1_selected") {
          const chosen = state.answers.H1 || [];
          opts = (instrument.itemsByCode.H1.options_template || [])
            .map((o) => ({ value: localize(o), label: localize(o) }))
            .filter((o) => chosen.includes(o.value));
        }
        if (item.extra_options) opts = opts.concat(item.extra_options);
        content = el("div", {}, [
          el("h2", { class: "survey-prompt" }, [itemPrompt(item)]),
          checkGroup(item.code, opts, state.answers[item.code], (v) => { state.answers[item.code] = v; }, item.exclusive_option, item.max_selections),
        ]);
        break;
      }

      case "numeric": {
        const input = el("input", { type: "number", name: item.code, min: item.min, max: item.max, value: state.answers[item.code] || "" });
        input.addEventListener("input", () => { state.answers[item.code] = input.value === "" ? "" : Number(input.value); refreshNextButton(); });
        content = el("div", {}, [el("h2", { class: "survey-prompt" }, [itemPrompt(item)]), input]);
        break;
      }

      case "slider": {
        content = el("div", {}, [
          el("h2", { class: "survey-prompt" }, [itemPrompt(item)]),
          sliderInput(item.code, item.min, item.max, state.answers[item.code], (v) => { state.answers[item.code] = v; refreshNextButton(); }),
        ]);
        if (item.extra_options) {
          content.appendChild(checkGroup(`${item.code}_dk`, item.extra_options, state.answers[`${item.code}_dk`], (v) => { state.answers[`${item.code}_dk`] = v; }));
        }
        break;
      }

      case "text": {
        const ta = el("textarea", { name: item.code, rows: item.rows || 3 }, [state.answers[item.code] || ""]);
        ta.value = state.answers[item.code] || "";
        ta.addEventListener("input", () => { state.answers[item.code] = ta.value; refreshNextButton(); });
        content = el("div", {}, [el("h2", { class: "survey-prompt" }, [itemPrompt(item)]), ta]);
        break;
      }

      case "grid":
      case "slider_grid": {
        const scale = item.scale || Array.from({ length: (item.max - item.min + 1) }, (_, i) => String(item.min + i));
        content = el("div", {}, [
          el("h2", { class: "survey-prompt" }, [itemPrompt(item)]),
          screen.totalPages > 1 ? el("p", { class: "survey-subprogress" }, [`Page ${screen.page} of ${screen.totalPages}`]) : null,
          renderGridResponsive(screen.rows, scale, (code) => state.answers[code], (code, v) => { state.answers[code] = v; }),
        ].filter(Boolean));
        break;
      }

      case "grid_two_step": {
        const wrap = el("div", {}, [el("h2", { class: "survey-prompt" }, [itemPrompt(item)])]);
        screen.rows.forEach((row) => {
          const rowWrap = el("div", { class: "survey-two-step" }, [
            el("p", { class: "survey-grid-statement" }, [localize(row.label)]),
            radioGroup(`${row.code}_heard`, item.step1_options.map((o) => ({ value: o, label: o })), state.answers[`${row.code}_heard`], (v) => {
              state.answers[`${row.code}_heard`] = v;
              if (v === "Never heard of them") delete state.answers[`${row.code}_trust`];
              render();
            }),
          ]);
          if (state.answers[`${row.code}_heard`] === "Heard of them") {
            rowWrap.appendChild(radioGroup(`${row.code}_trust`, item.step2_scale.map((o) => ({ value: o, label: o })), state.answers[`${row.code}_trust`], (v) => { state.answers[`${row.code}_trust`] = v; refreshNextButton(); }));
          }
          wrap.appendChild(rowWrap);
        });
        content = wrap;
        break;
      }

      case "grid_dynamic": {
        if (!state.order.E3_slots) {
          const rng = mulberry32(state.seed + 1);
          const e2 = state.answers.E2;
          const rows = instrument.itemsByCode.E1.rows;
          const chosen = [];
          if (e2 && e2 !== "none") chosen.push(e2);
          if (!chosen.includes("E1_09")) chosen.push("E1_09");
          const remaining = rows.map((r) => r.code).filter((c) => !chosen.includes(c));
          chosen.push(shuffle(remaining, rng)[0]);
          const order = shuffle(chosen.slice(0, 3), rng);
          state.order.E3_slots = {};
          item.slot_codes.forEach((slot, i) => { state.order.E3_slots[slot] = order[i]; });
        }
        const wrap = el("div", {}, [el("h2", { class: "survey-prompt" }, [itemPrompt(item)])]);
        item.slot_codes.forEach((slot) => {
          const issueCode = state.order.E3_slots[slot];
          const rowDef = instrument.itemsByCode.E1.rows.find((r) => r.code === issueCode);
          state.timings[`${slot}_issue`] = issueCode;
          wrap.appendChild(el("div", { class: "survey-two-step" }, [
            el("p", { class: "survey-grid-statement" }, [localize(rowDef.label)]),
            radioGroup(slot, item.scale.map((o) => ({ value: o, label: o })), state.answers[slot], (v) => { state.answers[slot] = v; refreshNextButton(); }),
          ]));
        });
        content = wrap;
        break;
      }

      case "message_exposure": {
        content = renderMessageExposure(item);
        break;
      }

      case "message": {
        if (!item.link_url) { pointer++; return render(); }
        const link = el("a", { href: item.link_url, target: "_blank", rel: "noopener" }, ["Open the letter"]);
        link.addEventListener("click", () => { state.answers.F10_click = 1; });
        content = el("div", {}, [el("p", {}, [itemPrompt(item)]), link]);
        break;
      }

      default:
        content = el("p", {}, [itemPrompt(item) || ""]);
    }

    chrome(content, {
      noBack,
      nextDisabled,
      onSubmit: () => {
        advance(1);
      },
    });
  }

  function renderMessageExposure(item) {
    if (state.condition === null) {
      const rng = mulberry32(state.seed + 2);
      state.condition = Math.floor(rng() * 7);
    }
    const cond = messages.find((m) => m.condition === state.condition);
    const dwellSeconds = item.min_dwell_seconds || 20;
    const wrap = el("div", { class: "survey-message" }, [
      el("p", { class: "survey-prompt" }, [itemPrompt(item)]),
      el("div", { class: "survey-message-text" }, cond.text.split("\n\n").map((p) => el("p", {}, [p]))),
    ]);
    const startedAt = state._msgStartedAt || (state._msgStartedAt = Date.now());
    let remaining = isTest ? 0 : Math.max(0, dwellSeconds - Math.floor((Date.now() - startedAt) / 1000));
    const countdown = el("p", { class: "survey-dwell", "aria-live": "polite" }, [
      remaining > 0 ? `Next available in ${remaining}s` : "",
    ]);
    wrap.appendChild(countdown);
    const timer = remaining > 0 ? setInterval(() => {
      remaining--;
      countdown.textContent = remaining > 0 ? `Next available in ${remaining}s` : "";
      const btn = root.querySelector(".survey-next");
      if (btn && remaining <= 0) btn.disabled = false;
      if (remaining <= 0) clearInterval(timer);
    }, 1000) : null;

    setTimeout(() => {
      const btn = root.querySelector(".survey-next");
      if (btn) btn.disabled = remaining > 0;
    }, 0);

    wrap._onAdvance = () => {
      state.timings.F0_time = Math.round((Date.now() - startedAt) / 1000);
    };
    return wrap;
  }

  function triggerScreenout(conditionName) {
    state.screenedOut = true;
    saveState(true).then(() => redirectScreenout());
  }

  async function redirectScreenout() {
    clearLocal();
    if (isTest) {
      fatalScreen("You would be screened out here. (Test mode: not redirecting.)");
      return;
    }
    const url = studyInfo && studyInfo.prolific_screenout_url;
    if (url) {
      window.location.href = url;
    } else {
      fatalScreen("Thank you. Based on your answers, you are not eligible to continue with this survey.");
    }
  }

  function advance(dir) {
    const screen = screens[pointer];
    if (!screen) return; // already past the last screen and finishing
    if (screen.item && screen.item.code === "F0") {
      const node = root.querySelector(".survey-message");
      if (node && node._onAdvance) node._onAdvance();
    }
    // Screen-out rules evaluated right after the relevant item is answered.
    for (const rule of instrument.screenout_rules) {
      if (screen.item.code === rule.code && screenoutCondition(rule.condition, state.answers[rule.code])) {
        return triggerScreenout(rule.condition);
      }
    }
    state._gridSub = 0;
    state.__dir = dir > 0 ? "fwd" : "back";
    pointer += dir;
    state.screenIndex = pointer;
    saveState(false);
    render();
  }

  async function saveState(immediate) {
    saveLocal();
    const payload = {
      response_id: state.responseId,
      study, country, source,
      prolific_pid: prolificPid,
      prolific_session: prolificSession,
      condition: state.condition,
      screened_out: state.screenedOut,
      last_item: screens[pointer] ? screens[pointer].item.code : null,
      comprehension_pass: state.comprehensionPass,
      device: /Mobi|Android/i.test(navigator.userAgent) ? "mobile" : "desktop",
      answers: state.answers,
      timings: state.timings,
    };
    try {
      await fetch("/api/survey/save", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: !immediate,
      });
    } catch (e) { /* best effort; localStorage keeps state for the next save */ }
  }

  let finishing = false;
  async function finish() {
    if (finishing) return;
    finishing = true;
    // Replace the last screen straight away so its Next button can't be
    // pressed again while the final save and completion calls are in flight.
    root.innerHTML = "";
    root.appendChild(el("div", { class: "survey-done", "aria-live": "polite" }, [
      el("p", {}, ["Saving your answers..."]),
    ]));
    await saveState(true);
    let result = {};
    try {
      const resp = await fetch("/api/survey/complete", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ response_id: state.responseId, comprehension_pass: state.comprehensionPass }),
      });
      result = await resp.json();
    } catch (e) { /* fall through to code display */ }
    state.completed = true;
    clearLocal();

    root.innerHTML = "";
    if (isTest) {
      root.appendChild(el("div", { class: "survey-done" }, [el("p", {}, ["Test complete. In a live study this respondent would now be redirected to Prolific."])]));
      return;
    }
    if (result.completion_url) {
      window.location.href = result.completion_url;
      return;
    }
    const code = result.completion_code || "THANKYOU";
    root.appendChild(el("div", { class: "survey-done" }, [
      el("p", {}, ["Thank you for completing the survey. Your completion code is:"]),
      el("p", { class: "survey-code" }, [code]),
      el("p", {}, ["Please copy this code and enter it wherever you were asked to."]),
    ]));
  }

  // --- Comprehension check option set -----------------------------------------
  function setComprehensionOptions() {
    const f1 = instrument.itemsByCode.F1;
    const seen = [];
    messages.forEach((m) => { if (!seen.includes(m.comprehension_answer)) seen.push(m.comprehension_answer); });
    f1.options = seen.map((a) => ({ value: a, label: a }));
  }

  // --- Boot ---------------------------------------------------------------------
  async function boot() {
    try {
      const [instrumentResp, messagesResp, studyResp] = await Promise.all([
        fetch("/survey/instrument.json"),
        fetch(`/survey/messages/${country}.json`),
        fetch(`/api/survey/study?study=${encodeURIComponent(study)}`),
      ]);
      instrument = await instrumentResp.json();
      messages = await messagesResp.json();
      studyInfo = studyResp.ok ? await studyResp.json() : null;
    } catch (e) {
      return fatalScreen("Sorry, the survey could not be loaded. Please try again shortly.");
    }

    if (!isTest && messages.some((m) => m.status === "draft")) {
      return fatalScreen("This survey is not yet open outside of test mode.");
    }
    if (!studyInfo || !studyInfo.open) {
      return fatalScreen("This study is not currently open. Please check back later.");
    }

    instrument.itemsByCode = {};
    instrument.items.forEach((it) => { instrument.itemsByCode[it.code] = it; });
    setComprehensionOptions();

    screens = buildScreens();

    pointer = state.screenIndex || 0;
    render();
    window.addEventListener("beforeunload", () => saveLocal());
  }

  boot();
})();

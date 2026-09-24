// GET /api/survey/export?study=<id>&format=csv|json
// Admin (Bearer SURVEY_ADMIN_TOKEN): wide-format export, one column per item
// code (grid rows and multi-select options each get their own column).
// Never includes prolific_pid or prolific_session. Also serves a matching
// codebook at ?study=<id>&format=codebook.
import instrument from "../../../survey/instrument.json";
import { json, isAuthorized } from "./_lib.js";

function slug(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 40);
}

function promptText(prompt) {
  if (typeof prompt === "string") return prompt;
  if (prompt && typeof prompt === "object") return prompt.uk || prompt.us || "";
  return "";
}

// Returns a list of { key, module, item_code, type, description, get(ctx) }
// columns, in instrument order, where ctx = { answers, timings, row }.
function buildColumns() {
  const cols = [];
  const NO_ANSWER_TYPES = new Set(["info", "info_header"]);

  for (const item of instrument.items) {
    const mod = item.module;
    const desc = promptText(item.prompt);

    if (NO_ANSWER_TYPES.has(item.type)) continue;

    if (item.type === "message_exposure") {
      cols.push({
        key: `${item.code}_time`, module: mod, item_code: item.code, type: item.type,
        description: `${desc} (seconds spent on the message screen)`,
        get: (ctx) => ctx.timings[`${item.code}_time`] ?? "",
      });
      continue;
    }

    if (item.type === "message") {
      cols.push({
        key: `${item.code}_click`, module: mod, item_code: item.code, type: item.type,
        description: `${desc} (1 if the link was clicked, else 0)`,
        get: (ctx) => (ctx.answers[`${item.code}_click`] ?? ctx.timings[`${item.code}_click`] ?? "") ? 1 : 0,
      });
      continue;
    }

    if (item.type === "grid_dynamic") {
      for (const slotCode of item.slot_codes || []) {
        cols.push({
          key: slotCode, module: mod, item_code: item.code, type: item.type,
          description: `${desc} (response for the issue shown in this slot)`,
          get: (ctx) => ctx.answers[slotCode] ?? "",
        });
        cols.push({
          key: `${slotCode}_issue`, module: mod, item_code: item.code, type: item.type,
          description: `${desc} (which issue code was shown in slot ${slotCode})`,
          get: (ctx) => ctx.timings[`${slotCode}_issue`] ?? "",
        });
      }
      continue;
    }

    if (item.type === "grid_two_step") {
      for (const row of item.rows || []) {
        if (row.label === null) continue; // unfilled placeholder row, skip until frozen
        cols.push({
          key: `${row.code}_heard`, module: mod, item_code: item.code, type: item.type,
          description: `${row.label} (heard of them: 1/0)`,
          get: (ctx) => ctx.answers[`${row.code}_heard`] ?? "",
        });
        cols.push({
          key: `${row.code}_trust`, module: mod, item_code: item.code, type: item.type,
          description: `${row.label} (trust rating, if heard of them)`,
          get: (ctx) => ctx.answers[`${row.code}_trust`] ?? "",
        });
      }
      continue;
    }

    if (item.type === "grid" || item.type === "slider_grid") {
      for (const row of item.rows || []) {
        const rowLabel = promptText(row.label) || row.label;
        cols.push({
          key: row.code, module: mod, item_code: item.code, type: item.type,
          description: `${desc} — ${rowLabel}`,
          get: (ctx) => ctx.answers[row.code] ?? "",
        });
      }
      continue;
    }

    if (item.type === "multi") {
      const options = item.options || (item.options_template
        ? item.options_template.map((o) => (typeof o === "string" ? o : promptText(o)))
        : []);
      for (const opt of options) {
        const value = typeof opt === "string" ? opt : opt.value;
        const label = typeof opt === "string" ? opt : opt.label;
        const key = `${item.code}_${slug(value)}`;
        cols.push({
          key, module: mod, item_code: item.code, type: item.type,
          description: `${desc} — ${label} (1 if selected, else 0)`,
          get: (ctx) => {
            const v = ctx.answers[item.code];
            if (!Array.isArray(v)) return 0;
            return v.includes(value) ? 1 : 0;
          },
        });
      }
      if (item.extra_options) {
        for (const opt of item.extra_options) {
          const key = `${item.code}_${slug(opt.value)}`;
          cols.push({
            key, module: mod, item_code: item.code, type: item.type,
            description: `${desc} — ${opt.label} (1 if selected, else 0)`,
            get: (ctx) => {
              const v = ctx.answers[item.code];
              if (!Array.isArray(v)) return 0;
              return v.includes(opt.value) ? 1 : 0;
            },
          });
        }
      }
      continue;
    }

    // numeric, single, slider, text, hidden: one column.
    cols.push({
      key: item.code, module: mod, item_code: item.code, type: item.type, description: desc,
      get: (ctx) => ctx.answers[item.code] ?? "",
    });
  }

  return cols;
}

const BASE_COLUMNS = [
  "response_id", "study", "country", "source", "condition",
  "started_at", "completed_at", "screened_out", "last_item",
  "comprehension_pass", "duration_s", "device",
];

function csvEscape(value) {
  const s = value === null || value === undefined ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!isAuthorized(request, env)) {
    return json(401, { error: "Unauthorized." });
  }

  const url = new URL(request.url);
  const study = url.searchParams.get("study");
  const format = url.searchParams.get("format") || "csv";
  if (!study) {
    return json(400, { error: "study is required." });
  }

  const itemColumns = buildColumns();

  if (format === "codebook") {
    const rows = ["column,item_code,module,type,description"];
    for (const c of BASE_COLUMNS) rows.push([c, "", "", "meta", ""].map(csvEscape).join(","));
    for (const c of itemColumns) rows.push([c.key, c.item_code, c.module, c.type, c.description].map(csvEscape).join(","));
    return new Response(rows.join("\n") + "\n", {
      headers: {
        "content-type": "text/csv; charset=utf-8",
        "content-disposition": `attachment; filename="${study}-codebook.csv"`,
      },
    });
  }

  const { results } = await env.SURVEY_DB
    .prepare("SELECT * FROM responses WHERE study = ? ORDER BY started_at")
    .bind(study)
    .all();

  const wide = results.map((row) => {
    const answers = JSON.parse(row.answers || "{}");
    const timings = JSON.parse(row.timings || "{}");
    const ctx = { answers, timings, row };
    const out = {};
    for (const c of BASE_COLUMNS) out[c] = row[c];
    for (const c of itemColumns) out[c.key] = c.get(ctx);
    return out;
  });

  if (format === "json") {
    return json(200, wide);
  }

  const header = [...BASE_COLUMNS, ...itemColumns.map((c) => c.key)];
  const lines = [header.join(",")];
  for (const row of wide) {
    lines.push(header.map((h) => csvEscape(row[h])).join(","));
  }
  return new Response(lines.join("\n") + "\n", {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="${study}-export.csv"`,
    },
  });
}

// Shared helpers for the survey API Functions. Not routed itself (leading
// underscore), imported by the sibling files in this directory.
import instrument from "../../../survey/instrument.json";

export function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function noContent() {
  return new Response(null, { status: 204 });
}

// Every item code the instrument defines, including grid rows and dynamic
// slot codes, plus the handful of non-item timing/interaction fields the
// instrument itself names (F0_time, F10_click). Mirrors the logic in
// scripts/survey/validate-instrument.mjs so the two stay in sync.
const CONTAINER_ONLY_TYPES = new Set(["grid", "grid_dynamic", "grid_two_step", "slider_grid"]);
const NO_CODE_TYPES = new Set(["info", "info_header", "message"]);

export const VALID_CODES = (() => {
  const codes = new Set(["F0_time", "F10_click"]);
  for (const item of instrument.items) {
    if (!NO_CODE_TYPES.has(item.type) && !CONTAINER_ONLY_TYPES.has(item.type)) {
      codes.add(item.code);
    }
    if (Array.isArray(item.rows)) {
      for (const row of item.rows) {
        if (item.type === "grid_two_step") {
          codes.add(`${row.code}_heard`);
          codes.add(`${row.code}_trust`);
        } else {
          codes.add(row.code);
        }
      }
    }
    if (Array.isArray(item.slot_codes)) {
      for (const c of item.slot_codes) codes.add(c);
    }
    // A slider with an extra "don't know" option stores it under a
    // synthetic companion code (e.g. I3_dk), not the instrument's own code.
    if (item.type === "slider" && Array.isArray(item.extra_options)) {
      codes.add(`${item.code}_dk`);
    }
  }
  return codes;
})();

export function isAuthorized(request, env) {
  const auth = request.headers.get("authorization") || "";
  const token = auth.replace(/^Bearer\s+/i, "");
  return Boolean(env.SURVEY_ADMIN_TOKEN) && token === env.SURVEY_ADMIN_TOKEN;
}

export async function getStudy(env, study) {
  const row = await env.SURVEY_DB
    .prepare("SELECT * FROM studies WHERE study = ?")
    .bind(study)
    .first();
  return row || null;
}

export async function checkRateLimit(env, ip, limit = 60) {
  if (!env.SURVEY_RATE_LIMIT) return true; // fail open if binding not configured yet
  const bucket = Math.floor(Date.now() / 60000);
  const key = `rl:${ip}:${bucket}`;
  const current = Number((await env.SURVEY_RATE_LIMIT.get(key)) || "0");
  if (current >= limit) return false;
  await env.SURVEY_RATE_LIMIT.put(key, String(current + 1), { expirationTtl: 90 });
  return true;
}

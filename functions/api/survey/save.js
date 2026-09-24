// POST /api/survey/save
// Upserts the current state of one in-progress (or just-finished) response.
// Called by survey.js after every screen. Never returns respondent data back;
// on success just 204s so the client keeps its own local state as truth.
import { json, noContent, VALID_CODES, getStudy, checkRateLimit } from "./_lib.js";

const MAX_BODY_BYTES = 200 * 1024;

export async function onRequestPost(context) {
  const { request, env } = context;

  const ip = request.headers.get("cf-connecting-ip") || "unknown";
  if (!(await checkRateLimit(env, ip))) {
    return json(429, { error: "Too many requests. Please slow down." });
  }

  const rawBody = await request.text();
  if (rawBody.length > MAX_BODY_BYTES) {
    return json(413, { error: "Payload too large." });
  }

  let body;
  try {
    body = JSON.parse(rawBody);
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }

  const {
    response_id, study, country, source,
    prolific_pid = null, prolific_session = null,
    condition = null, screened_out = false, last_item = null,
    comprehension_pass = null, device = null,
    answers = {}, timings = {},
  } = body;

  if (!response_id || typeof response_id !== "string" || response_id.length > 100) {
    return json(400, { error: "A valid response_id is required." });
  }
  if (!study || typeof study !== "string") {
    return json(400, { error: "study is required." });
  }
  if (country !== "uk" && country !== "us") {
    return json(400, { error: "country must be 'uk' or 'us'." });
  }
  if (!source || typeof source !== "string") {
    return json(400, { error: "source is required." });
  }
  if (typeof answers !== "object" || answers === null || Array.isArray(answers)) {
    return json(400, { error: "answers must be an object." });
  }
  const badCodes = Object.keys(answers).filter((c) => !VALID_CODES.has(c));
  if (badCodes.length) {
    return json(400, { error: `Unknown item code(s): ${badCodes.join(", ")}` });
  }

  const studyRow = await getStudy(env, study);
  if (!studyRow) {
    return json(400, { error: "Unknown study." });
  }
  if (!studyRow.open) {
    return json(403, { error: "This study is not currently open." });
  }
  if (studyRow.country !== country) {
    return json(400, { error: "country does not match this study." });
  }

  const now = new Date().toISOString();

  await env.SURVEY_DB
    .prepare(
      `INSERT INTO responses
        (response_id, study, country, source, prolific_pid, prolific_session, condition,
         started_at, updated_at, screened_out, last_item, comprehension_pass, device, answers, timings)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(response_id) DO UPDATE SET
         condition = excluded.condition,
         updated_at = excluded.updated_at,
         screened_out = excluded.screened_out,
         last_item = excluded.last_item,
         comprehension_pass = excluded.comprehension_pass,
         device = excluded.device,
         answers = excluded.answers,
         timings = excluded.timings`
    )
    .bind(
      response_id, study, country, source, prolific_pid, prolific_session, condition,
      now, now, screened_out ? 1 : 0, last_item, comprehension_pass, device,
      JSON.stringify(answers), JSON.stringify(timings)
    )
    .run();

  return noContent();
}

export async function onRequestGet() {
  return json(405, { error: "Use POST." });
}

// POST /api/survey/complete
// Marks a response as finished, computes duration, and returns the
// respondent-facing completion URL/code so the client can redirect or show
// a copyable code as a fallback.
import { json, getStudy } from "./_lib.js";

export async function onRequestPost(context) {
  const { request, env } = context;

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }

  const { response_id, comprehension_pass = null } = body;
  if (!response_id || typeof response_id !== "string") {
    return json(400, { error: "A valid response_id is required." });
  }

  const row = await env.SURVEY_DB
    .prepare("SELECT * FROM responses WHERE response_id = ?")
    .bind(response_id)
    .first();
  if (!row) {
    return json(404, { error: "Unknown response_id. Call /api/survey/save first." });
  }

  const now = new Date();
  const startedAt = new Date(row.started_at);
  const durationS = Math.max(0, Math.round((now.getTime() - startedAt.getTime()) / 1000));

  await env.SURVEY_DB
    .prepare(
      `UPDATE responses
       SET completed_at = ?, updated_at = ?, duration_s = ?, comprehension_pass = ?
       WHERE response_id = ?`
    )
    .bind(now.toISOString(), now.toISOString(), durationS, comprehension_pass, response_id)
    .run();

  const study = await getStudy(env, row.study);
  const completionUrl = study && study.prolific_completion_url ? study.prolific_completion_url : null;
  const completionCode = study && study.completion_code ? study.completion_code : null;

  return json(200, { completion_url: completionUrl, completion_code: completionCode, duration_s: durationS });
}

export async function onRequestGet() {
  return json(405, { error: "Use POST." });
}

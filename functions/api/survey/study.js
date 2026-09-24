// GET  /api/survey/study?study=<id>   Public: lets the client find out
//      whether a study is open and get its Prolific redirect URLs before
//      the respondent has answered anything (so it never exposes answers
//      or PIDs).
// POST /api/survey/study              Admin (Bearer SURVEY_ADMIN_TOKEN):
//      create or update a study row.
import { json, noContent, isAuthorized, getStudy } from "./_lib.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const study = url.searchParams.get("study") || "test";

  const row = await getStudy(env, study);
  if (!row) {
    return json(404, { error: "Unknown study." });
  }

  return json(200, {
    study: row.study,
    country: row.country,
    label: row.label,
    open: Boolean(row.open),
    prolific_completion_url: row.prolific_completion_url,
    prolific_screenout_url: row.prolific_screenout_url,
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!isAuthorized(request, env)) {
    return json(401, { error: "Unauthorized." });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }

  const {
    study, country, label,
    prolific_completion_url = null, prolific_screenout_url = null,
    completion_code = null, target_n = null, open = false,
  } = body;

  if (!study || typeof study !== "string") {
    return json(400, { error: "study is required." });
  }
  if (country !== "uk" && country !== "us") {
    return json(400, { error: "country must be 'uk' or 'us'." });
  }
  if (!label || typeof label !== "string") {
    return json(400, { error: "label is required." });
  }

  await env.SURVEY_DB
    .prepare(
      `INSERT INTO studies (study, country, label, prolific_completion_url, prolific_screenout_url, completion_code, target_n, open)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(study) DO UPDATE SET
         country = excluded.country,
         label = excluded.label,
         prolific_completion_url = excluded.prolific_completion_url,
         prolific_screenout_url = excluded.prolific_screenout_url,
         completion_code = excluded.completion_code,
         target_n = excluded.target_n,
         open = excluded.open`
    )
    .bind(study, country, label, prolific_completion_url, prolific_screenout_url, completion_code, target_n, open ? 1 : 0)
    .run();

  return noContent();
}

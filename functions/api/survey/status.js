// GET /api/survey/status?study=<id>
// Admin (Bearer SURVEY_ADMIN_TOKEN): aggregate counts only, for the plain
// dashboard at /survey/status/. Never returns individual answers or PIDs.
import { json, isAuthorized } from "./_lib.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!isAuthorized(request, env)) {
    return json(401, { error: "Unauthorized." });
  }

  const url = new URL(request.url);
  const study = url.searchParams.get("study");
  if (!study) {
    return json(400, { error: "study is required." });
  }

  const db = env.SURVEY_DB;

  const totals = await db
    .prepare(
      `SELECT
         COUNT(*) AS started,
         SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed,
         SUM(CASE WHEN screened_out = 1 THEN 1 ELSE 0 END) AS screened_out,
         SUM(CASE WHEN comprehension_pass = 1 THEN 1 ELSE 0 END) AS comprehension_pass,
         SUM(CASE WHEN comprehension_pass = 0 THEN 1 ELSE 0 END) AS comprehension_fail,
         AVG(duration_s) AS avg_duration_s
       FROM responses WHERE study = ?`
    )
    .bind(study)
    .first();

  const byCondition = await db
    .prepare(
      `SELECT condition, COUNT(*) AS n
       FROM responses WHERE study = ? AND completed_at IS NOT NULL
       GROUP BY condition ORDER BY condition`
    )
    .bind(study)
    .all();

  const byDay = await db
    .prepare(
      `SELECT substr(started_at, 1, 10) AS day, COUNT(*) AS n
       FROM responses WHERE study = ?
       GROUP BY day ORDER BY day`
    )
    .bind(study)
    .all();

  const studyRow = await db.prepare("SELECT * FROM studies WHERE study = ?").bind(study).first();

  return json(200, {
    study,
    target_n: studyRow ? studyRow.target_n : null,
    open: studyRow ? Boolean(studyRow.open) : null,
    started: totals.started || 0,
    completed: totals.completed || 0,
    screened_out: totals.screened_out || 0,
    comprehension_pass: totals.comprehension_pass || 0,
    comprehension_fail: totals.comprehension_fail || 0,
    avg_duration_s: totals.avg_duration_s ? Math.round(totals.avg_duration_s) : null,
    by_condition: byCondition.results || [],
    by_day: byDay.results || [],
  });
}

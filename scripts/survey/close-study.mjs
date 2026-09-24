#!/usr/bin/env node
// Closes a study (open = 0) and strips Prolific identifiers from its rows,
// so no PID/session data lingers once a study is done.
// Usage: node scripts/survey/close-study.mjs <study-id> [--remote]
import { execFileSync } from "node:child_process";

const study = process.argv[2];
const remote = process.argv.includes("--remote") ? "--remote" : "--local";

if (!study) {
  console.error("Usage: node scripts/survey/close-study.mjs <study-id> [--remote]");
  process.exit(1);
}

function d1(sql) {
  const out = execFileSync(
    "npx",
    ["wrangler", "d1", "execute", "SURVEY_DB", remote, "--json", "--command", sql],
    { encoding: "utf8" }
  );
  return JSON.parse(out);
}

const countResult = d1(
  `SELECT COUNT(*) AS n FROM responses WHERE study = '${study}' AND (prolific_pid IS NOT NULL OR prolific_session IS NOT NULL)`
);
const affected = countResult[0]?.results?.[0]?.n ?? 0;

d1(`UPDATE studies SET open = 0 WHERE study = '${study}'`);
d1(`UPDATE responses SET prolific_pid = NULL, prolific_session = NULL WHERE study = '${study}'`);

console.log(`Closed study "${study}" (${remote.replace("--", "")}). Cleared Prolific identifiers from ${affected} row(s).`);

-- Britain Talks AI / America Talks AI survey: D1 schema.
-- Apply with: npx wrangler d1 execute SURVEY_DB --remote --file=migrations/0001_survey.sql

CREATE TABLE IF NOT EXISTS responses (
  response_id TEXT PRIMARY KEY,
  study TEXT NOT NULL,
  country TEXT NOT NULL,
  source TEXT NOT NULL,
  prolific_pid TEXT,
  prolific_session TEXT,
  condition INTEGER,
  started_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  screened_out INTEGER NOT NULL DEFAULT 0,
  last_item TEXT,
  comprehension_pass INTEGER,
  duration_s INTEGER,
  device TEXT,
  answers TEXT NOT NULL DEFAULT '{}',
  timings TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_responses_study_completed
  ON responses (study, completed_at);

CREATE TABLE IF NOT EXISTS studies (
  study TEXT PRIMARY KEY,
  country TEXT NOT NULL,
  label TEXT NOT NULL,
  prolific_completion_url TEXT,
  prolific_screenout_url TEXT,
  completion_code TEXT,
  target_n INTEGER,
  open INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO studies (study, country, label, prolific_completion_url, prolific_screenout_url, completion_code, target_n, open)
VALUES
  ('test', 'uk', 'Test study (UK instrument, always open)', NULL, NULL, 'TEST0000', NULL, 1),
  ('uk-pretest-01', 'uk', 'UK pretest 1', NULL, NULL, NULL, 100, 0),
  ('uk-pilot-01', 'uk', 'UK pilot 1', NULL, NULL, NULL, 2000, 0);

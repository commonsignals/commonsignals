// Data layer for the MCP server at /mcp.
//
// Everything except comment search comes from the site's own published files,
// read from the deployed static assets at request time: /data/studies/index.json,
// each study's study.json and codebook.json, the counts in /data/mcp/<slug>.json
// (written by scripts/data-export.py build), /llms.txt and the pages' markdown.
// Nothing is bundled, so recodes, corrections, takedowns and new studies reach the
// server with the next deploy. Parsed files are cached per isolate, keyed by path
// and ETag; all of them are public.
//
// Comment search reads the D1 copy of each comments.csv (binding MCP_DB, loaded by
// scripts/mcp/load-d1.py), because parsing the largest study takes far longer than
// the Workers Free plan's 10 ms of CPU. Each copy records the SHA-256 of the
// comments.csv it was loaded from, and search refuses a study whose copy no longer
// matches the published file, so a corrected or removed comment is never quoted.

export const SITE = "https://commonsignals.org";
const RESPONSE_CAP = 60_000; // bytes of a whole search_comments result
const PAGE_CAP = 200_000; // bytes of a whole page's markdown
// Characters of markdown in one get_page response. Claude Code shows a tool result
// of about 32 KB inline but saves one of 51 KB to a file the model may not be able
// to open, so long pages come in parts, sized to leave room for the figure list.
const PAGE_PART = 22_000;
const FIGURE_LIST_CAP = 50;
const SEARCH_LIMIT = 25;
const RULE_2 =
  "These are people who chose to comment on particular posts, not a sample of the public, of a country or of any demographic, so these figures are not public opinion and must not be offered as an answer about what the public thinks.";
const QUOTE_RULE =
  "Quote each comment whole and character for character, curly quotes and apostrophes included, in its own block quote, with its id written as a link to its url, as in [id](url). Every comment you name, quoted or not and however short, carries that linked id, a reply_to text included. To name a comment without quoting it, as a spare or an aside, give its linked id and say what it argues in your own words, with none of its text in quotation marks. Never quote part of a comment, mark cuts in one, straighten its quotes or escape its characters; if a comment is too long to quote whole, pick another. Comment text belongs to its authors; the coding and compilation are licensed CC BY 4.0.";
const NO_MESSENGERS =
  "These tools hold no messenger data: the messenger map is not available through them, so they cannot name, list, rank or suggest messengers. Asked who is trusted, whom to approach or who should front something, say first that these tools hold no messenger data.";
const READING =
  "Asked where to start reading, recommend only what the reading list page lists, and nothing from elsewhere.";
const NO_ADVICE =
  "Common Signals describes how messages were received, takes no side and recommends no framing. Its hypotheses are untested, and differences between studies are not effects of the message, because audience, platform and claim all differ at once. The studies cannot tell anyone what to lead with: any advice is yours or another source's, so label it as such and never present it as what the data shows or what Common Signals recommends. If you offer a view of your own, keep it even-handed: say what each kind of message gained and lost in these threads, and do not steer towards either.";
const PAGE_BASES =
  "Rule 1 applies to every figure you take from this page, rough ones and bounds such as 'under 1%' or 'about a third' included: give the number of comments it is a share of, as in '12% of 322 comments'. A share of likes needs that number too, and a figure covering several studies needs each study's own count. Most figures on these pages are written without one, and figures_without_counts lists those in this part. Leave those out, or replace one with the figure get_study or search_comments gives, with its count. A figure from outside Common Signals needs its named source instead.";
const RECORD_BASES =
  "The record's capture method, notes, coding check and changelog quote some figures without the number they are a share of, often from an earlier version or the published article, and figures_without_counts lists them. Leave those out, or use the matching figure under figures, which carries its base.";
const PUBLIC_NOTE =
  "Asked what the public, a country or any group thinks, say these studies cannot answer it and give no figure from them, not even to illustrate what they hold.";
const OWN_LIST =
  "This study's own list, not shared with other studies: report it for this study alone, never beside or against another study's figure, even one with the same label.";

// A refusal is an expected answer, such as an unknown slug, returned to the
// client as a tool error with the valid options attached.
export class Refusal extends Error {
  constructor(message, details = {}) {
    super(message);
    this.details = details;
  }
}

const encoder = new TextEncoder();
const bytes = (text) => encoder.encode(text).length;
const pct = (n, base) => (base ? Math.round((1000 * n) / base) / 10 : null);
export const explorerUrl = (slug) => `${SITE}/data/${encodeURIComponent(slug)}/`;
export const commentUrl = (slug, id) => `${SITE}/data/${encodeURIComponent(slug)}/c/${encodeURIComponent(id)}`;

export function toolResult(result) {
  return { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result };
}

// Bytes a value adds to a tool result, which carries its JSON twice: once as
// structured content and once escaped inside the text copy.
function resultSize(value) {
  const json = JSON.stringify(value);
  return bytes(json) + bytes(JSON.stringify(json)) - 2;
}

// Published files

// A cached file is checked against its ETag at most once a minute, so a busy isolate
// is not re-asking for the same files on every request; a deploy's new files reach
// it within a minute. kind keeps different parses of one file apart.
const REVALIDATE_MS = 60_000;
const cache = new Map();

async function asset(ctx, path, parse, kind = "") {
  const key = kind ? `${path}#${kind}` : path;
  const hit = cache.get(key);
  const now = Date.now();
  if (hit && now - hit.checked < REVALIDATE_MS) return hit.value;
  const headers = hit ? { "if-none-match": hit.etag } : {};
  const res = await ctx.env.ASSETS.fetch(new Request(new URL(path, ctx.origin), { headers }));
  if (res.status === 304 && hit) {
    hit.checked = now;
    return hit.value;
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`static asset answered ${res.status}`);
  const value = parse(await res.text());
  const etag = res.headers.get("etag");
  if (etag) cache.set(key, { etag, value, checked: now });
  else cache.delete(key);
  return value;
}
const asJson = (text) => JSON.parse(text);
const asText = (text) => text;

async function studyIndex(ctx) {
  const index = await asset(ctx, "/data/studies/index.json", asJson);
  if (!index) throw new Error("index.json is missing");
  return index.studies;
}

async function loadStudy(ctx, slug, index) {
  const studies = index || (await studyIndex(ctx));
  if (!studies.some((s) => s.slug === slug)) {
    throw new Refusal(`Unknown study slug: ${JSON.stringify(slug)}.`, { valid_slugs: studies.map((s) => s.slug) });
  }
  const folder = `/data/studies/${encodeURIComponent(slug)}/`;
  const [study, codebook] = await Promise.all([
    asset(ctx, folder + "study.json", asJson),
    asset(ctx, folder + "codebook.json", asJson),
  ]);
  if (!study || !codebook) throw new Error("a study file is missing");
  return { study, codebook };
}

async function figures(ctx, slug) {
  const found = await asset(ctx, `/data/mcp/${encodeURIComponent(slug)}.json`, asJson);
  if (!found) throw new Error("the figures file is missing");
  return found;
}

function markdownPath(url) {
  const path = new URL(url, SITE).pathname;
  return path.endsWith("/") ? path + "index.html.md" : path + ".md";
}

function frontMatter(markdown, key) {
  const block = /^---\n([\s\S]*?)\n---\n/.exec(markdown);
  const line = block && block[1].split("\n").find((l) => l.startsWith(key + ": "));
  if (!line) return null;
  const value = line.slice(key.length + 2);
  return value.startsWith('"') && value.endsWith('"') ? value.slice(1, -1).replace(/\\(["\\])/g, "$1") : value;
}

// The citation wording the site already uses: the "Cite as" line of the study's
// article, carried into the front matter of its markdown version.
async function citeLine(ctx, study) {
  const data = `Data: ${study.title}, version ${study.version}, ${explorerUrl(study.slug)}`;
  if (study.article_url) {
    const cite = await asset(ctx, markdownPath(study.article_url), (text) => frontMatter(text, "cite"), "cite");
    if (cite) return `${cite} ${data}`;
  }
  return `Common Signals, '${study.title}'. ${data}`;
}

// What each response says about the study behind its figures

function reliability(study) {
  if (study.reliability) return { status: "published", reliability: study.reliability };
  const check = study.spot_check || {};
  const by = check.checked_by ? `, checked by ${check.checked_by}` : "";
  const when = check.date ? `, ${check.date}` : "";
  return {
    status: "no published grade",
    summary: `No reliability grade is published for this study. Its coding check: ${check.agreed} of ${check.sample} agreed${by}${when}.`,
    coding_check: check,
  };
}

function caveats(study) {
  const counts = study.counts || {};
  const key = Object.keys(counts).find((k) => k.startsWith("on_page") && counts[k] != null);
  const when = key === "on_page" ? "at capture" : key ? key.slice("on_page_".length).replace(/_/g, " ") : "";
  const coverage = key
    ? `Coverage: ${counts.retrieved} comments retrieved, against ${counts[key]} shown on the page ${when}.`
    : `Coverage: ${counts.retrieved} comments retrieved; how many the platform showed was not recorded.`;
  const status = reliability(study);
  return [
    RULE_2,
    `Capture method: ${study.capture_method}`,
    coverage,
    `Notes: ${study.notes}`,
    `Reliability: ${status.summary || "a reliability grade is published; see reliability."}`,
  ];
}

function studyHeader(study) {
  return { slug: study.slug, title: study.title, explorer_url: explorerUrl(study.slug) };
}

// Figures from /data/mcp/<slug>.json

function describeDimension(dim, block) {
  const counts = block.counts[dim.key] || {};
  const head = { key: dim.key, label: dim.label, kind: dim.kind, shared: Boolean(dim.shared), base: block.base };
  if (!dim.shared) head.note = OWN_LIST;
  if (dim.kind === "flag") {
    const n = counts.true || 0;
    return { ...head, n_true: n, pct_true: pct(n, block.base) };
  }
  return {
    ...head,
    values: dim.values.map((v) => ({ value: v.value, label: v.label, n: counts[v.value] || 0, pct: pct(counts[v.value] || 0, block.base) })),
  };
}

function describeStance(codebook, positioned, block) {
  const dim = codebook.dimensions.find((d) => d.key === "stance");
  if (!dim) return null;
  const counts = block.counts.stance || {};
  const value = (v, base) => ({ value: v.value, label: v.label, n: counts[v.value] || 0, pct: pct(counts[v.value] || 0, base) });
  return {
    all_coded: { base: block.base, base_label: "all coded comments", values: dim.values.map((v) => value(v, block.base)) },
    clear_position: {
      base: block.clear_position_base,
      base_label: `comments taking a clear position (stance ${positioned.join(", ")})`,
      values: dim.values.filter((v) => positioned.includes(v.value)).map((v) => value(v, block.clear_position_base)),
    },
  };
}

function describeBlock(codebook, positioned, block) {
  const dims = codebook.dimensions.filter((d) => (d.kind === "single" || d.kind === "flag") && d.key !== "stance");
  return {
    base: block.base,
    clear_position_base: block.clear_position_base,
    stance: describeStance(codebook, positioned, block),
    dimensions: dims.map((d) => describeDimension(d, block)),
  };
}

// Tools

export async function listStudies(ctx) {
  const index = await studyIndex(ctx);
  const studies = await Promise.all(
    index.map(async ({ slug }) => {
      const { study } = await loadStudy(ctx, slug, index);
      const status = reliability(study);
      return {
        ...studyHeader(study),
        platform: study.platform,
        artefact_title: study.artefact_title,
        artefact_url: study.artefact_url,
        capture_dates: study.capture_dates,
        coded: study.counts.coded,
        clear_position_base: study.counts.clear_position_base,
        central_claim: study.central_claim,
        version: study.version,
        article_url: study.article_url,
        reliability_status: status.summary || "A reliability grade is published; see get_study.",
      };
    }),
  );
  return { note: RULE_2, public_note: PUBLIC_NOTE, messengers: NO_MESSENGERS, studies };
}

export async function getStudy(ctx, slug, splitBy) {
  const { study, codebook } = await loadStudy(ctx, slug);
  const fig = await figures(ctx, slug);
  const groupDims = codebook.dimensions.filter((d) => d.kind === "group");
  let split = null;
  if (splitBy != null && splitBy !== "") {
    const group = groupDims.find((d) => d.key === splitBy);
    if (!group) {
      throw new Refusal(
        groupDims.length
          ? `split_by must be one of this study's group dimensions, and ${JSON.stringify(splitBy)} is not.`
          : `${slug} has no group dimensions, so its figures cannot be split.`,
        { valid_split_by: groupDims.map((d) => d.key) },
      );
    }
    const labels = Object.fromEntries((group.values || []).map((v) => [v.value, v.label]));
    split = {
      dimension: group.key,
      label: group.label,
      groups: (fig.groups[group.key] || []).map((block) => ({
        value: block.value,
        label: labels[block.value] ?? block.value,
        ...describeBlock(codebook, fig.clear_position_values, block),
      })),
    };
  }
  const uncoded = fig.all.uncoded
    ? ` ${fig.all.uncoded} of them were not coded in substance (empty stubs or comments excluded before coding) and carry stance na.`
    : "";
  return {
    ...studyHeader(study),
    study: {
      platform: study.platform,
      series: study.series,
      artefact_title: study.artefact_title,
      artefact_url: study.artefact_url,
      artefact_published: study.artefact_published,
      central_claim: study.central_claim,
      what_each_stance_means: codebook.stance_note,
      capture_dates: study.capture_dates,
      capture_method: study.capture_method,
      counts: study.counts,
      coding_check: study.spot_check,
      reliability: study.reliability ?? null,
      coders: study.coders,
      version: study.version,
      changelog: study.changelog,
      licence: study.licence,
      notes: study.notes,
      article_url: study.article_url,
    },
    base_note: `Each figure is a share of the base beside it. The study has ${study.counts.coded} coded comments.${uncoded}`,
    record_note: RECORD_BASES,
    figures_without_counts: figuresWithoutCounts(
      [study.capture_method, study.notes, study.spot_check?.note, ...(study.changelog || []).map((c) => c.note)].filter(Boolean).join("\n"),
    ),
    advice_note: NO_ADVICE,
    public_note: PUBLIC_NOTE,
    figures: describeBlock(codebook, fig.clear_position_values, fig.all),
    split_by: split,
    reliability: reliability(study),
    caveats: caveats(study),
    cite: await citeLine(ctx, study),
  };
}

export async function getCodebook(ctx, slug) {
  const { study, codebook } = await loadStudy(ctx, slug);
  return {
    ...studyHeader(study),
    note: `Frame, and any other dimension not marked shared, is this study's own list: report its figures for this study alone, never beside or against another study's, even under the same label.`,
    codebook,
    caveats: caveats(study),
    cite: await citeLine(ctx, study),
    licence: study.licence,
  };
}

export async function compareStudies(ctx, dimension) {
  const index = await studyIndex(ctx);
  const loaded = await Promise.all(index.map(({ slug }) => loadStudy(ctx, slug, index)));
  const sharedSets = loaded.map(({ codebook }) =>
    new Set(codebook.dimensions.filter((d) => d.shared && (d.kind === "single" || d.kind === "flag")).map((d) => d.key)),
  );
  const shared = [...sharedSets[0]].filter((key) => sharedSets.every((set) => set.has(key)));
  if (!shared.includes(dimension)) {
    throw new Refusal(
      `${JSON.stringify(dimension)} cannot be compared across studies: compare_studies accepts only dimensions that every study's codebook marks as shared. Each study codes frames with its own list, drafted from that post and its own comments, so a frame in one study cannot be compared with a frame in another, even when the labels match.`,
      { shared_dimensions: shared },
    );
  }
  const studies = await Promise.all(
    loaded.map(async ({ study, codebook }) => {
      const fig = await figures(ctx, study.slug);
      const dim = codebook.dimensions.find((d) => d.key === dimension);
      const entry = { ...studyHeader(study), platform: study.platform, ...describeDimension(dim, fig.all) };
      if (dimension === "stance") entry.stance = describeStance(codebook, fig.clear_position_values, fig.all);
      const grade = study.reliability?.dimensions?.[dimension];
      if (grade) entry.reliability_grade = grade;
      entry.caveats = caveats(study);
      entry.cite = await citeLine(ctx, study);
      return entry;
    }),
  );
  const notes = [
    "Each entry is on its own study's base. Report each study's figure with its base; do not add studies together or average them into one percentage.",
    NO_ADVICE,
    PUBLIC_NOTE,
  ];
  if (studies.some((s) => /direction only/i.test(JSON.stringify(s.reliability_grade ?? "")))) {
    notes.push("This dimension is graded Direction only in at least one study, so compare the direction of differences, not their levels.");
  }
  const label = loaded[0].codebook.dimensions.find((d) => d.key === dimension).label;
  return { dimension, label, notes, studies };
}

export async function searchComments(ctx, { slug, filters, text, limit = 10, offset = 0 }) {
  const { study, codebook } = await loadStudy(ctx, slug);
  const db = ctx.env.MCP_DB;
  if (!db) throw new Refusal("Comment search is not connected on this deployment yet: the D1 copy of the comments is missing.");
  const fig = await figures(ctx, slug);
  const meta = await db.prepare("SELECT table_name, comments_sha256, columns FROM mcp_studies WHERE slug = ?").bind(slug).first();
  if (!meta) throw new Refusal(`The searchable copy of ${slug} has not been loaded yet.`);
  if (meta.comments_sha256 !== fig.comments_sha256) {
    throw new Refusal(
      `The searchable copy of ${slug} is out of date with its published comments.csv, so its comments cannot be quoted until it is reloaded. get_study still gives current figures.`,
    );
  }
  const table = meta.table_name;
  const columns = JSON.parse(meta.columns);
  if (!/^c_[a-z0-9_]+$/.test(table) || !columns.every((c) => /^[a-z][a-z0-9_]*$/.test(c))) throw new Error("unexpected table layout");

  const dims = Object.fromEntries(codebook.dimensions.filter((d) => ["single", "flag", "group"].includes(d.kind)).map((d) => [d.key, d]));
  const where = [];
  const params = [];
  const applied = {};
  for (const [key, raw] of Object.entries(filters || {})) {
    const dim = dims[key];
    if (!dim || !columns.includes(key)) {
      throw new Refusal(`Unknown dimension for ${slug}: ${JSON.stringify(key)}.`, { valid_dimensions: Object.keys(dims).filter((k) => columns.includes(k)) });
    }
    const allowed = dim.kind === "flag" ? ["true", "false"] : dim.values.map((v) => v.value);
    const values = (Array.isArray(raw) ? raw : [raw]).map((v) => (typeof v === "boolean" ? String(v) : v));
    const bad = values.find((v) => !allowed.includes(v));
    if (!values.length || bad !== undefined) {
      throw new Refusal(`Unknown value for ${key} in ${slug}: ${JSON.stringify(bad ?? null)}.`, { dimension: key, valid_values: allowed });
    }
    where.push(`"${key}" IN (${values.map(() => "?").join(", ")})`);
    params.push(...values);
    applied[key] = values;
  }
  if (typeof text === "string" && text !== "") {
    where.push("instr(text_lc, ?) > 0");
    params.push(text.toLowerCase());
  }
  const filter = where.length ? ` WHERE ${where.join(" AND ")}` : "";
  const take = Math.min(Math.max(limit, 1), SEARCH_LIMIT);
  const cols = ["n", "id", "parent_n", "parent_id", "published_at", "published_at_precision", "likes", "text", ...columns.map((c) => `"${c}"`)];
  const { results } = await db
    .prepare(`SELECT ${cols.join(", ")}, COUNT(*) OVER () AS n_matched FROM "${table}"${filter} ORDER BY n LIMIT ? OFFSET ?`)
    .bind(...params, take, offset)
    .all();
  let matched = results.length ? results[0].n_matched : offset === 0 ? 0 : null;
  if (matched === null) {
    matched = (await db.prepare(`SELECT COUNT(*) AS n FROM "${table}"${filter}`).bind(...params).first()).n;
  }

  const parentRows = [...new Set(results.map((r) => r.parent_n).filter((n) => n != null))];
  const parents = new Map();
  if (parentRows.length) {
    const found = await db
      .prepare(`SELECT n, text FROM "${table}" WHERE n IN (${parentRows.map(() => "?").join(", ")})`)
      .bind(...parentRows)
      .all();
    for (const p of found.results) parents.set(p.n, p.text);
  }
  const rows = results.map((r) => {
    const row = {
      id: r.id,
      url: commentUrl(slug, r.id),
      text: r.text,
      codes: Object.fromEntries(columns.map((c) => [c, r[c]])),
      likes: r.likes === "" || r.likes == null ? null : Number(r.likes),
      published_at: r.published_at || null,
    };
    if (r.published_at_precision) row.published_at_precision = r.published_at_precision;
    if (r.parent_id) row.reply_to = { id: r.parent_id, url: commentUrl(slug, r.parent_id), text: parents.get(r.parent_n) ?? null };
    return row;
  });

  const response = {
    ...studyHeader(study),
    n_matched: matched,
    coded: study.counts.coded,
    base_note: `n_matched is a count of this study's ${study.counts.coded} coded comments.`,
    filters: applied,
    text: typeof text === "string" && text !== "" ? text : null,
    offset,
    returned: rows.length,
    truncated: false,
    next_offset: null,
    quoting: QUOTE_RULE,
    rows,
    caveats: caveats(study),
    cite: await citeLine(ctx, study),
    licence: study.licence,
  };
  // Keep the whole result under the cap: measure each row once and keep as many
  // rows as fit.
  let budget = RESPONSE_CAP - resultSize({ ...response, rows: [] }) - 200;
  let fit = 0;
  for (const row of rows) {
    const size = resultSize(row) + 2;
    if (size > budget) break;
    budget -= size;
    fit += 1;
  }
  if (fit === 0 && rows.length && rows[0].reply_to) {
    rows[0].reply_to.text = null;
    if (resultSize(rows[0]) + 2 <= budget) fit = 1;
  }
  if (fit === 0 && rows.length) {
    throw new Refusal("That comment is too long to return here. Open it on its page instead.", { url: rows[0].url });
  }
  rows.length = fit;
  response.returned = rows.length;
  response.truncated = offset + rows.length < matched;
  response.next_offset = response.truncated ? offset + rows.length : null;
  return response;
}

// Pages listed in /llms.txt

function pageUrlFor(markdownUrl) {
  if (markdownUrl.endsWith("/index.html.md")) return markdownUrl.slice(0, -"index.html.md".length);
  if (/\/README\.md$/.test(markdownUrl)) return markdownUrl;
  return markdownUrl.endsWith(".md") ? markdownUrl.slice(0, -3) : markdownUrl;
}

async function llmsEntries(ctx) {
  const text = await asset(ctx, "/llms.txt", asText);
  if (!text) throw new Error("llms.txt is missing");
  const entries = [];
  let section = null;
  for (const line of text.split("\n")) {
    const heading = /^## (.+)$/.exec(line);
    if (heading) {
      section = heading[1].trim();
      continue;
    }
    const item = /^- \[(.+?)\]\((https?:\/\/[^\s)]+)\)(?::\s*(.*))?$/.exec(line);
    if (item && section) {
      const url = item[2];
      const markdown = url.endsWith(".md") ? url : null;
      entries.push({ section, title: item[1], page_url: markdown ? pageUrlFor(markdown) : url, markdown_url: markdown, description: (item[3] || "").trim() });
    }
  }
  return entries;
}

export async function listPages(ctx) {
  const pages = await llmsEntries(ctx);
  return { source: `${SITE}/llms.txt`, notes: [READING, NO_MESSENGERS], pages };
}

function toMarkdownUrl(input) {
  let url;
  try {
    url = new URL(input, SITE + "/");
  } catch {
    return null;
  }
  if (!["commonsignals.org", "www.commonsignals.org"].includes(url.hostname)) return null;
  let path = url.pathname;
  if (path.endsWith(".md")) return SITE + path;
  if (path.endsWith("/")) return SITE + path + "index.html.md";
  if (path.endsWith(".html")) path = path.slice(0, -5);
  return SITE + path + ".md";
}

// A page's markdown in parts of at most PAGE_PART characters, cut at line breaks,
// after capping the whole page at PAGE_CAP bytes.
function pageParts(markdown) {
  let truncated = false;
  if (bytes(markdown) > PAGE_CAP) {
    const cut = new TextDecoder().decode(encoder.encode(markdown).slice(0, PAGE_CAP));
    markdown = cut.slice(0, cut.lastIndexOf("\n") + 1);
    truncated = true;
  }
  const parts = [];
  let current = "";
  for (const line of markdown.split(/(?<=\n)/)) {
    if (current && current.length + line.length > PAGE_PART) {
      parts.push(current);
      current = "";
    }
    // A line longer than a whole part is cut into part-sized pieces.
    let rest = line;
    while (current.length + rest.length > PAGE_PART) {
      parts.push(current + rest.slice(0, PAGE_PART - current.length));
      rest = rest.slice(PAGE_PART - current.length);
      current = "";
    }
    current += rest;
  }
  if (current || !parts.length) parts.push(current);
  return { parts, truncated };
}

// The shares a text gives with no count near them, such as "12% of its comments" or
// "a fifth of all likes". Articles and study records often write figures that way,
// but rule 1 needs the number, so get_page and get_study list them for the reader
// to leave out or look up. It is a heuristic that errs towards listing: a share is
// listed unless a count such as "270 of 385", "317/347" or "2,075 comments" stands
// within a short distance of it in the same sentence. One excerpt per sentence.
const SHARE = /\b\d+(?:\.\d+)?%|\b(?:half|a (?:third|quarter|fifth|tenth)|(?:one|two|three|four|five|six|seven|eight|nine) in (?:three|four|five|six|seven|eight|nine|ten|twenty))\b/gi;
const COUNT =
  /\b\d[\d,]*\s+(?:of|out of)\s+(?:the\s+|all\s+|its\s+|those\s+)?\d[\d,]*\b|\b(?:of|from)\s+(?:the\s+|all\s+)?\d[\d,]{2,}\b|\bn\s*=\s*\d|\b\d[\d,]*\s*\/\s*\d[\d,]*\b|\b\d[\d,]{2,}\s+(?:coded\s+)?(?:comments|replies|rows)\b/i;

function figuresWithoutCounts(text) {
  const plain = text.replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1");
  const found = [];
  for (const raw of plain.split(/\n+|(?<=[.!?])\s+/)) {
    const sentence = raw.replace(/[*_`#>|]+/g, " ").replace(/\s+/g, " ").trim();
    for (const m of sentence.matchAll(SHARE)) {
      if (COUNT.test(sentence.slice(Math.max(0, m.index - 120), m.index + m[0].length + 60))) continue;
      const start = Math.max(0, m.index - 50);
      const end = Math.min(sentence.length, m.index + m[0].length + 50);
      found.push(`${start > 0 ? "..." : ""}${sentence.slice(start, end)}${end < sentence.length ? "..." : ""}`);
      break;
    }
    if (found.length === FIGURE_LIST_CAP) break;
  }
  return found;
}

export async function getPage(ctx, url, part = 1) {
  const entries = await llmsEntries(ctx);
  const markdownUrl = typeof url === "string" ? toMarkdownUrl(url.trim()) : null;
  const entry = markdownUrl && entries.find((e) => e.markdown_url === markdownUrl);
  if (!entry) {
    throw new Refusal("That URL is not one of the pages listed in /llms.txt, so get_page will not return it. Use list_pages to see the pages it can return.");
  }
  const markdown = await asset(ctx, new URL(markdownUrl).pathname, asText);
  if (markdown == null) throw new Error("a listed page is missing");
  const { parts, truncated } = pageParts(markdown);
  if (part > parts.length) throw new Refusal(`This page has ${parts.length} part${parts.length === 1 ? "" : "s"}.`, { parts: parts.length });
  return {
    url: entry.page_url,
    markdown_url: markdownUrl,
    title: entry.title,
    section: entry.section,
    cite: frontMatter(markdown, "cite"),
    notes: [PAGE_BASES, NO_ADVICE, READING, NO_MESSENGERS],
    figures_without_counts: figuresWithoutCounts(parts[part - 1]),
    part,
    parts: parts.length,
    next_part: part < parts.length ? part + 1 : null,
    truncated,
    markdown: parts[part - 1],
  };
}

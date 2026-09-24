#!/usr/bin/env node
// Checks that every item code named in the instrument markdown appears in
// survey/instrument.json, and vice versa. Run: node scripts/survey/validate-instrument.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const mdPath = path.join(root, "_incoming/survey/instrument-v0.1.md");
const jsonPath = path.join(root, "survey/instrument.json");

const md = readFileSync(mdPath, "utf8");
const instrument = JSON.parse(readFileSync(jsonPath, "utf8"));

// --- Codes named in the markdown -------------------------------------------------
// Bracketed references look like [A1], [C1_01 to C1_20], [E3_a, E3_b, E3_c],
// [F0], [F0_time], [F4_01 to F4_06]. Table "Code" columns also list single
// codes like C1_01. We collect both.
const mdCodes = new Set();

function addRangeOrList(inner) {
  // "C1_01 to C1_20" -> expand; "E3_a, E3_b, E3_c" -> split; single code as-is.
  const rangeMatch = inner.match(/^([A-Z]+\d*)_(\d+)\s+to\s+([A-Z]+\d*)_(\d+)$/);
  if (rangeMatch) {
    const [, prefix1, start, prefix2, end] = rangeMatch;
    if (prefix1 !== prefix2) return;
    const width = start.length;
    for (let i = Number(start); i <= Number(end); i++) {
      mdCodes.add(`${prefix1}_${String(i).padStart(width, "0")}`);
    }
    return;
  }
  if (inner.includes(",")) {
    inner.split(",").forEach((part) => {
      const c = part.trim();
      if (/^[A-Za-z][A-Za-z0-9_]*$/.test(c)) mdCodes.add(c);
    });
    return;
  }
  if (/^[A-Za-z][A-Za-z0-9_]*$/.test(inner.trim())) mdCodes.add(inner.trim());
}

// [ ... ] bracket contents that look like code references (skip long prose notes).
const bracketRe = /\[([^\[\]]+)\]/g;
let m;
while ((m = bracketRe.exec(md))) {
  const inner = m[1].trim();
  // Only treat as a code reference if it's short and code-shaped (letters,
  // digits, underscores, "to", commas, spaces) -- excludes prose design notes,
  // which contain lowercase sentences, periods, etc.
  if (inner.length <= 40 && /^[A-Za-z0-9_,\s]+$/.test(inner) && /[A-Z]/.test(inner)) {
    addRangeOrList(inner);
  }
}

// Table "Code" column entries (pipe tables with a leading `| C1_01 |` etc.)
const tableCodeRe = /^\|\s*([A-Z][A-Za-z0-9]*_\d{2}|[A-Z][A-Za-z0-9]*)\s*\|/gm;
while ((m = tableCodeRe.exec(md))) {
  mdCodes.add(m[1]);
}

// Codes that are meta/labels rather than real item codes, or that the
// instrument itself marks as not-yet-fielded/open design points.
const IGNORE = new Set([
  "UK", "US", "Code",
  // Design-summary table header cells, picked up by the table-row regex
  // because they start with a capital letter like a real code would.
  "Element", "Specification", "Condition", "Demographics", "Ethics",
  "Length", "Mode", "Outputs", "Population", "Sample", "Segmentation",
  "Message", "Text", "Words", "Grade", "Sources", "Statement", "Row",
  "Issue", "Category", "Dimension", "Source",
]);
for (const c of IGNORE) mdCodes.delete(c);

// A few codes are named only inside long prose design notes (whole note
// wrapped in one bracket), so the short-bracket scan above can't see them.
// They are still real respondent-data fields the markdown commits to.
for (const c of ["F10_click"]) {
  if (md.includes(c)) mdCodes.add(c);
}

// --- Codes defined in instrument.json --------------------------------------------
const jsonCodes = new Set();
// Grid-family containers are never bracketed alone in the markdown (only
// "[C1_01 to C1_20]" style row ranges appear), so only their row/slot codes
// need to be matched. Structural text screens (info/info_header) have no
// item code of their own in the source at all.
const CONTAINER_ONLY_TYPES = new Set(["grid", "grid_dynamic", "grid_two_step", "slider_grid"]);
const NO_CODE_TYPES = new Set(["info", "info_header", "message"]);
function collect(item) {
  if (!NO_CODE_TYPES.has(item.type) && !CONTAINER_ONLY_TYPES.has(item.type)) {
    jsonCodes.add(item.code);
  }
  if (Array.isArray(item.rows)) {
    for (const row of item.rows) jsonCodes.add(row.code);
  }
  if (Array.isArray(item.slot_codes)) {
    for (const c of item.slot_codes) jsonCodes.add(c);
  }
}
for (const item of instrument.items) collect(item);
// F0_time is a recorded timing field, not a respondent-facing item, named
// directly in the markdown as its own bracket ([F0_time]).
jsonCodes.add("F0_time");
jsonCodes.add("F10_click");

const missingFromJson = [...mdCodes].filter((c) => !jsonCodes.has(c)).sort();
const extraInJson = [...jsonCodes].filter((c) => !mdCodes.has(c)).sort();

if (missingFromJson.length || extraInJson.length) {
  console.error("Instrument validation FAILED\n");
  if (missingFromJson.length) {
    console.error(`In markdown but missing from instrument.json (${missingFromJson.length}):`);
    console.error("  " + missingFromJson.join(", "));
  }
  if (extraInJson.length) {
    console.error(`In instrument.json but not named in markdown (${extraInJson.length}):`);
    console.error("  " + extraInJson.join(", "));
  }
  process.exit(1);
}

console.log(`Instrument validation passed: ${mdCodes.size} codes matched in both directions.`);

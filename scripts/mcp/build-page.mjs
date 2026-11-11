// Writes the parts of /data/ai-tools/ that come from the MCP server itself, so the
// page cannot drift from the server, and the server's version:
//   - the rules: INSTRUCTIONS from functions/mcp/_server.js, word for word;
//   - the tool list: each tool's name, description and parameters from TOOLS;
//   - functions/mcp/_version.js: the server's version, which is the build date.
//
// Run it after changing the server's instructions or tools, from the repo root
// after npm install: node scripts/mcp/build-page.mjs
// It only touches the regions between the build-mcp-page markers, and running it
// twice on the same day changes nothing.
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { INSTRUCTIONS, TOOLS } from "../../functions/mcp/_server.js";

const root = (path) => fileURLToPath(new URL(`../../${path}`, import.meta.url));
const PAGE = root("data/ai-tools/index.html");
const VERSION_FILE = root("functions/mcp/_version.js");

const escape = (text) => String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function rulesHtml() {
  const [intro, ...rest] = INSTRUCTIONS.split("\n\n");
  const rules = rest.join("\n").split("\n").filter(Boolean);
  const items = rules.map((rule) => {
    const m = /^(\d+)\. (.*)$/.exec(rule);
    if (!m) throw new Error(`a rule does not start with its number: ${rule}`);
    return `        <li>${escape(m[2])}</li>`;
  });
  return [`      <p>${escape(intro)}</p>`, "      <ol>", ...items, "      </ol>"].join("\n");
}

function typeLabel(schema) {
  if (schema.anyOf) return schema.anyOf.map(typeLabel).join(" or ");
  if (schema.type === "integer") {
    // zod gives every whole number a maximum of Number.MAX_SAFE_INTEGER, which is no real limit.
    const { minimum: min } = schema;
    const max = schema.maximum === Number.MAX_SAFE_INTEGER ? null : schema.maximum;
    if (min != null && max != null) return `whole number, ${min} to ${max}`;
    if (min != null) return `whole number, ${min} or more`;
    return "whole number";
  }
  if (schema.type === "object") return "object";
  if (schema.type === "array") return `list of ${typeLabel(schema.items || {})}`;
  return schema.type || "any";
}

function toolsHtml() {
  const out = [];
  for (const tool of TOOLS) {
    const schema = z.toJSONSchema(z.object(tool.inputSchema));
    const required = new Set(schema.required || []);
    out.push(`      <h3 id="tool-${tool.name.replace(/_/g, "-")}"><code>${escape(tool.name)}</code></h3>`);
    out.push(`      <p>${escape(tool.description)}</p>`);
    const params = Object.entries(schema.properties || {});
    if (!params.length) {
      out.push("      <p>It takes no parameters.</p>");
      continue;
    }
    // .table-wrap is the site's own wrapper: a wide table scrolls inside it on a phone.
    out.push('      <div class="table-wrap">');
    out.push("        <table>");
    out.push("          <thead><tr><th>Parameter</th><th>Type</th><th>Required</th><th>What it is</th></tr></thead>");
    out.push("          <tbody>");
    for (const [name, prop] of params) {
      const type = name === "filters" ? "object of dimension to value or list of values" : typeLabel(prop);
      out.push(`            <tr><td><code>${escape(name)}</code></td><td>${escape(type)}</td><td>${required.has(name) ? "yes" : "no"}</td><td>${escape(prop.description || "")}</td></tr>`);
    }
    out.push("          </tbody>");
    out.push("        </table>");
    out.push("      </div>");
  }
  return out.join("\n");
}

function replaceRegion(source, name, body) {
  const start = `<!-- build-mcp-page:start ${name} -->`;
  const end = `<!-- build-mcp-page:end ${name} -->`;
  const i = source.indexOf(start);
  const j = source.indexOf(end);
  if (i < 0 || j < i || source.indexOf(start, i + 1) >= 0) throw new Error(`the page needs exactly one ${name} region`);
  return source.slice(0, i + start.length) + "\n" + body + "\n      " + source.slice(j);
}

function writeIfChanged(path, text) {
  let old = null;
  try {
    old = readFileSync(path, "utf8");
  } catch {}
  if (old !== text) {
    writeFileSync(path, text);
    console.log(`wrote ${path}`);
  }
}

let page = readFileSync(PAGE, "utf8");
page = replaceRegion(page, "rules", rulesHtml());
page = replaceRegion(page, "tools", toolsHtml());
writeIfChanged(PAGE, page);

const today = new Date().toISOString().slice(0, 10).replace(/-/g, ".");
writeIfChanged(
  VERSION_FILE,
  `// Written by scripts/mcp/build-page.mjs: the server's version is its build date.\nexport const VERSION = "${today}";\n`,
);

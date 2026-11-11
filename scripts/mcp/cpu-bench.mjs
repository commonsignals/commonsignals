// CPU time per tool call on the largest study, measured in-process. The server's own
// onRequest runs in Node with the site's files standing in for env.ASSETS and the
// local D1 copy (filled by scripts/mcp/load-d1.py --local) opened with node:sqlite
// standing in for env.MCP_DB. Time spent in those stand-ins is reported apart: on
// Cloudflare a static asset read or a D1 query does not count towards the Worker's
// CPU limit. Only the main thread is measured, as Workers bills only that.
//
//   node --disallow-code-generation-from-strings scripts/mcp/cpu-bench.mjs
// Workers forbid code generation, so the flag keeps zod on the same path it takes there.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SLUG = "doac-debate-youtube-2026-09";
const CALLS = {
  list_studies: {},
  get_study: { slug: SLUG },
  get_codebook: { slug: SLUG },
  search_comments_text: { slug: SLUG, text: "unplug", limit: 10 },
  search_comments_filter: { slug: SLUG, filters: { stance: ["agree"], emotion: ["fear"] }, limit: 25 },
  compare_studies: { dimension: "stance" },
  list_pages: {},
  get_page: { url: "https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis" },
};
const toolOf = (key) => key.replace(/_(text|filter)$/, "");
const cpuNow = () => (process.threadCpuUsage ? process.threadCpuUsage() : process.cpuUsage());
const cpuMs = (start) => {
  const d = process.threadCpuUsage ? process.threadCpuUsage(start) : process.cpuUsage(start);
  return (d.user + d.system) / 1000;
};

function findLocalD1() {
  const dir = join(ROOT, ".wrangler/state/v3/d1");
  const stack = [dir];
  while (stack.length) {
    const d = stack.pop();
    if (!existsSync(d)) continue;
    for (const name of readdirSync(d)) {
      const p = join(d, name);
      if (statSync(p).isDirectory()) stack.push(p);
      else if (name.endsWith(".sqlite")) {
        const db = new DatabaseSync(p, { readOnly: true });
        const found = db.prepare("SELECT name FROM sqlite_master WHERE name = 'mcp_studies'").get();
        if (found) return db;
        db.close();
      }
    }
  }
  throw new Error("no local D1 copy found: run python3 scripts/mcp/load-d1.py --local");
}

async function runOne(key) {
  const sqlite = findLocalD1();
  let outside = 0;
  const timed = (fn) => {
    const start = cpuNow();
    try {
      return fn();
    } finally {
      outside += cpuMs(start);
    }
  };
  const ASSETS = {
    async fetch(request) {
      return timed(() => {
        const file = join(ROOT, decodeURIComponent(new URL(request.url).pathname));
        if (!existsSync(file) || statSync(file).isDirectory()) return new Response("not found", { status: 404 });
        const body = readFileSync(file);
        const etag = `"${createHash("md5").update(body).digest("hex")}"`;
        if (request.headers.get("if-none-match") === etag) return new Response(null, { status: 304, headers: { etag } });
        return new Response(body, { status: 200, headers: { etag } });
      });
    },
  };
  const MCP_DB = {
    prepare(sql) {
      let args = [];
      const api = {
        bind: (...a) => ((args = a), api),
        first: async () => timed(() => sqlite.prepare(sql).get(...args)) ?? null,
        all: async () => ({ results: timed(() => sqlite.prepare(sql).all(...args)) }),
      };
      return api;
    },
  };
  const { onRequest } = await import(join(ROOT, "functions/mcp/index.js"));
  const quiet = console.log;
  const samples = [];
  for (let i = 0; i < 31; i++) {
    const body = JSON.stringify({ jsonrpc: "2.0", id: i, method: "tools/call", params: { name: toolOf(key), arguments: CALLS[key] } });
    const request = new Request("http://127.0.0.1:8788/mcp", {
      method: "POST",
      body,
      headers: { "content-type": "application/json", accept: "application/json, text/event-stream", "mcp-protocol-version": "2025-06-18", "cf-connecting-ip": `bench-${i}` },
    });
    outside = 0;
    console.log = () => {};
    const start = cpuNow();
    const res = await onRequest({ request, env: { ASSETS, MCP_DB } });
    const text = await res.text();
    const total = cpuMs(start);
    console.log = quiet;
    if (text.includes('"isError":true')) throw new Error(`${key} returned an error: ${text.slice(0, 300)}`);
    samples.push({ total, outside, worker: total - outside });
  }
  const warm = samples.slice(1).sort((a, b) => a.worker - b.worker);
  console.log(JSON.stringify({ key, first: samples[0], fastest: warm[0], median: warm[Math.floor(warm.length / 2)] }));
}

if (process.argv[2]) {
  await runOne(process.argv[2]);
} else {
  const rows = [];
  for (const key of Object.keys(CALLS)) {
    const out = execFileSync(process.execPath, [...process.execArgv, fileURLToPath(import.meta.url), key], { encoding: "utf8" });
    rows.push(JSON.parse(out.trim().split("\n").pop()));
  }
  const f = (n) => n.toFixed(1).padStart(6);
  console.log(`CPU per call on ${SLUG}, in ms, main thread only. "stand-ins" is the time in the`);
  console.log("asset and D1 stand-ins, which on Cloudflare is not the Worker's CPU. Warm: 30 calls after the first.");
  console.log("tool                    first call  stand-ins |  warm fastest  warm median  stand-ins");
  for (const r of rows) {
    console.log(`${r.key.padEnd(23)} ${f(r.first.worker)}      ${f(r.first.outside)}   |  ${f(r.fastest.worker)}        ${f(r.median.worker)}       ${f(r.median.outside)}`);
  }
}

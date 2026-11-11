// /mcp: Common Signals' read-only MCP server, Streamable HTTP and stateless. It runs
// no model, needs no login and stores nothing. _server.js defines the tools and
// _data.js says where their data comes from.
//
// Any origin may connect, so browser-based clients and the MCP Inspector work: the
// server is public, read-only and holds nothing private, so there is nothing for a
// DNS rebinding attack to reach.
import { createMcpHandler } from "@modelcontextprotocol/server";
import { buildServer, TOOL_NAMES } from "./_server.js";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-expose-headers": "mcp-session-id, mcp-protocol-version",
};
const PREFLIGHT = {
  ...CORS,
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers":
    "content-type, accept, authorization, mcp-protocol-version, mcp-session-id, mcp-method, mcp-name, last-event-id",
  "access-control-max-age": "86400",
};

// 120 requests a minute per IP, counted per isolate, so only approximately:
// Cloudflare runs many isolates. KV isn't used for the counts because it takes one
// write a second per key, and 1,000 writes a day on the Free plan.
const LIMIT = 120;
const WINDOW_MS = 60_000;
const windows = new Map();

function overLimit(ip, now) {
  let window = windows.get(ip);
  if (!window || now - window.start >= WINDOW_MS) {
    if (windows.size > 10_000) {
      for (const [key, old] of windows) if (now - old.start >= WINDOW_MS) windows.delete(key);
    }
    window = { start: now, count: 0 };
    windows.set(ip, window);
  }
  window.count += 1;
  return window.count > LIMIT;
}

// What to log for a request: the tool or MCP method, never its arguments. Only
// names the server defines are logged, so a client cannot put text in the logs.
async function requestName(request) {
  if (request.method !== "POST") return request.method;
  try {
    const body = await request.clone().json();
    const message = Array.isArray(body) ? body[0] : body;
    if (message?.method === "tools/call") return TOOL_NAMES.includes(message.params?.name) ? message.params.name : "unknown tool";
    return typeof message?.method === "string" && /^[a-z][a-zA-Z/_]{0,40}$/.test(message.method) ? message.method : "other";
  } catch {
    return "unreadable";
  }
}

function log(name, status, outcome, started) {
  console.log(JSON.stringify({ mcp: name, status, ...(outcome ? { outcome } : {}), ms: Date.now() - started }));
}

// The SDK streams its response and runs the tool while the stream is open, so the
// log line is written when the stream ends, once the tool's outcome is known.
function finish(response, onEnd) {
  const headers = new Headers(response.headers);
  for (const [key, value] of Object.entries(CORS)) headers.set(key, value);
  let body = response.body;
  if (body) body = body.pipeThrough(new TransformStream({ flush: onEnd }));
  else onEnd();
  return new Response(body, { status: response.status, statusText: response.statusText, headers });
}

export async function onRequest(context) {
  const { request, env } = context;
  const started = Date.now();
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: PREFLIGHT });

  const name = await requestName(request);
  if (overLimit(request.headers.get("cf-connecting-ip") || "local", started)) {
    log(name, 429, null, started);
    return new Response(JSON.stringify({ error: "Too many requests: the limit is 120 a minute. Try again shortly." }), {
      status: 429,
      headers: { ...CORS, "content-type": "application/json", "retry-after": "60" },
    });
  }

  const ctx = { env, origin: new URL(request.url).origin, outcome: null };
  let response;
  try {
    const handler = createMcpHandler(() => buildServer(ctx));
    response = await (typeof handler === "function" ? handler(request) : handler.fetch(request));
  } catch {
    response = new Response(JSON.stringify({ error: "The MCP server failed to handle this request." }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
  return finish(response, () => log(name, response.status, ctx.outcome, started));
}

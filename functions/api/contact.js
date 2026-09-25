// POST /api/contact
// Accepts { name, email, message, website (honeypot) } as JSON and sends it
// to hello@commonsignals.org using Cloudflare's native Email Routing "send
// email" binding, so no third-party API key is needed.
//
// One-off setup on the Cloudflare dashboard (Ben, not committed):
//   1. Enable Email Routing for the commonsignals.org zone.
//   2. Add hello@commonsignals.org as a destination address and verify it
//      (click the link in the verification email Cloudflare sends).
//   3. Add the "SEND_EMAIL" email binding in the Pages dashboard (Settings >
//      Bindings), not wrangler.toml: Pages rejects [[send_email]] there.
// No secret is needed. The FROM address below just needs to be on the same zone.
import { EmailMessage } from "cloudflare:email";

const TO = "hello@commonsignals.org";
const FROM = "noreply@commonsignals.org";

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function toBase64Utf8(str) {
  const bytes = new TextEncoder().encode(str);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

function encodedWord(str) {
  return `=?UTF-8?B?${toBase64Utf8(str)}?=`;
}

export async function onRequestPost(context) {
  const { request, env } = context;

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }

  const name = String(body.name || "").trim().slice(0, 200);
  const email = String(body.email || "").trim().slice(0, 320);
  const message = String(body.message || "").trim().slice(0, 5000);
  const website = String(body.website || "").trim(); // honeypot

  if (website) {
    // Bot filled the hidden field. Pretend success, do nothing.
    return new Response(null, { status: 204 });
  }
  if (!name || !email || !message) {
    return json(400, { error: "Name, email and message are all required." });
  }
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  if (!emailOk) {
    return json(400, { error: "That does not look like a valid email address." });
  }

  if (!env.SEND_EMAIL) {
    // Binding not configured yet (e.g. Email Routing not enabled). Fail
    // clearly so the front end can show the mailto fallback.
    return json(503, { error: "Email sending is not configured yet." });
  }

  const text = `New contact form message from commonsignals.org\n\nName: ${name}\nEmail: ${email}\n\n${message}`;
  const raw = [
    `From: Common Signals website <${FROM}>`,
    `To: ${TO}`,
    `Reply-To: ${email}`,
    `Subject: ${encodedWord(`Contact form: ${name}`)}`,
    `MIME-Version: 1.0`,
    `Content-Type: text/plain; charset="UTF-8"`,
    `Content-Transfer-Encoding: base64`,
    ``,
    toBase64Utf8(text).replace(/(.{76})/g, "$1\r\n"),
  ].join("\r\n");

  try {
    const msg = new EmailMessage(FROM, TO, raw);
    await env.SEND_EMAIL.send(msg);
  } catch (err) {
    console.error("Email Routing send failed", err && err.message);
    return json(502, { error: "Could not send the message. Please try again or email us directly." });
  }

  return new Response(null, { status: 204 });
}

export async function onRequestGet() {
  return json(405, { error: "Use POST." });
}

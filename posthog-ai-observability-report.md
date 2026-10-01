# PostHog AI Observability report

## Outcome

No application changes were needed because this repository is a static site and has no LLM SDK, server-side model-call path, package manifest, or build system. Consequently, there is no existing generation to instrument with PostHog AI Observability.

I selected and reviewed the `manual-capture` workflow because no vendor SDK is present. Manual capture is the correct route if a future backend or worker begins making LLM requests, but adding a client or synthetic `$ai_generation` events now would misrepresent activity and would not instrument a real call.

## Assessment

- `README.md` identifies the project as a static HTML, CSS, JavaScript, and assets snapshot.
- `main.js` contains only site interaction behavior; it does not make model requests.
- `scripts/data-export.py` is data-contract tooling and does not make model requests.
- `functions/data/[slug]/c/[id].js` is the only checked Cloudflare Function and only serves static assets; it does not call an LLM.
- There is no conversation identifier, authenticated user at a model-call site, request turn, or registered model tool from which to construct an AI Observability session, trace, or span.
- No `package.json`, `pyproject.toml`, or `requirements.txt` is present, so there is no LLM SDK or dependency manifest to extend.
- Existing PostHog browser analytics was intentionally left unchanged.
- No dashboard or other PostHog project object was created or modified.

## Verification

The integration is **not applicable / unverified** rather than active: there is no triggerable LLM turn in this repository. Source review of the browser scripts, data tooling, and deployed function confirmed the absence of a model-call path. No package install, model request, synthetic event, or build command was run.

When this project gains an LLM-backed feature, instrument the call immediately after the provider response with a `$ai_generation` capture. Use a stable authenticated user ID only as the distinct ID; use one `$ai_session_id` per conversation and one `$ai_trace_id` per user turn. Include the provider, model, token counts, latency, and prompt/completion payloads as the documented `$ai_*` fields. Capture tool executions as `$ai_span` events that share that turn's trace ID.

Then trigger two turns in one conversation and confirm in **AI Observability → Traces** that both traces belong to one session, each turn has one trace, and all generations or tool spans for a turn share its trace ID.

## Privacy mode

No AI Observability client or capture helper was added, so this project has no AI Observability privacy-mode setting.

For a future manual-capture implementation, decide before sending prompt or completion content whether sensitive text may be stored. Manual payloads should omit `$ai_input` and `$ai_output_choices` when content must not be retained. See [AI Observability privacy mode](https://posthog.com/docs/ai-observability/privacy-mode) for SDK-wide and request-level controls when using a supported wrapper SDK.

## Run record

The workflow decision was recorded in `.posthog-wizard-cache/.posthog-ai.json` as `manual-capture`, with no SDK package or LLM callsite applicable.

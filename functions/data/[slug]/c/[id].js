// Serves the comment detail shell for /data/<slug>/c/<id> without changing
// the URL. Cloudflare Pages' own static-asset resolution finds /data/<slug>/c/
// already exists as a directory (it has an index.html) and 308s straight to
// it before a plain _redirects placeholder rule ever gets a chance to run --
// so the shell has to be served from a Function instead, which runs first.
export async function onRequestGet(context) {
  const shellURL = new URL(`/data/${context.params.slug}/c/index.html`, context.request.url);
  return context.env.ASSETS.fetch(shellURL);
}

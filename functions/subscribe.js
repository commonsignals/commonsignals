const SUBSTACK_SUBSCRIBE_URL = 'https://commonsignalsorg.substack.com/api/v1/free';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

export async function onRequestPost(context) {
  let body;
  try {
    body = await context.request.json();
  } catch {
    return json({ error: 'Invalid request.' }, 400);
  }

  const email = (body.email || '').trim();
  const website = body.website || ''; // honeypot, mirrors the client-side check

  if (website) {
    return json({ ok: true });
  }

  if (!EMAIL_RE.test(email)) {
    return json({ error: 'Please enter a valid email address.' }, 400);
  }

  const pageUrl = context.request.headers.get('referer') || 'https://commonsignals.org/';

  try {
    const substackRes = await fetch(SUBSTACK_SUBSCRIBE_URL, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'user-agent': 'commonsignals.org subscribe form (+https://commonsignals.org)',
      },
      body: JSON.stringify({
        email,
        first_url: pageUrl,
        first_referrer: '',
        current_url: pageUrl,
        current_referrer: '',
        referral_code: '',
        source: 'embed',
      }),
    });

    if (substackRes.ok) {
      return json({ ok: true });
    }

    let message = 'Something went wrong. Please try again.';
    try {
      const data = await substackRes.json();
      if (data && (data.error || data.message)) message = data.error || data.message;
    } catch {}
    return json({ error: message }, 502);
  } catch {
    return json({ error: 'Something went wrong. Please try again.' }, 502);
  }
}

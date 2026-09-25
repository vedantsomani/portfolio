// Worker entry: Astro's Cloudflare handler, plus two rules applied to every response, including
// static assets (wrangler.jsonc sets assets.run_worker_first so assets pass through here):
//   1. X-Robots-Tag: noindex, nofollow while PRE_LAUNCH is true, and always on hosts other than
//      the production domain (workers.dev, preview URLs).
//   2. Security headers (also in public/_headers; set here too so on-demand /contact gets them).
import { handle } from '@astrojs/cloudflare/handler';

const PRODUCTION_HOST = 'vedantsomani.tech';

// Launch switch. true → production is noindex too. Launch: set to false (see REPORT.md).
// Local audits override it without a code change: `wrangler dev --var PRE_LAUNCH:false`
// (npm run preview:audit). With the override, localhost counts as the production host.
const PRE_LAUNCH = true;

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1']);

// CSP: self, plus the Cloudflare Web Analytics beacon (script) and its reporting endpoint.
// 'unsafe-inline' covers Astro's inline hydration/transition scripts and the head motion flag.
// 'wasm-unsafe-eval' lets the hall's Meshopt decoder compile WebAssembly (not JS eval), and blob:
// in connect-src lets GLTFLoader read the textures embedded in saarthi.glb.
const SECURITY_HEADERS: Record<string, string> = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://static.cloudflareinsights.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'self' blob: https://cloudflareinsights.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join('; '),
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
};

// Mirrors public/_redirects. With run_worker_first the adapter's asset fallback follows a
// _redirects 301 itself and serves the target as a 200, so retired paths are answered here.
// PRAHARI moved from Projects to the Lab (design stage, no public artifacts).
const RETIRED: [RegExp, string][] = [
  [/^\/services(\/.*)?$/, '/'],
  [/^\/projects\/prahari$/, '/lab/prahari'],
];

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const retired = RETIRED.find(([re]) => re.test(url.pathname));
    let response = retired
      ? new Response(null, { status: 301, headers: { Location: retired[1] } })
      : await handle(request, env, ctx);

    // With run_worker_first, `astro dev` routes public/ files here and the adapter 404s them.
    // One lookup in the assets binding before accepting a 404 keeps dev working. In production it
    // only runs for real 404s.
    if (response.status === 404 && request.method === 'GET') {
      const asset = await env.ASSETS.fetch(request);
      if (asset.ok) response = asset;
    }

    const host = url.hostname;
    const override = (env as { PRE_LAUNCH?: string }).PRE_LAUNCH;
    const preLaunch = override === undefined ? PRE_LAUNCH : override !== 'false';
    const indexable =
      !preLaunch && (host === PRODUCTION_HOST || (override === 'false' && LOCAL_HOSTS.has(host)));

    // Asset and redirect responses can have immutable headers; copy before setting.
    const out = new Response(response.body, response);
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
      if (!out.headers.has(name)) out.headers.set(name, value);
    }
    if (!indexable) out.headers.set('X-Robots-Tag', 'noindex, nofollow');
    return out;
  },
};

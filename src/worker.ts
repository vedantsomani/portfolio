// Worker entry: Astro's Cloudflare handler, plus one rule. Every host other than the production
// domain (workers.dev, preview URLs) is marked noindex, including static assets. That's why
// wrangler.jsonc sets assets.run_worker_first: without it, assets are served before this code runs.
import { handle } from '@astrojs/cloudflare/handler';

const PRODUCTION_HOST = 'vedantsomani.tech';

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    let response = await handle(request, env, ctx);

    // With run_worker_first, `astro dev` routes public/ files here and the adapter 404s them.
    // One lookup in the assets binding before accepting a 404 keeps dev working; in production
    // it only runs for real 404s.
    if (response.status === 404 && request.method === 'GET') {
      const asset = await env.ASSETS.fetch(request);
      if (asset.ok) response = asset;
    }

    if (new URL(request.url).hostname === PRODUCTION_HOST) return response;

    // Asset and redirect responses can have immutable headers; copy before setting.
    const marked = new Response(response.body, response);
    marked.headers.set('X-Robots-Tag', 'noindex, nofollow');
    return marked;
  },
};

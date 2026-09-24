// Minimal Workers runtime types. The full `wrangler types` runtime output redefines DOM globals
// and breaks client scripts, so only what the server code touches is declared here.
// Bindings (Env) come from worker-configuration.d.ts: `npm run cf-typegen`.

interface RateLimit {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

interface Fetcher {
  fetch(input: Request | string | URL, init?: RequestInit): Promise<Response>;
}

declare module 'cloudflare:workers' {
  export const env: Env;
}

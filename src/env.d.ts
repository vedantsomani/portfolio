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

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

interface ExportedHandler<E = unknown> {
  fetch?(request: Request, env: E, ctx: ExecutionContext): Response | Promise<Response>;
}

// Build-time constants from astro.config.mjs (vite.define): which supplied files exist.
declare const __HAS_RESUME__: boolean;
declare const __HAS_TELEMETRY__: boolean;
declare const __MODELS__: string[];

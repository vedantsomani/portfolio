// @ts-check
import { defineConfig, envField, sessionDrivers } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';
import { existsSync, readdirSync } from 'node:fs';

// Canonical origin. Other hosts (workers.dev, preview URLs) are marked noindex in src/worker.ts.
const site = 'https://vedantsomani.tech';

// Files Vedant supplies later. Prerendering runs in workerd (no fs), so their presence is decided
// here, in Node, and passed to the code as build-time constants (declared in src/env.d.ts).
/** @param {string} path */
const has = (path) => existsSync(new URL(path, import.meta.url));
const models = has('./public/models')
  ? readdirSync(new URL('./public/models', import.meta.url))
      .filter((f) => f.endsWith('.glb'))
      .map((f) => f.replace(/\.glb$/, ''))
  : [];

export default defineConfig({
  site,
  // Static by default; only /contact (and the action endpoint) render on demand in the Worker.
  output: 'static',
  // about.html instead of about/index.html: Workers assets then serve /about directly
  // instead of redirecting to /about/.
  build: { format: 'file', inlineStylesheets: 'always' },
  trailingSlash: 'never',
  adapter: cloudflare({
    // Every image sits on a prerendered page, so optimise at build time. No Images binding.
    imageService: 'compile',
  }),
  // Sessions are unused. An explicit driver stops the adapter provisioning a KV namespace for them.
  session: { driver: sessionDrivers.lruCache() },
  // /contact renders on demand, so the sitemap can't discover it from the build; list it explicitly.
  integrations: [mdx(), sitemap({ customPages: [`${site}/contact`] })],
  prefetch: { prefetchAll: false, defaultStrategy: 'hover' },
  image: { responsiveStyles: false },
  vite: {
    // Minify the Worker bundle too (Astro builds server output unminified): smaller cold starts,
    // and no comments from our code or dependencies ship.
    // Pre-bundle the actions route for the Worker environment. Discovered late on a cold cache
    // (fresh CI checkout), it made Vite reload mid-`astro check` and fail on a vanished chunk.
    environments: {
      ssr: { optimizeDeps: { include: ['astro/actions/runtime/entrypoints/route.js'] } },
    },
    plugins: [
      {
        name: 'minify-worker',
        apply: 'build',
        configEnvironment: (name) =>
          name === 'ssr' ? { build: { minify: 'esbuild' } } : undefined,
      },
    ],
    define: {
      __HAS_RESUME__: JSON.stringify(has('./public/resume.pdf')),
      __HAS_TELEMETRY__: JSON.stringify(has('./public/data/fusion-benchmark.csv')),
      __MODELS__: JSON.stringify(models),
    },
  },
  env: {
    schema: {
      // Secrets: `wrangler secret put RESEND_API_KEY` / `CONTACT_TO_EMAIL`; locally in .dev.vars.
      RESEND_API_KEY: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_TO_EMAIL: envField.string({ context: 'server', access: 'secret', optional: true }),
      // Optional; defaults to "Vedant Somani <hello@vedantsomani.tech>" (src/lib/enquiry-email.ts).
      CONTACT_FROM_EMAIL: envField.string({ context: 'server', access: 'secret', optional: true }),
      // Test-only: points the Resend call at a local stub (acceptance check 10). Unset in production.
      RESEND_API_URL: envField.string({ context: 'server', access: 'secret', optional: true }),
      // TODO(vedant): Cloudflare Web Analytics token (dashboard → Web Analytics → add site).
      PUBLIC_CF_BEACON_TOKEN: envField.string({
        context: 'client',
        access: 'public',
        optional: true,
      }),
    },
  },
});

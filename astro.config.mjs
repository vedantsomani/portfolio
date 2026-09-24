// @ts-check
import { defineConfig, envField, sessionDrivers } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

// TODO(vedant): production domain. Until then canonicals point at SITE_URL or localhost.
const site = process.env.SITE_URL ?? 'http://localhost:4321';

export default defineConfig({
  site,
  // Static by default; only /contact (and the action endpoint) render on demand in the Worker.
  output: 'static',
  // services.html instead of services/index.html: Workers assets then serve /services directly
  // instead of redirecting to /services/.
  build: { format: 'file' },
  trailingSlash: 'never',
  adapter: cloudflare({
    // Every image sits on a prerendered page, so optimise at build time. No Images binding.
    imageService: 'compile',
  }),
  // Sessions are unused. An explicit driver stops the adapter provisioning a KV namespace for them.
  session: { driver: sessionDrivers.lruCache() },
  integrations: [mdx(), sitemap()],
  prefetch: { prefetchAll: false, defaultStrategy: 'hover' },
  image: { responsiveStyles: false },
  env: {
    schema: {
      // Secrets: `wrangler secret put RESEND_API_KEY` / `CONTACT_TO_EMAIL`; locally in .dev.vars.
      RESEND_API_KEY: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_TO_EMAIL: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_FROM_EMAIL: envField.string({
        context: 'server',
        access: 'secret',
        default: 'Portfolio <onboarding@resend.dev>',
      }),
      // TODO(vedant): Cloudflare Web Analytics token (dashboard → Web Analytics → add site).
      PUBLIC_CF_BEACON_TOKEN: envField.string({
        context: 'client',
        access: 'public',
        optional: true,
      }),
    },
  },
});

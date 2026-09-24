import { env } from 'cloudflare:workers';

// Per-IP limit for the contact form, backed by the Workers Rate Limiting binding (wrangler.jsonc).
// The binding counts per Cloudflare location and only supports 10 s / 60 s windows, so it is a
// burst guard (5 per minute), not the 5-per-hour the spec asks for. The honeypot handles bots.
// If the binding is missing (misconfigured deploy), fail open rather than block real enquiries.
export async function rateLimit(ip: string): Promise<{ ok: boolean }> {
  const limiter = (env as Partial<Env>).CONTACT_LIMITER;
  if (!limiter) return { ok: true };
  const { success } = await limiter.limit({ key: `contact:${ip}` });
  return { ok: success };
}

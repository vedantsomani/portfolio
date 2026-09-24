// Sliding-window limiter keyed by IP: 5 submissions per hour.
// Memory lives per serverless instance, so this is best-effort on Vercel (a cold start or a second
// instance resets it). The honeypot catches most bots; a shared store is the upgrade if spam appears.
const WINDOW_MS = 60 * 60 * 1000;
const LIMIT = 5;
const hits = new Map<string, number[]>();

export function rateLimit(key: string, now = Date.now()): { ok: boolean; retryAfterMin: number } {
  const recent = (hits.get(key) ?? []).filter((t) => now - t < WINDOW_MS);
  if (recent.length >= LIMIT) {
    hits.set(key, recent);
    return { ok: false, retryAfterMin: Math.ceil((WINDOW_MS - (now - recent[0])) / 60000) };
  }
  recent.push(now);
  hits.set(key, recent);
  // Keep the map from growing without bound on a long-lived instance.
  if (hits.size > 5000) {
    for (const [k, v] of hits) if (v.every((t) => now - t >= WINDOW_MS)) hits.delete(k);
  }
  return { ok: true, retryAfterMin: 0 };
}

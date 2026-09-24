// Analytics events from SITE_SPEC §7. One helper so the backend can be chosen later without
// touching call sites. TODO(vedant): pick the event backend; until then track() is a no-op.
// Cloudflare Web Analytics (the beacon in BaseLayout) covers page views only, not custom events.

export const EVENTS = [
  'hero_start_project',
  'hero_see_lab',
  'hero_lens_used',
  'project_open',
  'hall_object_rotate',
  'service_view',
  'contact_open',
  'form_start',
  'lead_submit',
  'email_click',
  'whatsapp_click',
  'resume_download',
  'github_out',
] as const;

export type EventName = (typeof EVENTS)[number];
export type EventProps = Record<string, string | number | boolean>;

export function track(event: EventName, props?: EventProps): void {
  if (import.meta.env.DEV) console.debug('[track]', event, props ?? {});
}

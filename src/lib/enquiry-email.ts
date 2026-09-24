// Builds the enquiry email sent to Vedant: subject, plain text, and an HTML version with the
// same structure (one field per line, blank line, then the message).

// vedantsomani.tech is verified in Resend, so the site's own address is the default sender.
export const DEFAULT_FROM = 'Vedant Somani <hello@vedantsomani.tech>';

// Resend's shared test sender only delivers to the account owner (a live send returned 403),
// so a resend.dev address is never used in production, even if it is configured.
export function resolveFrom(configured: string | undefined, isProd: boolean): string {
  const value = configured?.trim();
  if (!value) return DEFAULT_FROM;
  if (isProd && /@resend\.dev>?$/i.test(value)) {
    console.warn('[contact] CONTACT_FROM_EMAIL uses resend.dev; sending from', DEFAULT_FROM);
    return DEFAULT_FROM;
  }
  return value;
}

export interface Enquiry {
  name: string;
  email: string;
  company?: string;
  projectType: string;
  budget: string;
  message: string;
}

const escapeHtml = (s: string) =>
  s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

export function buildEnquiryEmail(e: Enquiry): { subject: string; text: string; html: string } {
  const fields: [string, string][] = [
    ['Name', e.name],
    ['Email', e.email],
    ['Company / site', e.company?.trim() || '—'],
    ['Project type', e.projectType],
    ['Budget', e.budget],
  ];

  const text = [
    ...fields.map(([label, value]) => `${label}: ${value}`),
    '',
    'Message:',
    e.message,
  ].join('\n');

  const html = [
    '<div style="font-family: system-ui, sans-serif; font-size: 15px; line-height: 1.5; color: #14100e;">',
    ...fields.map(
      ([label, value]) => `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`,
    ),
    '<br>',
    '<div><strong>Message:</strong></div>',
    `<div style="white-space: pre-wrap;">${escapeHtml(e.message)}</div>`,
    '</div>',
  ].join('\n');

  return { subject: `New enquiry — ${e.name} (${e.projectType})`, text, html };
}

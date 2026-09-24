// Builds the contact email sent to Vedant: subject, plain text, and an HTML version with the
// same structure (one field per line, blank line, then the message). All input is escaped in HTML.

// vedantsomani.tech is verified in Resend, so the site's own address is the default sender.
export const DEFAULT_FROM = 'Vedant Somani <hello@vedantsomani.tech>';

// Resend's shared test domain only delivers to the account owner (a live send returned 403), so a
// sender on it is never used in production, even if one is configured.
const SHARED_TEST_DOMAIN = /@resend\.dev>?$/i;

export function resolveFrom(configured: string | undefined, isProd: boolean): string {
  const value = configured?.trim();
  if (!value) return DEFAULT_FROM;
  if (isProd && SHARED_TEST_DOMAIN.test(value)) {
    console.warn('[contact] CONTACT_FROM_EMAIL is on the shared test domain; using', DEFAULT_FROM);
    return DEFAULT_FROM;
  }
  return value;
}

export interface Message {
  name: string;
  email: string;
  reason: string;
  message: string;
}

const escapeHtml = (s: string) =>
  s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

// Header-safe: no line breaks can reach the subject line.
const oneLine = (s: string) => s.replace(/[\r\n]+/g, ' ').trim();

export function buildMessageEmail(m: Message): { subject: string; text: string; html: string } {
  const fields: [string, string][] = [
    ['Name', m.name],
    ['Email', m.email],
    ['Reason', m.reason],
  ];

  const text = [
    ...fields.map(([label, value]) => `${label}: ${value}`),
    '',
    'Message:',
    m.message,
  ].join('\n');

  const html = [
    '<div style="font-family: system-ui, sans-serif; font-size: 15px; line-height: 1.5; color: #14100e;">',
    ...fields.map(
      ([label, value]) => `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`,
    ),
    '<br>',
    '<div><strong>Message:</strong></div>',
    `<div style="white-space: pre-wrap;">${escapeHtml(m.message)}</div>`,
    '</div>',
  ].join('\n');

  return { subject: `New message — ${oneLine(m.name)} (${m.reason})`, text, html };
}

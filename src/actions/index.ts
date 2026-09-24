import { ActionError, defineAction } from 'astro:actions';
import { z } from 'astro/zod';
import {
  CONTACT_FROM_EMAIL,
  CONTACT_TO_EMAIL,
  RESEND_API_KEY,
  RESEND_API_URL,
} from 'astro:env/server';
import { reasons, site } from '../data/site';
import { rateLimit } from '../lib/rate-limit';
import { buildMessageEmail, resolveFrom } from '../lib/enquiry-email';

const reasonValues = reasons.map((r) => r.value) as [string, ...string[]];

export const contactSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Enter your name.')
    .max(100, 'Keep your name under 100 characters.'),
  email: z.email('Enter an email address like name@example.com.'),
  reason: z.enum(reasonValues, 'Choose a reason.'),
  message: z
    .string()
    .trim()
    .min(20, 'Tell me a little more — at least 20 characters.')
    .max(5000, 'Keep the message under 5,000 characters.'),
  // Honeypot: humans never see this field.
  website: z.string().optional(),
});

const reasonLabel = (value: string) => reasons.find((r) => r.value === value)?.label ?? value;

export const server = {
  contact: defineAction({
    accept: 'form',
    input: contactSchema,
    handler: async (input, context) => {
      // Bots that fill the honeypot get a normal-looking success and nothing is sent.
      if (input.website) return { sent: true };

      const limit = await rateLimit(context.clientAddress);
      if (!limit.ok) {
        throw new ActionError({
          code: 'TOO_MANY_REQUESTS',
          message:
            'Too many messages from this connection. Wait a minute and try again, or email directly.',
        });
      }

      const email = buildMessageEmail({
        name: input.name,
        email: input.email,
        reason: reasonLabel(input.reason),
        message: input.message,
      });
      // Secrets are read from the Worker env at runtime (astro:env via the Cloudflare adapter).
      // CONTACT_FROM_EMAIL and CONTACT_TO_EMAIL are optional overrides of the site defaults.
      const from = resolveFrom(CONTACT_FROM_EMAIL, import.meta.env.PROD);
      const to = CONTACT_TO_EMAIL || site.email;

      if (!RESEND_API_KEY || !to) {
        if (import.meta.env.DEV) {
          const log = ['[contact] Resend not configured; message logged instead.'];
          log.push(`From: ${from}`, `To: ${to}`, `Subject: ${email.subject}`, '', email.text);
          console.info(log.join('\n'));
          return { sent: true };
        }
        throw new ActionError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'The form is not connected yet. Please email instead.',
        });
      }

      // Resend's REST API over fetch (runs on workerd without the Node SDK).
      const res = await fetch(`${RESEND_API_URL || 'https://api.resend.com'}/emails`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from,
          to: [to],
          reply_to: input.email,
          subject: email.subject,
          text: email.text,
          html: email.html,
        }),
      });
      if (!res.ok) {
        console.error('[contact] Resend error', res.status, await res.text());
        throw new ActionError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'The message could not be sent. Please try again or email directly.',
        });
      }
      return { sent: true };
    },
  }),
};

import { ActionError, defineAction } from 'astro:actions';
import { z } from 'astro/zod';
import { CONTACT_FROM_EMAIL, CONTACT_TO_EMAIL, RESEND_API_KEY } from 'astro:env/server';
import { Resend } from 'resend';
import { budgets, projectTypes } from '../data/services';
import { rateLimit } from '../lib/rate-limit';
import { site } from '../data/site';
import { buildEnquiryEmail, resolveFrom } from '../lib/enquiry-email';

const typeValues = projectTypes.map((t) => t.value) as [string, ...string[]];
const budgetValues = budgets.map((b) => b.value) as [string, ...string[]];

export const contactSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Enter your name.')
    .max(100, 'Keep your name under 100 characters.'),
  email: z.email('Enter an email address like name@example.com.'),
  company: z.string().trim().max(200, 'Keep this under 200 characters.').optional(),
  type: z.enum(typeValues, 'Choose a project type.'),
  budget: z.enum(budgetValues, 'Choose a budget range.'),
  description: z
    .string()
    .trim()
    .min(20, 'Tell me a little more — at least 20 characters.')
    .max(5000, 'Keep the description under 5,000 characters.'),
  // Honeypot: humans never see this field.
  website: z.string().optional(),
});

const label = (list: readonly { value: string; label: string }[], value: string) =>
  list.find((x) => x.value === value)?.label ?? value;

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

      const email = buildEnquiryEmail({
        name: input.name,
        email: input.email,
        company: input.company,
        projectType: label(projectTypes, input.type),
        budget: label(budgets, input.budget),
        message: input.description,
      });
      // Secrets are read from the Worker env at runtime (astro:env via the Cloudflare adapter).
      // CONTACT_FROM_EMAIL and CONTACT_TO_EMAIL are optional overrides of the site defaults.
      const from = resolveFrom(CONTACT_FROM_EMAIL, import.meta.env.PROD);
      const to = CONTACT_TO_EMAIL ?? site.email;

      if (!RESEND_API_KEY || !to) {
        if (import.meta.env.DEV) {
          const log = ['[contact] Resend not configured; message logged instead.'];
          log.push(`From: ${from}`, `Subject: ${email.subject}`, '', email.text);
          console.info(log.join('\n'));
          return { sent: true };
        }
        throw new ActionError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'The form is not connected yet. Please email instead.',
        });
      }

      const resend = new Resend(RESEND_API_KEY);
      const { error } = await resend.emails.send({
        from,
        to,
        replyTo: input.email,
        subject: email.subject,
        text: email.text,
        html: email.html,
      });
      if (error) {
        console.error('[contact] Resend error', error);
        throw new ActionError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'The message could not be sent. Please try again or email directly.',
        });
      }
      return { sent: true };
    },
  }),
};

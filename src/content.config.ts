import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Every fact in these collections comes from SITE_SPEC §6. Unknown values stay optional and
// render as dev-only TODO markers; production drops them rather than guessing.

const projects = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/projects' }),
  schema: ({ image }) =>
    z
      .object({
        title: z.string(),
        slug: z.string(),
        // Problem- or result-first, one line.
        summary: z.string().max(140),
        kind: z.enum(['client', 'engineering']),
        status: z.enum(['shipped', 'prototype', 'research']).optional(),
        // true → no repo link, no internals (AGENTS.md hard rule 3).
        restricted: z.boolean().default(false),
        year: z.string().optional(),
        role: z.array(z.string()).default([]),
        stack: z.array(z.string()).default([]),
        cover: image(),
        coverAlt: z.string(),
        /** Dev-only TODO label while the cover is a generated placeholder. */
        coverTodo: z.string().optional(),
        featured: z.boolean().default(false),
        order: z.number(),
        outcome: z.string().optional(),
        demoUrl: z.url().optional(),
        repoUrl: z.url().optional(),
        // Rendered in Plex Mono: part numbers and measurements only.
        specs: z.array(z.object({ label: z.string(), value: z.string() })).optional(),
      })
      .refine((p) => !(p.restricted && p.repoUrl), {
        message: 'Restricted projects cannot have a repoUrl (AGENTS.md hard rule 3).',
        path: ['repoUrl'],
      }),
});

const lab = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/lab' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      slug: z.string(),
      // No status → the entry is hidden in production.
      status: z.enum(['concept', 'prototype', 'validated', 'archived']).optional(),
      date: z.coerce.date().optional(),
      discipline: z.string(),
      artifact: image(),
      artifactAlt: z.string(),
      artifactTodo: z.string().optional(),
      hypothesis: z.string().optional(),
      /** One-line verified result. The Home lab preview needs status + result. */
      result: z.string().optional(),
      /** GLB path under public/ for the hardware hall. */
      model: z.string().optional(),
      /** CSV path under public/ for the telemetry plot. */
      telemetry: z.string().optional(),
      order: z.number().default(0),
    }),
});

export const collections = { projects, lab };

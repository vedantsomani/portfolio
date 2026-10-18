import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { DISCIPLINES } from './lib/disciplines';

// Every fact in these collections comes from SITE_SPEC §6. Unknown values stay optional and
// render as dev-only TODO markers; production drops them rather than guessing.
// Status labels must match the evidence (AGENTS.md hard rule 8): each value below names the
// strongest thing the project's own files show, never a stage it has not reached.

// Block diagram: the case study's Architecture section and, for a project with no real image, its
// card cover. `links[i]` labels the connection after column i, only where the page states it.
const architecture = z.object({
  label: z.string(),
  columns: z.array(z.object({ title: z.string(), nodes: z.array(z.string()) })).min(2),
  links: z.array(z.string().nullable()).optional(),
});

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
        status: z
          .enum(['in-layout', 'frozen', 'bench-tested', 'research', 'prototype', 'built'])
          .optional(),
        // true → no repo link, no internals (AGENTS.md hard rule 3).
        restricted: z.boolean().default(false),
        year: z.string().optional(),
        role: z.array(z.string()).default([]),
        stack: z.array(z.string()).default([]),
        disciplines: z.array(z.enum(DISCIPLINES)).min(1),
        /** Up to two results for the card, in mono. Restates the page; never new claims. */
        results: z
          .array(z.object({ label: z.string(), value: z.string() }))
          .max(2)
          .optional(),
        architecture: architecture.optional(),
        /** A real image only. Without one the card draws the block diagram instead. */
        cover: image().optional(),
        coverAlt: z.string().optional(),
        /** Evidence class of the cover ("Photograph", "KiCad render, not a photograph"): the
         *  record header labels it exhibit 00. */
        coverKind: z.string().optional(),
        /** Dev-only TODO naming the image still needed. */
        coverTodo: z.string().optional(),
        featured: z.boolean().default(false),
        order: z.number(),
        outcome: z.string().optional(),
        demoUrl: z.url().optional(),
        repoUrl: z.url().optional(),
        // Rendered in Plex Mono: part numbers and measurements only.
        specs: z.array(z.object({ label: z.string(), value: z.string() })).optional(),
        /** Credit for work this project builds on (shown in the case header). */
        builtOn: z.string().optional(),
        /** Quick-scan block at the top of the case study. Restates the page; never new claims. */
        glance: z
          .object({
            problem: z.string().optional(),
            part: z.string().optional(),
            exists: z.string().optional(),
            result: z.string().optional(),
          })
          .optional(),
      })
      .refine((p) => !(p.restricted && p.repoUrl), {
        message: 'Restricted projects cannot have a repoUrl (AGENTS.md hard rule 3).',
        path: ['repoUrl'],
      })
      .refine((p) => !p.cover || p.coverAlt, {
        message: 'A cover needs coverAlt.',
        path: ['coverAlt'],
      })
      .refine((p) => p.cover || p.architecture, {
        message: 'Without a cover image the card draws the architecture diagram, so add one.',
        path: ['architecture'],
      }),
});

const lab = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/lab' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      slug: z.string(),
      // No status → the entry is hidden in production.
      status: z
        .enum(['concept', 'simulation-tested', 'prototype', 'validated', 'archived'])
        .optional(),
      date: z.coerce.date().optional(),
      discipline: z.string(),
      /** Architecture and results only (AGENTS.md hard rule 3): PRAHARI, SKYNET. */
      restricted: z.boolean().default(false),
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

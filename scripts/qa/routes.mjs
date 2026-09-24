// Every route the acceptance checks cover (FINAL_GOAL §2). /lab/[slug] pages exist only for lab
// entries with a status; none has one yet, so the list below is read from the build.
import { readdirSync, existsSync } from 'node:fs';

const labDir = 'dist/client/lab';
const labEntries = existsSync(labDir)
  ? readdirSync(labDir)
      .filter((f) => f.endsWith('.html'))
      .map((f) => `/lab/${f.replace(/\.html$/, '')}`)
  : [];

export const ROUTES = [
  '/',
  '/projects',
  '/projects/saarthi',
  '/projects/prahari',
  '/projects/vajra',
  '/lab',
  ...labEntries,
  '/about',
  '/contact',
];
export const NOT_FOUND = '/this-page-does-not-exist';
export const BASE = process.env.BASE ?? 'http://127.0.0.1:8787';

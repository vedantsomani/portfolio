// Every route the acceptance checks cover (FINAL_GOAL §2). Project and lab pages are read from the
// build, so new entries are covered without editing this list (lab pages exist only with a status).
import { readdirSync, existsSync } from 'node:fs';

const built = (dir, prefix) =>
  existsSync(dir)
    ? readdirSync(dir)
        .filter((f) => f.endsWith('.html'))
        .map((f) => `${prefix}/${f.replace(/\.html$/, '')}`)
    : [];
const projectPages = built('dist/client/projects', '/projects');
const labEntries = built('dist/client/lab', '/lab');

export const ROUTES = [
  '/',
  '/projects',
  ...projectPages,
  '/lab',
  ...labEntries,
  '/about',
  '/contact',
];
export const NOT_FOUND = '/this-page-does-not-exist';
export const BASE = process.env.BASE ?? 'http://127.0.0.1:8787';

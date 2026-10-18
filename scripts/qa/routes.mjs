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

// Three places (the archive, the briefing, contact) and every record, which opens as a file over the
// lab. /about, /projects and /lab redirect into the home page (src/worker.ts): see REDIRECTS.
export const ROUTES = ['/', ...projectPages, ...labEntries, '/briefing', '/contact'];
export const REDIRECTS = [
  ['/about', '/#transmission'],
  ['/projects', '/#lab'],
  ['/lab', '/#lab'],
];
export const NOT_FOUND = '/this-page-does-not-exist';
export const BASE = process.env.BASE ?? 'http://127.0.0.1:8787';

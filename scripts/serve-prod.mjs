// Local stand-in for Vercel: serves .vercel/output/static with brotli and routes on-demand
// paths to the built function, so Lighthouse measures production output.
// Usage: npm run build && node scripts/serve-prod.mjs [port]
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { brotliCompressSync } from 'node:zlib';

const port = Number(process.argv[2] ?? 4322);
const root = '.vercel/output';
const staticDir = join(root, 'static');
const { default: fn } = await import(
  new URL(`../${root}/functions/_render.func/dist/server/entry.mjs`, import.meta.url)
);

const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.xml': 'application/xml',
  '.txt': 'text/plain',
  '.json': 'application/json',
  '.woff2': 'font/woff2',
  '.avif': 'image/avif',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
};
const compressible = new Set(['.html', '.js', '.css', '.svg', '.xml', '.txt', '.json']);
const dynamic = [/^\/_actions(\/.*)?$/, /^\/contact\/?$/, /^\/_image\/?$/];

async function file(path) {
  try {
    const s = await stat(path);
    return s.isFile() ? path : null;
  } catch {
    return null;
  }
}

createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  const send = (status, body, ext, extra = {}) => {
    const headers = { 'content-type': types[ext] ?? 'application/octet-stream', ...extra };
    if (compressible.has(ext) && /\bbr\b/.test(req.headers['accept-encoding'] ?? '')) {
      body = brotliCompressSync(body);
      headers['content-encoding'] = 'br';
    }
    headers['content-length'] = body.length;
    res.writeHead(status, headers).end(body);
  };

  // Vercel injects these at the edge; locally, an empty script stands in.
  if (url.pathname.startsWith('/_vercel/')) return send(200, Buffer.from(''), '.js');

  if (dynamic.some((r) => r.test(url.pathname))) {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const request = new Request(url, {
      method: req.method,
      headers: { ...req.headers, 'x-forwarded-for': '127.0.0.1' },
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : Buffer.concat(chunks),
    });
    const response = await fn.fetch(request);
    const body = Buffer.from(await response.arrayBuffer());
    const headers = Object.fromEntries(response.headers);
    delete headers['content-length'];
    delete headers['content-encoding'];
    const ext = (headers['content-type'] ?? '').includes('html') ? '.html' : '.json';
    return send(response.status, body, ext, headers);
  }

  const rel = normalize(decodeURIComponent(url.pathname)).replace(/^([/\\])+/, '');
  const hit =
    (await file(join(staticDir, rel))) ??
    (await file(join(staticDir, rel, 'index.html'))) ??
    (await file(join(staticDir, `${rel}.html`)));
  if (hit) {
    const extra = url.pathname.startsWith('/_astro/')
      ? { 'cache-control': 'public, max-age=31536000, immutable' }
      : {};
    return send(200, await readFile(hit), extname(hit), extra);
  }
  send(404, await readFile(join(staticDir, '404.html')), '.html');
}).listen(port, () => console.log(`serving production build on http://localhost:${port}`));

// Contact sheet from frames.mjs captures: node scripts/qa/sheet.mjs <dir> <prefix> <cols> <tileW> <out>
import sharp from 'sharp';
import { readdirSync } from 'node:fs';
const [, , dir, prefix, colsArg, tileArg, out] = process.argv;
const cols = Number(colsArg);
const tileW = Number(tileArg);
const files = readdirSync(dir)
  .filter((f) => f.startsWith(prefix + '-') && /-\d+\.jpg$/.test(f))
  .sort((a, b) => Number(a.match(/-(\d+)\.jpg$/)[1]) - Number(b.match(/-(\d+)\.jpg$/)[1]));
const first = await sharp(`${dir}/${files[0]}`).metadata();
const tileH = Math.round((first.height / first.width) * tileW);
const tiles = await Promise.all(files.map((f) => sharp(`${dir}/${f}`).resize(tileW, tileH).toBuffer()));
const rows = Math.ceil(files.length / cols);
await sharp({ create: { width: cols * tileW + (cols - 1) * 6, height: rows * tileH + (rows - 1) * 6, channels: 3, background: '#444' } })
  .composite(tiles.map((t, i) => ({ input: t, left: (i % cols) * (tileW + 6), top: Math.floor(i / cols) * (tileH + 6) })))
  .jpeg({ quality: 70 })
  .toFile(out);

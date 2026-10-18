// Encodes the renders from blender/out/ for the site:
//   lab     blender/out/rest-desk.png (blender/lab.py --shots hub: the room with the hologram on) →
//           src/assets/set/lab-rest-desk.jpg (astro:assets makes the AVIF/JPG sizes at build);
//           blender/out/close/<id>.png → public/set/lab/close/<id>.avif (the push-in's close-ups)
//   film    blender/out/film/<tier>/<shot>.mp4 + film.json (blender/film.py) →
//           public/set/film/<tier>/ and src/data/film.json, with the film's first frame as poster
//   holo    blender/out/holo-{desk,phone}.mp4 (blender/lab.py --shots holoanim) → public/set/holo/
// Films get their index moved to the front (scripts/faststart.mjs) so they play while they load.
// Usage: node scripts/set-images.mjs
import { existsSync } from 'node:fs';
import { copyFile, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';
import { faststart } from './faststart.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'blender', 'out');
const stills = join(root, 'src', 'assets', 'set');
const pub = join(root, 'public', 'set', 'lab');
const anchors = join(root, 'src', 'data', 'lab-set.json');

if (!existsSync(out)) {
  console.error('No renders: run blender/lab.py first (see its header).');
  process.exit(1);
}
await mkdir(stills, { recursive: true });

let bytes = 0;
const note = async (file) => {
  const { size } = await stat(file);
  bytes += size;
  return `${(size / 1024).toFixed(1)} KB`;
};

for (const name of ['rest-desk']) {
  const src = join(out, `${name}.png`);
  if (!existsSync(src)) continue;
  const dest = join(stills, `lab-${name}.jpg`);
  await sharp(src).jpeg({ quality: 90, mozjpeg: true }).toFile(dest);
  console.log(`still   ${name} → ${await note(dest)}`);
}

const close = [];
const closeDir = join(out, 'close');
if (existsSync(closeDir)) {
  const dest = join(pub, 'close');
  await rm(dest, { recursive: true, force: true });
  await mkdir(dest, { recursive: true });
  for (const f of (await readdir(closeDir)).filter((x) => x.endsWith('.png')).sort()) {
    const id = f.replace(/\.png$/, '');
    const file = join(dest, `${id}.avif`);
    await sharp(join(closeDir, f))
      .resize({ width: 1600 })
      .avif({ quality: 45, effort: 6 })
      .toFile(file);
    close.push(id);
    console.log(`close   ${id} → ${await note(file)}`);
  }
}

// The film: each shot as its own file per tier (phone, desk, hd), its chapter times, and its first
// frame. The folder is the script's own output, so it is rebuilt from scratch each run.
const filmDest = join(root, 'public', 'set', 'film');
const filmMeta = join(out, 'film.json');
if (existsSync(join(out, 'film')) && existsSync(filmMeta)) {
  const { tiers = [], chapters = [] } = JSON.parse(await readFile(filmMeta, 'utf8'));
  await rm(filmDest, { recursive: true, force: true });
  for (const tag of tiers) {
    await mkdir(join(filmDest, tag), { recursive: true });
    for (const { id } of chapters) {
      const file = join(filmDest, tag, `${id}.mp4`);
      await writeFile(file, faststart(await readFile(join(out, 'film', tag, `${id}.mp4`))));
      console.log(`film    ${tag}/${id} → ${await note(file)}`);
    }
  }
  const firstDir = join(out, 'arrival', 'orbit');
  const first = existsSync(firstDir)
    ? (await readdir(firstDir)).filter((f) => /^\d{4}\.(png|jpg)$/.test(f)).sort()[0]
    : null;
  if (first) {
    await sharp(join(firstDir, first))
      .resize({ width: 1920 })
      .avif({ quality: 55, effort: 6 })
      .toFile(join(filmDest, 'poster.avif'));
  }
  await copyFile(join(out, 'film.json'), join(root, 'src', 'data', 'film.json'));
}

{
  const holo = join(out, 'holo');
  const hologram = { video: false, poster: false };
  const hdest = join(root, 'public', 'set', 'holo');
  if (existsSync(join(out, 'holo-desk.mp4')) || existsSync(join(out, 'holo.png'))) {
    await mkdir(hdest, { recursive: true });
    for (const tag of ['desk', 'phone']) {
      const film = join(out, `holo-${tag}.mp4`);
      if (!existsSync(film)) continue;
      await writeFile(join(hdest, `${tag}.mp4`), faststart(await readFile(film)));
      console.log(`film    holo-${tag} → ${await note(join(hdest, `${tag}.mp4`))}`);
      hologram.video = true;
    }
    const poster = existsSync(join(holo, '0000.png'))
      ? join(holo, '0000.png')
      : join(out, 'holo.png');
    await sharp(poster)
      .resize({ width: 1600 })
      .avif({ quality: 52, effort: 6 })
      .toFile(join(hdest, 'poster.avif'));
    console.log(`poster  holo → ${await note(join(hdest, 'poster.avif'))}`);
    hologram.poster = true;
  }
  await writeFile(
    join(root, 'src', 'data', 'arrival.json'),
    `${JSON.stringify({ note: 'Written by scripts/set-images.mjs.', hologram }, null, 2)}
`,
  );
}

if (existsSync(anchors)) {
  const data = JSON.parse(await readFile(anchors, 'utf8'));
  if (close.length) data.close = close;
  await writeFile(anchors, `${JSON.stringify(data, null, 2)}\n`);
}
console.log(`total ${(bytes / 1024 / 1024).toFixed(2)} MB`);

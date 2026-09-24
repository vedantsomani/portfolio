// Flat, labelled-in-code placeholders. Every file here is TODO(vedant): replace with a real photo.
// Run: node scripts/placeholders.mjs
import sharp from 'sharp';

const out = 'src/assets/placeholders';
const items = [
  // name, width, height, colour (photo-toned warm greys, one step apart so tiles read as distinct)
  ['hero-photo', 2400, 1600, '#3b332e'],
  ['client-cover', 2400, 1050, '#2f2824'],
  ['saarthi-cover', 1600, 1200, '#352d29'],
  ['skynet-cover', 1200, 1600, '#2b2521'],
  ['hall-saarthi', 1200, 1200, '#2a2320'],
  ['hall-setu', 1200, 1200, '#2a2320'],
];

for (const [name, width, height, background] of items) {
  await sharp({ create: { width, height, channels: 3, background } })
    .jpeg({ quality: 80 })
    .toFile(`${out}/${name}.jpg`);
  console.log(`${name}.jpg ${width}x${height}`);
}

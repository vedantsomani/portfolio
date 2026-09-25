// Hardware hall fallback: a 24-frame turntable per object, as one horizontal AVIF sprite
// (public/hall/<id>-sprite.avif), scrubbed by drag when WebGL is unavailable.
// It renders public/models/<id>.glb when it exists (else the procedural mesh from
// src/scripts/hall/models.ts) with Three.js in Edge (Playwright), and stitches the frames with sharp.
// Re-run whenever a GLB changes.
// Run: node scripts/hall-sprites.mjs
import { build } from 'esbuild';
import { chromium } from 'playwright';
import sharp from 'sharp';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';

// Must match the ids in src/data/hall.ts (SETU is out until confirmed).
const IDS = ['saarthi'];
const FRAMES = 24;
const SIZE = 480;
const OUT = 'public/hall';

const harness = `
import { Box3, DirectionalLight, Group, PerspectiveCamera, PMREMGenerator, Scene,
  SRGBColorSpace, Vector3, WebGLRenderer } from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { buildModel } from './src/scripts/hall/models.ts';

window.renderTurntable = async (id, frames, size, glbBase64) => {
  const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(size, size * 0.75, false);
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.setClearColor(0x14100e, 1);
  const scene = new Scene();
  scene.environment = new PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;
  const key = new DirectionalLight(0xffffff, 2.4);
  key.position.set(3, 6, 4);
  scene.add(key);
  let obj = buildModel(id);
  if (glbBase64) {
    const bytes = Uint8Array.from(atob(glbBase64), (c) => c.charCodeAt(0));
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    obj = (await loader.parseAsync(bytes.buffer, '')).scene;
  }
  const box = new Box3().setFromObject(obj);
  obj.position.sub(box.getCenter(new Vector3()));
  const pivot = new Group();
  pivot.add(obj);
  const s = box.getSize(new Vector3());
  pivot.scale.setScalar(4 / Math.max(s.x, s.y, s.z));
  const holder = new Group();
  holder.rotation.x = 0.35;
  holder.add(pivot);
  scene.add(holder);
  const camera = new PerspectiveCamera(30, 4 / 3, 0.1, 100);
  camera.position.set(0, 0, 9);
  const out = [];
  for (let i = 0; i < frames; i++) {
    holder.rotation.y = (i / frames) * Math.PI * 2;
    renderer.render(scene, camera);
    out.push(renderer.domElement.toDataURL('image/png'));
  }
  renderer.dispose();
  return out;
};
`;

const bundle = await build({
  stdin: { contents: harness, resolveDir: process.cwd(), loader: 'js' },
  bundle: true,
  format: 'iife',
  write: false,
  minify: true,
});

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge' });
const page = await browser.newPage();
await page.setContent('<!doctype html><body></body>');
await page.addScriptTag({ content: bundle.outputFiles[0].text });

const glbFor = (id) => {
  const path = `public/models/${id}.glb`;
  return existsSync(path) ? readFileSync(path).toString('base64') : null;
};

for (const id of IDS) {
  const urls = await page.evaluate(
    ([i, f, s, g]) => window.renderTurntable(i, f, s, g),
    [id, FRAMES, SIZE, glbFor(id)],
  );
  const h = Math.round(SIZE * 0.75);
  const frames = urls.map((u, i) => ({
    input: Buffer.from(u.split(',')[1], 'base64'),
    left: i * SIZE,
    top: 0,
  }));
  const info = await sharp({
    create: { width: SIZE * FRAMES, height: h, channels: 3, background: '#14100e' },
  })
    .composite(frames)
    .avif({ quality: 50 })
    .toFile(`${OUT}/${id}-sprite.avif`);
  console.log(`hall/${id}-sprite.avif ${SIZE * FRAMES}x${h} ${(info.size / 1024).toFixed(1)} KB`);
}
await browser.close();

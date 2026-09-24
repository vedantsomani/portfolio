// Three.js stage for the hardware hall. Loaded lazily by ./index.ts, never in an initial chunk.
// One renderer for the hall; one key light plus a room environment; matte materials, no bloom.
// Drag rotates with damped inertia; after 1.2 s idle the object turns at 6°/s. The wheel is left
// alone so the page scrolls. Switching objects: the current one scales 1 → 0.85 and fades while
// the next rotates in from −30°, 500 ms.
import {
  Box3,
  DirectionalLight,
  Group,
  Mesh,
  PerspectiveCamera,
  PMREMGenerator,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
  type Material,
  type Object3D,
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { buildModel } from './models';
import type { HallStage, StageOptions } from './index';

const IDLE_SPEED = (6 * Math.PI) / 180; // rad/s
const IDLE_AFTER = 1.2; // s
const SWITCH = 0.5; // s
const TILT = -0.35; // rad, a three-quarter view from above

async function loadGLB(url: string): Promise<Object3D> {
  const [{ GLTFLoader }, { MeshoptDecoder }] = await Promise.all([
    import('three/examples/jsm/loaders/GLTFLoader.js'),
    import('three/examples/jsm/libs/meshopt_decoder.module.js'),
  ]);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  return (await loader.loadAsync(url)).scene;
}

// Centre on the origin and scale so every object fills the stage the same way.
function normalise(obj: Object3D): Group {
  const box = new Box3().setFromObject(obj);
  const size = box.getSize(new Vector3());
  const centre = box.getCenter(new Vector3());
  obj.position.sub(centre);
  const pivot = new Group();
  pivot.add(obj);
  pivot.scale.setScalar(4 / Math.max(size.x, size.y, size.z));
  return pivot;
}

const materials = (obj: Object3D) => {
  const list: Material[] = [];
  obj.traverse((o) => {
    const m = (o as Mesh).material;
    if (m) list.push(...(Array.isArray(m) ? m : [m]));
  });
  return list;
};

function setOpacity(obj: Object3D, opacity: number) {
  for (const m of materials(obj)) {
    m.transparent = opacity < 1;
    m.opacity = opacity;
  }
}

const ease = (t: number) => 1 - Math.pow(1 - t, 3);

export async function createStage(
  el: HTMLElement,
  ids: string[],
  opts: StageOptions,
): Promise<HallStage> {
  const renderer = new WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'low-power',
    // Keeps the last frame readable for screenshots (QA and scripts/hall-sprites.mjs).
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = SRGBColorSpace;
  const canvas = renderer.domElement;
  canvas.className = 'hall__canvas';
  canvas.setAttribute('aria-hidden', 'true');

  const scene = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  const envMap = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envMap;
  scene.environmentIntensity = 0.55;
  const key = new DirectionalLight(0xffffff, 2.4);
  key.position.set(3, 6, 4);
  scene.add(key);

  const camera = new PerspectiveCamera(30, 1, 0.1, 100);
  camera.position.set(0, 0, 9);

  const objects = await Promise.all(
    ids.map(async (id) =>
      normalise(opts.glb.includes(id) ? await loadGLB(`/models/${id}.glb`) : buildModel(id)),
    ),
  );
  const holders = objects.map((obj) => {
    const h = new Group();
    h.rotation.x = -TILT;
    h.add(obj);
    h.visible = false;
    scene.add(h);
    return h;
  });

  let current = 0;
  let angle = 0.6;
  let velocity = 0;
  let idle = IDLE_AFTER;
  let switching: { from: number; to: number; t: number } | null = null;
  let raf = 0;
  let last = 0;
  let onScreen = true;
  let dragging = false;
  let lastX = 0;
  let rotated = new Set<number>();

  holders[current].visible = true;

  function resize() {
    const { width, height } = el.getBoundingClientRect();
    renderer.setSize(Math.max(1, width), Math.max(1, height), false);
    camera.aspect = Math.max(1, width) / Math.max(1, height);
    camera.updateProjectionMatrix();
  }

  function frame(now: number) {
    raf = 0;
    if (!onScreen || document.hidden) return;
    const dt = Math.min(0.05, last ? (now - last) / 1000 : 1 / 60);
    last = now;

    if (!dragging) {
      angle += velocity * dt;
      velocity *= Math.exp(-dt * 3);
      idle += dt;
      if (idle > IDLE_AFTER && !opts.reduce) angle += IDLE_SPEED * dt;
    }

    if (switching) {
      switching.t += dt / SWITCH;
      const t = Math.min(1, switching.t);
      const out = holders[switching.from].children[0];
      const inn = holders[switching.to].children[0];
      const k = ease(t);
      holders[switching.from].scale.setScalar(1 - 0.15 * k);
      setOpacity(out, 1 - k);
      holders[switching.to].rotation.y = angle - (Math.PI / 6) * (1 - k);
      setOpacity(inn, k);
      if (t >= 1) {
        holders[switching.from].visible = false;
        holders[switching.from].scale.setScalar(1);
        setOpacity(out, 1);
        switching = null;
      }
    }
    holders[current].rotation.y = switching ? holders[current].rotation.y : angle;

    renderer.render(scene, camera);
    raf = requestAnimationFrame(frame);
  }

  const wake = () => {
    if (!raf) {
      last = 0;
      raf = requestAnimationFrame(frame);
    }
  };

  const noteRotate = () => {
    if (!rotated.has(current)) {
      rotated.add(current);
      opts.onRotate(ids[current]);
    }
  };

  const onDown = (e: PointerEvent) => {
    dragging = true;
    lastX = e.clientX;
    velocity = 0;
    canvas.setPointerCapture(e.pointerId);
  };
  const onMove = (e: PointerEvent) => {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    lastX = e.clientX;
    const delta = dx * 0.01;
    angle += delta;
    velocity = delta * 60;
    idle = 0;
    noteRotate();
    wake();
  };
  const onUp = () => {
    dragging = false;
    idle = 0;
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const step = (e.key === 'ArrowLeft' ? -1 : 1) * (Math.PI / 12);
    if (opts.reduce) angle += step;
    else velocity += step * 3;
    idle = 0;
    noteRotate();
    wake();
  };
  canvas.addEventListener('pointerdown', onDown);
  canvas.addEventListener('pointermove', onMove);
  canvas.addEventListener('pointerup', onUp);
  canvas.addEventListener('pointercancel', onUp);
  el.addEventListener('keydown', onKey);

  const io = new IntersectionObserver(([entry]) => {
    onScreen = entry.isIntersecting;
    wake();
  });
  io.observe(el);
  const ro = new ResizeObserver(resize);
  ro.observe(el);
  const onVisibility = () => wake();
  document.addEventListener('visibilitychange', onVisibility);

  resize();
  el.prepend(canvas);
  wake();

  return {
    show(i: number) {
      if (i === current) return;
      const from = current;
      current = i;
      holders[i].visible = true;
      if (opts.reduce) {
        holders[from].visible = false;
        holders[i].rotation.y = angle;
      } else {
        switching = { from, to: i, t: 0 };
      }
      wake();
    },
    dispose() {
      cancelAnimationFrame(raf);
      io.disconnect();
      ro.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      el.removeEventListener('keydown', onKey);
      scene.traverse((o) => {
        const mesh = o as Mesh;
        mesh.geometry?.dispose();
        for (const m of materials(o)) m.dispose();
      });
      envMap.dispose();
      pmrem.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
      rotated = new Set();
    },
  };
}

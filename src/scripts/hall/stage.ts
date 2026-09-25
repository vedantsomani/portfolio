// Three.js stage for the hardware hall. Loaded lazily by ./index.ts, never in an initial chunk.
// One renderer for the hall; one key light plus a room environment; matte materials, no bloom.
// Drag rotates with damped inertia; after 1.2 s idle the object turns at 6°/s. The wheel is left
// alone so the page scrolls. Switching objects: the current one scales 1 → 0.85 and fades while
// the next rotates in from −30°, 500 ms.
// Guided views (Saarthi only, and only from the real GLB): focus(view) eases the camera to a pose
// that shows one part group, outlines those parts on the model, and places HTML labels over the
// canvas. Positions come from the KiCad file (src/data/saarthi-board.ts); the GLB shares its origin,
// so board millimetre (x, y) is model metre (x / 1000, z / 1000).
import {
  Box3,
  MeshBasicMaterial,
  PlaneGeometry,
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
import { PARTS, type BoardGroup } from '../../data/saarthi-board';
import type { HallStage, StageOptions } from './index';

const IDLE_SPEED = (6 * Math.PI) / 180; // rad/s
const IDLE_AFTER = 1.2; // s
const SWITCH = 0.5; // s
const TILT = -0.35; // rad, a three-quarter view from above
const EASE_T = 0.12; // s time constant for view moves: settles in ~400 ms
const MARK_Y = 0.0032; // m above the board's underside: clears the tallest part in each group
const BG = 0x14100e;

export type ViewId = 'overview' | BoardGroup;

// Camera pose per view: tilt (0 = edge-on, π/2 = top-down), camera distance in normalised units,
// and the board point (mm) to centre. Overview keeps the three-quarter turntable.
const POSES: Record<ViewId, { tilt: number; dist: number; focus: [number, number] | null }> = {
  overview: { tilt: -TILT, dist: 9, focus: null },
  flight: { tilt: 1.1, dist: 4, focus: [44, 68] },
  safety: { tilt: 1.1, dist: 5.8, focus: [70, 91] },
  sensors: { tilt: 1.15, dist: 3.6, focus: [64, 55] },
};

// A dark frame (0.9 mm, as meshes: WebGL lines are always 1 px) and a dark tint for each part, in
// GLB space, hidden until its group is shown. Dark reads on the board's light solder mask.
const FRAME = 0.0009; // m
function buildMarks(): Map<BoardGroup, Group> {
  const groups = new Map<BoardGroup, Group>();
  const tint = new MeshBasicMaterial({
    color: BG,
    transparent: true,
    opacity: 0.28,
    depthTest: false,
    depthWrite: false,
  });
  const edge = new MeshBasicMaterial({ color: BG, depthTest: false, depthWrite: false });
  const flat = (w: number, h: number, x: number, z: number, material: MeshBasicMaterial) => {
    const m = new Mesh(new PlaneGeometry(w, h), material);
    m.rotation.x = -Math.PI / 2;
    m.position.set(x, MARK_Y, z);
    m.renderOrder = material === edge ? 11 : 10;
    return m;
  };
  for (const p of PARTS) {
    let g = groups.get(p.group);
    if (!g) {
      g = new Group();
      g.visible = false;
      groups.set(p.group, g);
    }
    const [cx, cz, w, h] = [p.x / 1000, p.y / 1000, p.w / 1000 + FRAME * 2, p.h / 1000 + FRAME * 2];
    g.add(
      flat(w, h, cx, cz, tint),
      flat(w, FRAME, cx, cz - h / 2, edge),
      flat(w, FRAME, cx, cz + h / 2, edge),
      flat(FRAME, h, cx - w / 2, cz, edge),
      flat(FRAME, h, cx + w / 2, cz, edge),
    );
  }
  return groups;
}

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

  // Guided views need the real board: its GLB shares the KiCad origin the part positions use.
  const guidedIndex = opts.glb.includes('saarthi') ? ids.indexOf('saarthi') : -1;
  let guidedRaw: Object3D | null = null;
  const marks = buildMarks();
  const objects = await Promise.all(
    ids.map(async (id, i) => {
      const raw = opts.glb.includes(id) ? await loadGLB(`/models/${id}.glb`) : buildModel(id);
      if (i === guidedIndex) {
        guidedRaw = raw;
        marks.forEach((g) => raw.add(g));
      }
      return normalise(raw);
    }),
  );

  // HTML labels over the canvas, one per part, shown with their group.
  const labelLayer = el.querySelector<HTMLElement>('[data-hall-labels]');
  const labels = PARTS.map((p) => {
    const span = document.createElement('span');
    span.className = `hall__label hall__label--${p.la}`;
    span.textContent = p.label;
    span.hidden = true;
    labelLayer?.append(span);
    return { part: p, span, at: new Vector3(p.lx / 1000, MARK_Y, p.ly / 1000) };
  });
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
  // View state: current values ease toward the active pose.
  let view: ViewId = 'overview';
  let tilt = -TILT;
  let dist = 9;
  let easingAngle = false;
  const camTarget = new Vector3();
  const goal = new Vector3();
  const scratch = new Vector3();

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
      if (view === 'overview' && idle > IDLE_AFTER && !opts.reduce) angle += IDLE_SPEED * dt;
    }

    // Ease toward the active view's pose (instant under reduced motion).
    const pose = POSES[view];
    const k = opts.reduce ? 1 : 1 - Math.exp(-dt / EASE_T);
    if (easingAngle) {
      angle += (0 - angle) * k;
      if (Math.abs(angle) < 0.001) easingAngle = false;
    }
    tilt += (pose.tilt - tilt) * k;
    dist += (pose.dist - dist) * k;
    holders[current].rotation.x = tilt;

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

    // Centre the camera on the view's focus point, wherever the rotation has carried it.
    scene.updateMatrixWorld();
    goal.set(0, 0, 0);
    if (pose.focus && guidedRaw) {
      goal.set(pose.focus[0] / 1000, MARK_Y, pose.focus[1] / 1000);
      goal.applyMatrix4((guidedRaw as Object3D).matrixWorld);
    }
    camTarget.lerp(goal, k);
    camera.position.set(camTarget.x, camTarget.y, camTarget.z + dist);
    camera.lookAt(camTarget);
    camera.updateMatrixWorld();

    renderer.render(scene, camera);
    placeLabels();
    raf = requestAnimationFrame(frame);
  }

  // Project each visible label's anchor onto the canvas.
  function placeLabels() {
    if (!guidedRaw || !labelLayer) return;
    const { width, height } = el.getBoundingClientRect();
    for (const l of labels) {
      if (l.span.hidden) continue;
      scratch
        .copy(l.at)
        .applyMatrix4((guidedRaw as Object3D).matrixWorld)
        .project(camera);
      const x = ((scratch.x + 1) / 2) * width;
      const y = ((1 - scratch.y) / 2) * height;
      l.span.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    }
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
    easingAngle = false;
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
    easingAngle = false;
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
    focus(next: string) {
      if (!guidedRaw || current !== guidedIndex || !(next in POSES)) return false;
      view = next as ViewId;
      // Turn the board square to the viewer by the shortest way round, then hold it there.
      angle = Math.atan2(Math.sin(angle), Math.cos(angle));
      easingAngle = view !== 'overview';
      velocity = 0;
      idle = 0;
      marks.forEach((g, group) => (g.visible = group === view));
      labels.forEach((l) => (l.span.hidden = l.part.group !== view));
      wake();
      return true;
    },
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
      labels.forEach((l) => l.span.remove());
      rotated = new Set();
    },
  };
}

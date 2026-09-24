// X-ray lens controller (03_PHASE3_MOTION §1). Picks a mode and drives it:
//   gl      OGL shader (./gl.ts, loaded on idle): velocity radius, decaying trail, noise edge, rim
//   css     stacked images, radial-gradient mask on the x-ray (no WebGL, low-end, or saveData)
//   toggle  reduced motion: no lens, a "Show circuit layout" button that cuts between the layers
// Touch screens get one scripted Lissajous pass, then the lens settles centre-right at 60% radius;
// a horizontal drag moves it while vertical scrolling stays native (touch-action: pan-y).
import { track } from '../../lib/track';

export interface Lens {
  activate(): void;
  destroy(): void;
}

export interface LensFrame {
  x: number; // CSS px from the stage's left
  y: number; // CSS px from the stage's top
  r: number; // radius in CSS px
  dt: number; // seconds since the last frame
  time: number; // seconds since start
}

export interface LensRenderer {
  render(frame: LensFrame): void;
  resize(): void;
  dispose(): void;
}

const LERP = 0.12; // per 60 Hz frame, made frame-rate independent below
const REST_RADIUS = 140; // px at a ~860 px wide stage
const MAX_VEL_SCALE = 1.6;
const RELAX = 0.2; // s time constant: back to rest in ~600 ms
const PASS = 2.4; // s scripted pass on touch

const noop: Lens = { activate() {}, destroy() {} };

function loadXray(picture: HTMLElement): HTMLImageElement | null {
  picture.querySelectorAll<HTMLElement>('[data-srcset]').forEach((el) => {
    el.setAttribute('srcset', el.dataset.srcset ?? '');
    el.removeAttribute('data-srcset');
  });
  return picture.querySelector('img');
}

function initToggle(fig: HTMLElement, xray: HTMLElement): Lens {
  const toggle = fig.querySelector<HTMLButtonElement>('[data-lens-toggle]');
  if (!toggle) return noop;
  toggle.hidden = false;
  const onClick = () => {
    const on = toggle.getAttribute('aria-pressed') !== 'true';
    if (on) loadXray(xray);
    toggle.setAttribute('aria-pressed', String(on));
    xray.hidden = !on;
    fig.classList.toggle('lens--xray', on);
  };
  toggle.addEventListener('click', onClick);
  return {
    activate() {},
    destroy: () => toggle.removeEventListener('click', onClick),
  };
}

export function initLens(root: HTMLElement, reduce: boolean): Lens {
  const figEl = root.querySelector<HTMLElement>('[data-lens]');
  const stageEl = figEl?.querySelector<HTMLElement>('[data-lens-stage]');
  const photoEl = figEl?.querySelector<HTMLImageElement>('[data-lens-photo]');
  const xrayEl = figEl?.querySelector<HTMLElement>('[data-lens-xray]');
  const ringEl = figEl?.querySelector<HTMLElement>('[data-lens-ring]');
  if (!figEl || !stageEl || !photoEl || !xrayEl || !ringEl) return noop;
  if (reduce) return initToggle(figEl, xrayEl);
  // Narrowed once, so the closures below keep the non-null types.
  const [fig, stage, photo, xray, ring] = [figEl, stageEl, photoEl, xrayEl, ringEl];

  const nav = navigator as Navigator & { connection?: { saveData?: boolean } };
  const lowEnd = (navigator.hardwareConcurrency ?? 8) <= 4 || Boolean(nav.connection?.saveData);
  const touch = matchMedia('(hover: none)').matches;

  let renderer: LensRenderer | null = null;
  let destroyed = false;
  let started = false;
  let raf = 0;
  let last = 0;
  let clock = 0;
  let onScreen = true;
  let used = false;

  // Lens state: target (pointer or script) → smoothed position.
  const target = { x: 0, y: 0 };
  const pos = { x: 0, y: 0 };
  let presence = 0; // 0 hidden → 1 fully open
  let presenceTarget = 0;
  let velScale = 1;
  let restScale = 1; // 0.6 once the touch pass settles
  let pass: { t: number } | null = null;
  let lastTarget = { x: 0, y: 0 };

  const size = () => stage.getBoundingClientRect();
  const baseRadius = () => REST_RADIUS * Math.min(1.25, Math.max(0.75, size().width / 860));

  function frame(now: number) {
    raf = 0;
    if (destroyed || !onScreen || document.hidden) return;
    const dt = Math.min(0.05, last ? (now - last) / 1000 : 1 / 60);
    last = now;
    clock += dt;
    const { width: w, height: h } = size();

    if (pass) {
      // Lissajous 3:2 across the board, then glide to the rest point.
      pass.t += dt;
      const p = Math.min(1, pass.t / PASS);
      const a = p * Math.PI * 2;
      const fade = 1 - p * p;
      const rest = { x: w * 0.68, y: h * 0.5 };
      target.x = rest.x + fade * (w * 0.5 + w * 0.36 * Math.sin(a * 1.5) - rest.x);
      target.y = rest.y + fade * (h * 0.5 + h * 0.32 * Math.sin(a) - rest.y);
      restScale = 1 - 0.4 * p;
      if (p >= 1) pass = null;
    }

    const k = 1 - Math.pow(1 - LERP, dt * 60);
    pos.x += (target.x - pos.x) * k;
    pos.y += (target.y - pos.y) * k;
    presence += (presenceTarget - presence) * (1 - Math.exp(-dt / 0.08));

    // Radius grows with pointer speed (up to 1.6×) and relaxes back over ~600 ms.
    const speed = Math.hypot(target.x - lastTarget.x, target.y - lastTarget.y) / dt;
    lastTarget = { ...target };
    const wanted = 1 + (MAX_VEL_SCALE - 1) * Math.min(1, speed / 2200);
    velScale = Math.max(wanted, 1 + (velScale - 1) * Math.exp(-dt / RELAX));

    const r = baseRadius() * restScale * velScale * presence;
    if (renderer) renderer.render({ x: pos.x, y: pos.y, r, dt, time: clock });
    else {
      xray.style.setProperty('--x', `${pos.x}px`);
      xray.style.setProperty('--y', `${pos.y}px`);
      xray.style.setProperty('--r', `${r}px`);
    }
    if (!touch) {
      ring.style.transform = `translate(${pos.x}px, ${pos.y}px) scale(${Math.max(0.001, presence)})`;
    }
    raf = requestAnimationFrame(frame);
  }

  const wake = () => {
    if (!raf && started && !destroyed) {
      last = 0;
      raf = requestAnimationFrame(frame);
    }
  };

  const local = (e: PointerEvent) => {
    const rect = size();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const onMove = (e: PointerEvent) => {
    if (!started) return;
    const p = local(e);
    target.x = p.x;
    target.y = p.y;
    if (e.pointerType === 'mouse' || pass === null) presenceTarget = 1;
    if (e.pointerType !== 'mouse') {
      pass = null;
      restScale = 0.6;
    }
    if (!used) {
      used = true;
      track('hero_lens_used');
    }
    wake();
  };
  const onEnter = (e: PointerEvent) => {
    if (e.pointerType !== 'mouse' || !started) return;
    const p = local(e);
    // Open where the pointer is, not from wherever the lens last was.
    if (presence < 0.05) Object.assign(pos, p);
    presenceTarget = 1;
    wake();
  };
  const onLeave = (e: PointerEvent) => {
    if (e.pointerType === 'mouse') presenceTarget = 0;
  };

  stage.addEventListener('pointermove', onMove);
  stage.addEventListener('pointerenter', onEnter);
  stage.addEventListener('pointerleave', onLeave);

  const io = new IntersectionObserver(([entry]) => {
    onScreen = entry.isIntersecting;
    wake();
  });
  io.observe(stage);
  const onVisibility = () => wake();
  document.addEventListener('visibilitychange', onVisibility);
  const ro = new ResizeObserver(() => renderer?.resize());
  ro.observe(stage);

  async function start() {
    if (destroyed) return;
    const xrayImg = loadXray(xray);
    if (!lowEnd && xrayImg) {
      try {
        const { createGLLens } = await import('./gl');
        renderer = await createGLLens(stage, photo, xrayImg);
      } catch (err) {
        if (import.meta.env.DEV) console.warn('[lens] WebGL unavailable, CSS fallback', err);
        renderer = null;
      }
    }
    if (destroyed) {
      renderer?.dispose();
      return;
    }
    if (!renderer) {
      xray.hidden = false;
      fig.classList.add('lens--css');
    }
    fig.classList.add('lens--live');
    started = true;
    const { width: w, height: h } = size();
    Object.assign(pos, { x: w * 0.5, y: h * 0.5 });
    Object.assign(target, pos);
    if (touch) {
      pass = { t: 0 };
      presenceTarget = 1;
    }
    wake();
  }

  return {
    activate() {
      const idle = window.requestIdleCallback ?? ((cb: () => void) => setTimeout(cb, 200));
      idle(() => void start());
    },
    destroy() {
      destroyed = true;
      cancelAnimationFrame(raf);
      io.disconnect();
      ro.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      stage.removeEventListener('pointermove', onMove);
      stage.removeEventListener('pointerenter', onEnter);
      stage.removeEventListener('pointerleave', onLeave);
      renderer?.dispose();
      renderer = null;
    },
  };
}

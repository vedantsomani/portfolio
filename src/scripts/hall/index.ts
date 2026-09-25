// Hardware hall controller: in the initial bundle, but tiny. Three.js (./stage.ts) is imported
// only when the hall is within one viewport. If WebGL fails, a 24-frame AVIF turntable sprite
// (public/hall/<id>-sprite.avif, made by scripts/hall-sprites.mjs) is scrubbed by drag instead.
// If neither works the hall stays the plain list it is without JS.
import { track } from '../../lib/track';
import { reducedMotion } from '../lifecycle';

export interface HallStage {
  show(index: number): void;
  /** Guided view ('overview', 'flight', 'safety', 'sensors'). false: this stage can't show it. */
  focus?(view: string): boolean;
  dispose(): void;
}

export interface StageOptions {
  glb: string[];
  reduce: boolean;
  onRotate(id: string): void;
}

const FRAMES = 24;

function createSpriteStage(el: HTMLElement, ids: string[], onRotate: (id: string) => void) {
  const sprite = document.createElement('div');
  sprite.className = 'hall__sprite';
  sprite.setAttribute('aria-hidden', 'true');
  el.prepend(sprite);
  let current = 0;
  let frame = 0;
  let startX = 0;
  let startFrame = 0;
  let dragging = false;
  const paint = () => {
    sprite.style.backgroundImage = `url(/hall/${ids[current]}-sprite.avif)`;
    sprite.style.backgroundPositionX = `${(frame / (FRAMES - 1)) * 100}%`;
  };
  const onDown = (e: PointerEvent) => {
    dragging = true;
    startX = e.clientX;
    startFrame = frame;
    sprite.setPointerCapture(e.pointerId);
  };
  const onMove = (e: PointerEvent) => {
    if (!dragging) return;
    frame = (((startFrame + Math.round((e.clientX - startX) / 12)) % FRAMES) + FRAMES) % FRAMES;
    onRotate(ids[current]);
    paint();
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    frame = (frame + (e.key === 'ArrowLeft' ? -1 : 1) + FRAMES) % FRAMES;
    onRotate(ids[current]);
    paint();
  };
  const onUp = () => (dragging = false);
  sprite.addEventListener('pointerdown', onDown);
  sprite.addEventListener('pointermove', onMove);
  sprite.addEventListener('pointerup', onUp);
  el.addEventListener('keydown', onKey);
  paint();
  return {
    show(i: number) {
      current = i;
      paint();
    },
    dispose() {
      el.removeEventListener('keydown', onKey);
      sprite.remove();
    },
  } satisfies HallStage;
}

export function initHall(root: HTMLElement): () => void {
  const stageQ = root.querySelector<HTMLElement>('[data-hall-stage]');
  const items = [...root.querySelectorAll<HTMLElement>('[data-hall-item]')];
  const controlsQ = root.querySelector<HTMLElement>('[data-hall-controls]');
  const prev = root.querySelector<HTMLButtonElement>('[data-hall-prev]');
  const next = root.querySelector<HTMLButtonElement>('[data-hall-next]');
  const count = root.querySelector<HTMLElement>('[data-hall-count]');
  if (!stageQ || !items.length || !controlsQ || !prev || !next || !count) return () => {};
  // Narrowed once, so the closures below keep the non-null types.
  const stageEl = stageQ;

  const ids = items.map((li) => li.dataset.hallItem ?? '');
  const glb = items
    .filter((li) => li.dataset.glb !== undefined)
    .map((li) => li.dataset.hallItem ?? '');
  const onRotate = (id: string) => track('hall_object_rotate', { object: id });
  let stage: HallStage | null = null;
  let destroyed = false;
  let index = 0;

  const show = (i: number) => {
    index = (i + items.length) % items.length;
    items.forEach((li, k) => (li.hidden = k !== index));
    count.textContent = `${index + 1} / ${items.length}`;
    stageEl.setAttribute(
      'aria-label',
      `${items[index].querySelector('h3')?.textContent ?? ''}, rotatable view. Drag or use the arrow keys to rotate.`,
    );
    stage?.show(index);
  };
  const onPrev = () => show(index - 1);
  const onNext = () => show(index + 1);

  // Guided views: one explanation at a time; the 3D stage turns to it, or, without WebGL, the
  // static board map highlights it. Without JS all explanations stay visible as a list.
  const viewButtons = [...root.querySelectorAll<HTMLButtonElement>('[data-view]')];
  const viewPanels = [...root.querySelectorAll<HTMLElement>('[data-view-panel]')];
  const map = root.querySelector<SVGElement>('[data-board-map]');
  root.querySelector<HTMLElement>('.hall__view-buttons')?.removeAttribute('hidden');
  let view = 'overview';
  const applyView = () => {
    const in3d = stage?.focus?.(view) ?? false;
    // No 3D board to turn: the map explains the view (overview keeps the sprite or render).
    root.classList.toggle('hall--map', !in3d && view !== 'overview' && booted);
    if (map) map.dataset.view = view;
  };
  const setView = (next: string) => {
    view = next;
    viewButtons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.view === next)));
    viewPanels.forEach((p) => (p.hidden = p.dataset.viewPanel !== next));
    if (!booted) bootOnce();
    applyView();
  };
  const onView = (e: Event) => {
    const next = (e.currentTarget as HTMLButtonElement).dataset.view;
    if (next) setView(next);
  };
  viewButtons.forEach((b) => b.addEventListener('click', onView));
  viewPanels.forEach((p) => (p.hidden = p.dataset.viewPanel !== view));

  // The carousel works at once; the stage fills in when Three.js (or the sprite) is ready.
  root.classList.add('hall--ready');
  show(0);

  async function boot() {
    try {
      const { createStage } = await import('./stage');
      stage = await createStage(stageEl, ids, { glb, reduce: reducedMotion(), onRotate });
    } catch (err) {
      if (import.meta.env.DEV) console.warn('[hall] WebGL unavailable, sprite fallback', err);
      stage = createSpriteStage(stageEl, ids, onRotate);
    }
    if (destroyed) {
      stage.dispose();
      return;
    }
    root.classList.add('hall--live');
    stage.show(index);
    applyView();
  }

  // Boot once. A hall that is already in range at load waits for intent (hover, touch, focus, or
  // the first scroll) so Three.js and the GLB never compete with the page load; one reached by
  // scrolling boots as it comes within a viewport.
  let booted = false;
  const intents = ['pointerenter', 'pointerdown', 'focus'] as const;
  const bootOnce = () => {
    if (booted) return;
    booted = true;
    io.disconnect();
    intents.forEach((t) => stageEl.removeEventListener(t, bootOnce));
    window.removeEventListener('scroll', bootOnce);
    void boot();
  };
  let first = true;
  const io = new IntersectionObserver(
    ([entry]) => {
      const atLoad = first;
      first = false;
      if (!entry.isIntersecting) return;
      if (!atLoad) return bootOnce();
      intents.forEach((t) => stageEl.addEventListener(t, bootOnce));
      window.addEventListener('scroll', bootOnce, { once: true, passive: true });
    },
    { rootMargin: '100% 0px' },
  );
  io.observe(root);
  prev.addEventListener('click', onPrev);
  next.addEventListener('click', onNext);

  return () => {
    destroyed = true;
    io.disconnect();
    intents.forEach((t) => stageEl.removeEventListener(t, bootOnce));
    window.removeEventListener('scroll', bootOnce);
    prev.removeEventListener('click', onPrev);
    next.removeEventListener('click', onNext);
    viewButtons.forEach((b) => b.removeEventListener('click', onView));
    stage?.dispose();
  };
}

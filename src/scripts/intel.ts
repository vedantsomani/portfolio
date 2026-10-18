// The briefing's opening (BriefingIntel.astro), cut like a mission briefing, about eight seconds:
//   0.0  the frame and the title come up over the whole Earth
//   0.5  the feed falls towards the target, one image into the next (each centred on it)
//   3.9  a lock closes on the campus
//   4.5  the page's own identity card slides in as the dossier
//   5.0  three projects are pinned to the map, a line from the target to each
//   7.3  everything but the card clears, and the page is there with the card in its place
// Skip and Escape go straight to the page. Sound (ticks and static) only if it is on.
import { cue } from './sound';

const KEY = 'archive:handoff';
const EASE = 'cubic-bezier(.16,1,.3,1)';
const T = { zoom0: 0.5, zoom1: 3.9, lock: 3.9, card: 4.5, pins: 5.0, out: 7.3, gone: 8.2 };

const clamp = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => x * x * (3 - 2 * x);

export function initIntel(el: HTMLElement): () => void {
  const page = document.querySelector<HTMLElement>('.brief-page');
  const card = document.querySelector<HTMLElement>('[data-idcard]');
  const skip = el.querySelector<HTMLButtonElement>('[data-handoff-skip]');
  if (el.hidden || !page || !card) return () => {};
  const pg = page;
  const levels = [...el.querySelectorAll<HTMLElement>('[data-intel-level]')];
  const km = (el.dataset.km ?? '').split(',').map(Number);
  const alt = el.querySelector<HTMLElement>('[data-intel-alt]');
  const lock = el.querySelector<HTMLElement>('[data-intel-lock]');
  const typed = el.querySelector<HTMLElement>('[data-intel-type]');
  // Only the pins the layout shows (phones drop one).
  const pins = [...el.querySelectorAll<HTMLElement>('[data-intel-pin]')].filter(
    (p) => p.offsetParent,
  );
  const lines = el.querySelector<SVGSVGElement>('[data-intel-lines]');
  const timers: number[] = [];
  const anims: Animation[] = [];
  let raf = 0;
  let done = false;
  page.inert = true;
  try {
    sessionStorage.setItem(KEY, '1');
  } catch {
    /* private mode: the briefing may open this way again, which is harmless */
  }

  // The zoom: each level is centred on the target, and level i is at its own size when the camera
  // has zoomed km[0] / km[i] times; a level fades in over the one before as it comes up to size.
  const ratio = levels.map((_, i) => km[0] / km[i]);
  // The whole globe in frame to start, on a tall screen too (the images are squares as wide as the
  // screen's longer side).
  const z0 = 0.82 * Math.min(1, innerWidth / innerHeight) ** 0.85;
  const z1 = ratio[ratio.length - 1] * 1.3;
  const zoomAt = (t: number) => {
    const e = smooth(clamp((t - T.zoom0) / (T.zoom1 - T.zoom0)));
    return Math.exp(Math.log(z0) + (Math.log(z1) - Math.log(z0)) * e);
  };
  const altitude = (z: number) => {
    const a = (km[0] / z) * 0.9;
    return a >= 10 ? `${Math.round(a).toLocaleString('en-IN')} km` : `${a.toFixed(1)} km`;
  };
  const start = performance.now();
  const frame = () => {
    const t = (performance.now() - start) / 1000;
    const z = zoomAt(t);
    levels.forEach((lv, i) => {
      const k = z / ratio[i];
      const shown = i === 0 ? 1 : clamp((k - 0.4) / 0.5);
      const covered = i + 1 < levels.length && z / ratio[i + 1] > 0.95;
      lv.style.transform = `scale(${k})`;
      lv.style.opacity = String(shown);
      lv.style.visibility = covered ? 'hidden' : 'visible';
    });
    if (alt) alt.textContent = altitude(z);
    if (!done && t < T.out) raf = requestAnimationFrame(frame);
  };
  raf = requestAnimationFrame(frame);

  const at = (s: number, fn: () => void) => timers.push(window.setTimeout(fn, s * 1000));
  const play = (node: Element | null, keys: Keyframe[], opts: KeyframeAnimationOptions) => {
    if (!node) return;
    anims.push(node.animate(keys, { fill: 'both', ...opts }));
  };

  // The title types itself.
  if (typed) {
    const name = typed.textContent ?? '';
    typed.textContent = '';
    name.split('').forEach((ch, i) => at(0.35 + i * 0.045, () => (typed.textContent += ch)));
  }
  at(0.05, () => cue('static'));
  at(T.lock, () => {
    cue('tick');
    play(
      lock,
      [
        { opacity: 0, transform: 'scale(2.6)' },
        { opacity: 1, transform: 'scale(1)' },
      ],
      { duration: 520, easing: EASE },
    );
  });
  // The dossier: the real card, above the map, into its own place; the title gives way to it.
  at(T.card, () => {
    cue('static');
    play(el.querySelector('[data-intel-title]'), [{ opacity: 1 }, { opacity: 0 }], {
      duration: 400,
      easing: 'ease-out',
    });
    play(
      card,
      [
        { opacity: 0, transform: 'translateX(14vw) scale(.94)' },
        { opacity: 1, transform: 'none' },
      ],
      { duration: 760, easing: EASE },
    );
  });
  // The pins, each with a line drawn from the target.
  pins.forEach((pin, i) =>
    at(T.pins + i * 0.38, () => {
      cue('tick');
      play(
        pin,
        [
          { opacity: 0, transform: 'translateY(12px)' },
          { opacity: 1, transform: 'none' },
        ],
        { duration: 480, easing: EASE },
      );
      if (!lines) return;
      const r = pin.getBoundingClientRect();
      const ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      const len = Math.hypot(r.left - innerWidth / 2, r.top + r.height / 2 - innerHeight / 2);
      ln.setAttribute('x1', String(innerWidth / 2));
      ln.setAttribute('y1', String(innerHeight / 2));
      ln.setAttribute('x2', String(r.left));
      ln.setAttribute('y2', String(r.top + r.height / 2));
      ln.style.strokeDasharray = String(len);
      lines.append(ln);
      play(ln, [{ strokeDashoffset: len }, { strokeDashoffset: 0 }], {
        duration: 420,
        easing: 'ease-out',
      });
    }),
  );
  at(T.out, () => finish(true));

  function finish(slow: boolean) {
    if (done) return;
    done = true;
    cancelAnimationFrame(raf);
    timers.forEach(clearTimeout);
    const end = () => {
      el.hidden = true;
      // The card has made its entrance: its own on-arrival animation must not run again.
      document.documentElement.classList.add('intel-done');
      document.documentElement.classList.remove('intel-on');
      for (const a of anims) a.cancel();
      pg.inert = false;
      // Reading starts at the name.
      const name = document.getElementById('brief-name');
      if (name) {
        name.tabIndex = -1;
        name.focus({ preventScroll: true });
      }
    };
    // The card must be in its place before the cover goes: a skip lands it at once.
    if (!slow) {
      const entered = anims.some((a) => (a.effect as KeyframeEffect | null)?.target === card);
      for (const a of anims) a.finish();
      if (!entered) play(card, [{ opacity: 0 }, { opacity: 1 }], { duration: 260 });
    }
    el.animate([{ opacity: 1 }, { opacity: 0 }], {
      duration: slow ? (T.gone - T.out) * 1000 : 260,
      easing: 'ease-in-out',
      fill: 'forwards',
    }).finished.then(end, end);
  }

  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') finish(false);
  };
  const onSkip = () => finish(false);
  skip?.addEventListener('click', onSkip);
  document.addEventListener('keydown', onKey);
  skip?.focus({ preventScroll: true });

  return () => {
    done = true;
    cancelAnimationFrame(raf);
    timers.forEach(clearTimeout);
    skip?.removeEventListener('click', onSkip);
    document.removeEventListener('keydown', onKey);
    for (const a of anims) a.cancel();
    page.inert = false;
    document.documentElement.classList.remove('intel-on');
  };
}

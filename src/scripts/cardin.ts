// The briefing's opening (BriefingCard.astro), about five seconds, like a game's mission dossier:
//   0.0  the room goes dark, "Incoming dossier" types itself
//   0.35 the page's own ID card comes in from the side of the screen, spinning over and over,
//        slowing as it comes, and lands face up in the middle (light runs over it as it turns,
//        the laminate glints, its shadow lengthens as it lifts towards us)
//   1.75 it settles with a little give, then it is read: a scan runs down it, brackets lock on the
//        photo, "Verified" comes up, the name decodes, the fields come in
//   3.9  it goes into its place on the page as the dark clears
// The card is the real element (its text stays text), moved by a transform each frame. Skip and
// Escape go straight to the page. Sound (ticks and static) only if it is on.
import { cue } from './sound';

const KEY = 'archive:handoff';
const T = {
  in: 0.35,
  land: 1.75,
  scan: 1.95,
  lock: 2.25,
  name: 2.5,
  fields: 2.7,
  out: 3.9,
  gone: 4.75,
};
const TURNS = 3.5; // how many times it flips over on the way in

const clamp = (x: number) => Math.min(1, Math.max(0, x));
const outCubic = (x: number) => 1 - (1 - x) ** 3;
const outQuint = (x: number) => 1 - (1 - x) ** 5;
const inOut = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2);
// A spring's settle: overshoots a little, rings down.
const settle = (x: number) => (x >= 1 ? 1 : 1 - Math.exp(-6 * x) * Math.cos(9 * x));
const GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/<>';

export function initCardIn(el: HTMLElement): () => void {
  const page = document.querySelector<HTMLElement>('.brief-page');
  const card = document.querySelector<HTMLElement>('[data-idcard]');
  const skip = el.querySelector<HTMLButtonElement>('[data-handoff-skip]');
  const typed = el.querySelector<HTMLElement>('[data-cardin-type]');
  if (el.hidden || !page || !card) return () => {};
  const pg = page;
  const cd = card;
  const timers: number[] = [];
  const made: HTMLElement[] = [];
  let raf = 0;
  let done = false;
  pg.inert = true;
  try {
    sessionStorage.setItem(KEY, '1');
  } catch {
    /* private mode: the briefing may open this way again, which is harmless */
  }

  // Where the card is at rest on the page, and the pose it lands in: the middle of the screen,
  // as large as fits.
  cd.style.transform = 'none';
  const r = cd.getBoundingClientRect();
  const dx = innerWidth / 2 - (r.left + r.width / 2);
  const dy = innerHeight / 2 - (r.top + r.height / 2);
  const big = Math.min(1.45, (0.86 * innerWidth) / r.width, (0.62 * innerHeight) / r.height);
  const fromX = innerWidth / 2 + r.width * big; // off the right edge

  // What rides on the card: its back (seen when it is turned over), the light on it, the scan,
  // the photo's lock, the stamp.
  const add = (cls: string, parent: HTMLElement = cd, html = '') => {
    const n = document.createElement('div');
    n.className = cls;
    n.setAttribute('aria-hidden', 'true');
    n.innerHTML = html;
    parent.append(n);
    made.push(n);
    return n;
  };
  const back = add('cardin-back', cd, '<span>Vedant Somani</span><span>vedantsomani.tech</span>');
  const sheen = add('cardin-sheen');
  const holo = add('cardin-holo');
  const scan = add('cardin-scan');
  const photo = cd.querySelector<HTMLElement>('.idcard__photo');
  const lock = photo ? add('cardin-lock', photo, '<i></i><i></i><i></i><i></i>') : null;
  const stamp = photo ? add('cardin-stamp', photo, 'Verified') : null;
  const name = document.getElementById('brief-name');
  const fields = [...cd.querySelectorAll<HTMLElement>('.idcard__fields > div, .idcard__focus')];
  fields.forEach((f) => (f.style.opacity = '0'));

  const start = performance.now();
  let lastSide = 1;
  const frame = () => {
    const t = (performance.now() - start) / 1000;
    // In: across from the side, spinning about its upright axis, slowing as it comes.
    const k = clamp((t - T.in) / (T.land - T.in));
    const travel = outCubic(k);
    const spin = (1 - outQuint(k)) * TURNS * 360; // degrees still to turn
    const s = settle(clamp((t - T.land) / 0.7));
    // Out: from the middle into its place.
    const o = inOut(clamp((t - T.out) / (T.gone - T.out - 0.1)));
    const x = (fromX * (1 - travel) + dx * travel) * (1 - o) + 0 * o;
    const y = (dy - 0.12 * innerHeight * (1 - travel) * Math.sin(Math.PI * travel)) * (1 - o);
    const tilt = -16 * (1 - travel) + 3 * (1 - s) * (t > T.land ? 1 : 0);
    const lift = 1 + 0.06 * Math.sin(Math.PI * travel); // towards us, mid-flight
    const scale = big * lift * (t > T.land ? 1 + 0.025 * (1 - s) : 1) * (1 - o) + o;
    const rx = 8 * (1 - travel) * Math.sin(t * 9);
    cd.style.transform =
      `translate(${x}px, ${y}px) perspective(1400px) rotateY(${spin}deg) rotateX(${rx}deg) ` +
      `rotateZ(${tilt}deg) scale(${scale})`;
    cd.style.opacity = t < T.in ? '0' : '1';
    // Which side faces us: past edge-on, its back.
    const a = ((spin % 360) + 360) % 360;
    const side = a > 90 && a < 270 ? -1 : 1;
    if (side !== lastSide) {
      back.style.opacity = side < 0 ? '1' : '0';
      lastSide = side;
    }
    // The light: a band that crosses the card as it turns, brightest near face-on; the laminate's
    // rainbow follows it. A little blur while it spins fast.
    const face = Math.abs(Math.cos((a * Math.PI) / 180));
    sheen.style.backgroundPosition = `${(a / 360) * 300 - 100}% 0`;
    sheen.style.opacity = String(0.55 * face * (1 - o) + (t > T.land ? 0.15 * (1 - s) : 0));
    holo.style.backgroundPosition = `${(a / 360) * 200}% ${50 + 30 * Math.sin(t * 2)}%`;
    holo.style.opacity = String(0.22 * face * (1 - outCubic(clamp((t - T.land) / 0.9))));
    const speed = (TURNS * 360 * 5 * (1 - k) ** 4) / (T.land - T.in); // deg/s, roughly
    cd.style.filter = `blur(${Math.min(1.6, speed / 900).toFixed(2)}px)`;
    cd.style.boxShadow = `0 ${30 + 50 * lift * (1 - o)}px ${60 + 80 * (lift - 1) * 10}px -30px rgb(0 0 0 / ${0.9 - 0.3 * o})`;
    if (!done && t < T.gone) raf = requestAnimationFrame(frame);
  };
  raf = requestAnimationFrame(frame);

  const at = (s: number, fn: () => void) => timers.push(window.setTimeout(fn, s * 1000));
  // The heading types itself.
  if (typed) {
    const text = typed.textContent ?? '';
    typed.textContent = '';
    text.split('').forEach((ch, i) => at(0.05 + i * 0.03, () => (typed.textContent += ch)));
  }
  at(0.05, () => cue('static'));
  at(T.in + 0.05, () => cue('static'));
  at(T.land, () => cue('tick'));
  at(T.scan, () => scan.classList.add('is-on'));
  at(T.lock, () => {
    cue('tick');
    lock?.classList.add('is-on');
    stamp?.classList.add('is-on');
  });
  // The name decodes: random glyphs settling letter by letter into the name.
  if (name) {
    const real = name.textContent ?? '';
    at(T.name, () => {
      const t0 = performance.now();
      const tick = () => {
        const p = clamp((performance.now() - t0) / 650);
        const n = Math.floor(p * real.length);
        name.textContent = real
          .split('')
          .map((ch, i) =>
            i < n || ch === ' ' ? ch : GLYPHS[Math.floor(Math.random() * GLYPHS.length)],
          )
          .join('');
        if (p < 1 && !done) requestAnimationFrame(tick);
        else name.textContent = real;
      };
      tick();
    });
  }
  fields.forEach((f, i) =>
    at(T.fields + i * 0.12, () => {
      f.animate(
        [
          { opacity: 0, transform: 'translateX(-8px)' },
          { opacity: 1, transform: 'none' },
        ],
        { duration: 320, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'forwards' },
      );
      cue('tick');
    }),
  );
  at(T.out, () => finish(true));

  function finish(slow: boolean) {
    if (done && !slow) return;
    if (!slow) done = true;
    const end = () => {
      done = true;
      cancelAnimationFrame(raf);
      timers.forEach(clearTimeout);
      el.hidden = true;
      cd.style.transform = '';
      cd.style.opacity = '';
      cd.style.filter = '';
      cd.style.boxShadow = '';
      fields.forEach((f) => {
        f.style.opacity = '';
        f.getAnimations().forEach((a) => a.cancel());
      });
      for (const n of made) n.remove();
      if (name && name.textContent !== name.dataset.real && name.dataset.real)
        name.textContent = name.dataset.real;
      document.documentElement.classList.add('cardin-done');
      document.documentElement.classList.remove('cardin-on');
      pg.inert = false;
      if (name) {
        name.tabIndex = -1;
        name.focus({ preventScroll: true });
      }
    };
    if (!slow) {
      cancelAnimationFrame(raf);
      el.animate([{ opacity: 1 }, { opacity: 0 }], {
        duration: 240,
        fill: 'forwards',
      }).finished.then(end, end);
      return;
    }
    el.animate([{ opacity: 1 }, { opacity: 0 }], {
      duration: (T.gone - T.out) * 1000,
      easing: 'ease-in-out',
      fill: 'forwards',
    }).finished.then(end, end);
  }
  if (name) name.dataset.real = name.textContent ?? '';

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
    for (const n of made) n.remove();
    cd.style.transform = '';
    cd.style.opacity = '';
    cd.style.filter = '';
    pg.inert = false;
    document.documentElement.classList.remove('cardin-on');
  };
}

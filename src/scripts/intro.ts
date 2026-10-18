// Cold open (SITE_SPEC §4.0). Gate → credits → cut to the hero. Loaded on demand, only when the
// head script armed it, so repeat visits never download it.
//   gate     veins creep in from the dark while the visitor chooses sound or silence
//   credits  each card emerges as its tracking slowly opens; a muted impact per card with sound on;
//            the veins keep growing underneath, slowly
//   circuit  on "the silicon up" the veins recede and right-angled copper traces route in from the
//            edges towards the name: the organic becomes the machine
//   cut      a short red veil with static, then the overlay dissolves into the hero
// Skip (always visible) and Escape jump to the cut. Everything else is inert while this runs, and
// focus goes to <main> afterwards.
import { cue, setSound } from './sound';

const SEEN = 'intro-seen';
const TAU = Math.PI * 2;

interface Branch {
  x: number;
  y: number;
  a: number;
  w: number;
}

function fit(canvas: HTMLCanvasElement) {
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(innerWidth * dpr);
  canvas.height = Math.round(innerHeight * dpr);
  const ctx = canvas.getContext('2d');
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}

// Organic growth: a few branches random-walk inwards from the edges, thinning and splitting now and
// then. The canvas is never cleared, so the growth accumulates. Kept sparse: negative space matters.
function veins(canvas: HTMLCanvasElement) {
  const ctx = fit(canvas);
  const w = innerWidth;
  const h = innerHeight;
  const live: Branch[] = [];
  let spawned = 0;
  const MAX = Math.round(Math.min(150, (w * h) / 9000));
  const seed = () => {
    const side = Math.floor(Math.random() * 4);
    const t = 0.1 + Math.random() * 0.8;
    const [x, y, a] =
      side === 0
        ? [t * w, -4, Math.PI / 2]
        : side === 1
          ? [w + 4, t * h, Math.PI]
          : side === 2
            ? [t * w, h + 4, -Math.PI / 2]
            : [-4, t * h, 0];
    live.push({ x, y, a: a + (Math.random() - 0.5) * 0.8, w: 1.6 + Math.random() * 2.2 });
    spawned++;
  };
  for (let i = 0; i < 6; i++) seed();

  return (dt: number, speed: number) => {
    if (!ctx) return;
    if (live.length < 3 && spawned < MAX) seed();
    const steps = Math.max(1, Math.round(speed * dt * 60));
    for (let i = live.length - 1; i >= 0; i--) {
      const b = live[i];
      const pts: [number, number][] = [[b.x, b.y]];
      for (let k = 0; k < steps; k++) {
        // Wander, with a faint pull away from the centre: the growth frames the type, never covers it.
        const toC = Math.atan2(h / 2 - b.y, w / 2 - b.x);
        const dc = Math.hypot(w / 2 - b.x, h / 2 - b.y) / Math.hypot(w / 2, h / 2);
        let d = toC - b.a;
        d = Math.atan2(Math.sin(d), Math.cos(d));
        b.a += (Math.random() - 0.5) * 0.3 + d * (dc > 0.45 ? 0.004 : -0.012);
        b.x += Math.cos(b.a) * 1.2;
        b.y += Math.sin(b.a) * 1.2;
        b.w *= 0.9965;
        pts.push([b.x, b.y]);
        if (Math.random() < 0.009 && spawned < MAX) {
          const s = Math.random() < 0.5 ? -1 : 1;
          live.push({ x: b.x, y: b.y, a: b.a + s * (0.5 + Math.random() * 0.5), w: b.w * 0.7 });
          spawned++;
        }
      }
      const stroke = (style: string, width: number) => {
        ctx.strokeStyle = style;
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(pts[0][0], pts[0][1]);
        for (const [x, y] of pts) ctx.lineTo(x, y);
        ctx.stroke();
      };
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      stroke('rgb(255 30 40 / 0.03)', b.w * 6);
      stroke('rgb(92 4 9)', b.w);
      stroke('rgb(190 24 34 / 0.5)', b.w * 0.3);
      const off = b.x < -40 || b.y < -40 || b.x > w + 40 || b.y > h + 40;
      if (b.w < 0.28 || off) live.splice(i, 1);
    }
  };
}

// Circuit: buses of three parallel traces route from the edges to a box around the name, straight
// then 45°, as a PCB router would, with a pad at each end. Redrawn each frame up to their length.
function traces(canvas: HTMLCanvasElement) {
  const ctx = fit(canvas);
  const w = innerWidth;
  const h = innerHeight;
  const half = Math.min(w * 0.36, 520);
  const box = { x0: w / 2 - half, x1: w / 2 + half, y0: h * 0.5 - 80, y1: h * 0.5 + 80 };
  type Line = { pts: [number, number][]; len: number; delay: number };
  const lines: Line[] = [];
  const GROUPS = w < 700 ? 4 : 6;
  for (let g = 0; g < GROUPS; g++) {
    const side = g % 4;
    const t = 0.18 + ((g * 0.37) % 0.64);
    const sx = side === 1 ? w + 2 : side === 3 ? -2 : t * w;
    const sy = side === 0 ? -2 : side === 2 ? h + 2 : t * h;
    const vertical = side === 0 || side === 2;
    const tx = vertical
      ? Math.min(box.x1, Math.max(box.x0, sx + (g % 2 ? 1 : -1) * w * 0.08))
      : side === 1
        ? box.x1
        : box.x0;
    const ty = vertical ? (side === 0 ? box.y0 : box.y1) : Math.min(box.y1, Math.max(box.y0, sy));
    for (let k = -1; k <= 1; k++) {
      const o = k * 8;
      const a: [number, number] = vertical ? [sx + o, sy] : [sx, sy + o];
      const b: [number, number] = vertical ? [tx + o, ty] : [tx, ty + o];
      const dx = b[0] - a[0];
      const dy = b[1] - a[1];
      const m = Math.min(Math.abs(dx), Math.abs(dy));
      const mid: [number, number] = vertical
        ? [a[0], b[1] - Math.sign(dy) * m]
        : [b[0] - Math.sign(dx) * m, a[1]];
      const pts = [a, mid, b];
      let len = 0;
      for (let i = 1; i < pts.length; i++)
        len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      lines.push({ pts, len, delay: g * 0.12 + (k + 1) * 0.04 });
    }
  }
  let t = 0;
  return (dt: number) => {
    if (!ctx) return;
    t += dt;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#ff2e3b';
    ctx.fillStyle = '#ff2e3b';
    ctx.shadowColor = 'rgb(255 46 59 / 0.7)';
    ctx.shadowBlur = 8;
    ctx.lineWidth = 1.5;
    for (const l of lines) {
      let left = Math.max(0, (t - l.delay) * 900);
      if (left <= 0) continue;
      const done = left >= l.len;
      ctx.beginPath();
      ctx.moveTo(l.pts[0][0], l.pts[0][1]);
      let end = l.pts[0];
      for (let i = 1; i < l.pts.length && left > 0; i++) {
        const [x0, y0] = l.pts[i - 1];
        const [x1, y1] = l.pts[i];
        const seg = Math.hypot(x1 - x0, y1 - y0);
        const f = Math.min(1, left / seg);
        end = [x0 + (x1 - x0) * f, y0 + (y1 - y0) * f];
        ctx.lineTo(end[0], end[1]);
        left -= seg;
      }
      ctx.stroke();
      if (done) {
        ctx.beginPath();
        ctx.arc(end[0], end[1], 3, 0, TAU);
        ctx.fill();
      }
    }
  };
}

const wait = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const id = setTimeout(resolve, ms);
    signal.addEventListener('abort', () => {
      clearTimeout(id);
      reject(new DOMException('skipped', 'AbortError'));
    });
  });

export function runIntro(): (() => void) | undefined {
  const html = document.documentElement;
  const root = document.querySelector<HTMLElement>('[data-intro-root]');
  if (!root || html.dataset.intro !== 'pending') {
    root?.remove();
    return;
  }
  const veinEl = root.querySelector<HTMLCanvasElement>('[data-intro-veins]');
  const traceEl = root.querySelector<HTMLCanvasElement>('[data-intro-traces]');
  const gateEl = root.querySelector<HTMLElement>('[data-intro-gate]');
  const skipEl = root.querySelector<HTMLButtonElement>('[data-intro-skip]');
  const cutEl = root.querySelector<HTMLElement>('[data-intro-cut]');
  if (!veinEl || !traceEl || !gateEl || !skipEl || !cutEl) {
    root.remove();
    delete html.dataset.intro;
    return;
  }
  const [overlay, veinCanvas, traceCanvas, gate, skip, cutLayer] = [
    root,
    veinEl,
    traceEl,
    gateEl,
    skipEl,
    cutEl,
  ];
  html.dataset.intro = 'gate';
  try {
    sessionStorage.setItem(SEEN, '1');
  } catch {
    /* blocked storage: the intro may play again next visit */
  }

  // Lift the overlay out of <main> and make everything else inert while it runs.
  document.body.append(overlay);
  const others = [...document.body.children].filter(
    (el): el is HTMLElement => el !== overlay && el instanceof HTMLElement && !el.inert,
  );
  others.forEach((el) => (el.inert = true));

  const cards = [...overlay.querySelectorAll<HTMLElement>('[data-intro-card]')];
  const enters = [...overlay.querySelectorAll<HTMLButtonElement>('[data-intro-enter]')];
  const growVeins = veins(veinCanvas);
  let drawTraces: ((dt: number) => void) | null = null;
  let speed = 0.5;
  let raf = 0;
  let last = 0;
  let finished = false;
  let cutting = false;
  const abort = new AbortController();

  const loop = (now: number) => {
    const dt = Math.min(0.05, last ? (now - last) / 1000 : 1 / 60);
    last = now;
    growVeins(dt, speed);
    drawTraces?.(dt);
    raf = requestAnimationFrame(loop);
  };
  raf = requestAnimationFrame(loop);
  // The gate emerges once the display face is ready (never later than 1.2 s, by CSS). Only Archivo
  // is awaited: document.fonts.ready would also wait for the mono face, which the page asks for
  // late, and hold the gate (the first paint) back for no visible reason.
  void (document.fonts?.load('300 1em Archivo') ?? Promise.resolve()).then(() =>
    overlay.classList.add('intro--ready'),
  );
  requestAnimationFrame(() => enters[0]?.focus({ preventScroll: true }));

  function finish() {
    if (finished) return;
    finished = true;
    abort.abort();
    cancelAnimationFrame(raf);
    removeEventListener('keydown', onKey);
    others.forEach((el) => (el.inert = false));
    overlay.remove();
    delete html.dataset.intro;
    document.dispatchEvent(new Event('intro:done'));
    document.getElementById('main')?.focus({ preventScroll: true });
  }

  async function cut(quick = false) {
    if (cutting) return;
    cutting = true;
    abort.abort();
    cue('static');
    cutLayer.animate([{ opacity: 0 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }], {
      duration: quick ? 240 : 520,
      easing: 'ease-out',
    });
    const out = overlay.animate([{ opacity: 1 }, { opacity: 0 }], {
      duration: quick ? 320 : 900,
      delay: quick ? 60 : 180,
      easing: 'cubic-bezier(0.7, 0, 0.84, 0)',
      fill: 'forwards',
    });
    await out.finished.catch(() => {});
    finish();
  }

  // Card: fade in while tracking opens, hold, fade out. Tracking opens over the whole hold.
  function card(el: HTMLElement, hold: number) {
    el.animate([{ '--track': '0.2em' }, { '--track': '0.42em' }] as Keyframe[], {
      duration: hold,
      easing: 'linear',
      fill: 'forwards',
    });
    el.animate(
      [
        { opacity: 0, filter: 'blur(6px)' },
        { opacity: 1, filter: 'blur(0)', offset: 0.28 },
        { opacity: 1, filter: 'blur(0)', offset: 0.8 },
        { opacity: 0, filter: 'blur(3px)' },
      ],
      { duration: hold, easing: 'ease-in-out', fill: 'forwards' },
    );
  }

  async function play() {
    html.dataset.intro = 'playing';
    gate.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 900, fill: 'forwards' });
    speed = 1.1;
    // Milliseconds on screen: presents, the three disciplines, the silicon line, the name.
    const holds = [2600, 1700, 1700, 1700, 2600, 2800];
    try {
      await wait(900, abort.signal);
      gate.remove();
      for (let i = 0; i < cards.length; i++) {
        const hold = holds[i] ?? 2000;
        cue('boom');
        card(cards[i], hold);
        if (i === cards.length - 2) {
          // The organic recedes; the circuit arrives.
          veinCanvas.animate([{ opacity: 1 }, { opacity: 0.18 }], {
            duration: 1600,
            fill: 'forwards',
            easing: 'ease-in-out',
          });
          speed = 0.3;
          drawTraces = traces(traceCanvas);
        }
        await wait(hold - 250, abort.signal);
      }
      await cut();
    } catch {
      /* skipped */
    }
  }

  const onEnter = (e: Event) => {
    setSound((e.currentTarget as HTMLElement).dataset.introEnter === 'sound');
    enters.forEach((b) => (b.disabled = true));
    skip.focus({ preventScroll: true });
    void play();
  };
  const onSkip = () => void cut(true);
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      void cut(true);
    }
  };
  enters.forEach((b) => b.addEventListener('click', onEnter));
  skip.addEventListener('click', onSkip);
  addEventListener('keydown', onKey);

  return finish;
}

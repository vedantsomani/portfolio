// The film player (Film.astro). Plays once per session after the cold open, by itself, from the
// first frame to the last; the crew's radio is subtitled as it is spoken; it ends on the title card
// and fades into the lab it ends in; Skip or Escape ends it at once. "Play the film"
// (archive:film-play) runs it again on request, reduced motion included, since then the visitor
// asked for it. While it plays the rest of the page is inert, so the keyboard stays with the film.
// The film is served one file per shot (blender/film.py). Two video elements take turns: while one
// plays a shot, the other loads the next, and at the cut the next one is shown and started, so the
// shots run as one film. Its clock is the shot's start plus the live player's time.
import { reducedMotion, whenIntroDone } from './lifecycle';
import { filmCue, radioVoice, type FilmCue } from './sound';

// Sound effects against each shot's own clock (seconds from the shot's start), matched to the
// renders' timing in blender/arrival.py and blender/lab.py.
const EFFECTS: Record<string, [number, FilmCue][]> = {
  descent: [
    [0.1, 'engine'],
    [4.85, 'engine-cut'],
    [4.9, 'clunk'],
  ],
  ramp: [
    [0.4, 'hiss'],
    [3.4, 'clunk'],
  ],
  street: [
    [2.65, 'servo'],
    [4.1, 'scan'],
    [7.45, 'powerdown'],
  ],
  approach: [[4.0, 'servo']],
  door: [[6.3, 'creak']],
  'lab-breaker': [
    [0.45, 'creak'],
    [2.17, 'breaker'],
  ],
  'lab-power': [
    [0.27, 'tube'],
    [0.67, 'tube'],
    [1.07, 'tube'],
    [1.47, 'tube'],
  ],
  'lab-bench': [[4.97, 'holo']],
};

const SEEN = 'archive:film-seen';
const FADE_MS = 1100;
const CARD_MS = 3400; // the title card's hold before the lab

interface Chapter {
  id: string;
  start: number;
  end: number;
}

interface Line {
  at: number;
  who: string;
  text: string;
  voice?: string;
}

const store = {
  get(key: string) {
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key: string, value: string) {
    try {
      sessionStorage.setItem(key, value);
    } catch {
      /* private mode: the film may play again next visit, which is harmless */
    }
  },
};

export function initFilm(root: HTMLElement): () => void {
  const players = [...root.querySelectorAll<HTMLVideoElement>('[data-film-video]')];
  const skip = root.querySelector<HTMLButtonElement>('[data-film-skip]');
  const sub = root.querySelector<HTMLElement>('[data-film-sub]');
  const whoEl = root.querySelector<HTMLElement>('[data-film-who]');
  const lineEl = root.querySelector<HTMLElement>('[data-film-line]');
  const bar = root.querySelector<HTMLElement>('[data-film-progress]');
  const signal = root.querySelector<HTMLElement>('[data-film-signal]');
  const card = root.querySelector<HTMLElement>('[data-film-card]');
  const chapters = JSON.parse(root.dataset.chapters ?? '[]') as Chapter[];
  const lines = JSON.parse(root.dataset.lines ?? '[]') as Line[];
  if (players.length < 2 || !chapters.length || !skip || !sub || !whoEl || !lineEl || !bar) {
    return () => {};
  }
  const [skipBtn, subEl, who, line, progress] = [skip, sub, whoEl, lineEl, bar];
  const signalEnd = Number(root.dataset.signalEnd) || 0;
  const tiers = (root.dataset.tiers ?? 'desk,phone').split(',');
  const conn = (
    navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }
  ).connection;
  const small = matchMedia('(max-width: 56rem), (max-aspect-ratio: 4/5)').matches || conn?.saveData;
  // Big, sharp screens on a fast line get the 1440p shots when there are any.
  const big =
    screen.width * devicePixelRatio >= 2400 &&
    (!conn?.effectiveType || conn.effectiveType === '4g');
  const has = (t: string) => tiers.includes(t);
  const tier =
    small && has('phone') ? 'phone' : big && has('hd') ? 'hd' : has('desk') ? 'desk' : tiers[0];
  const part = (i: number) => `/set/film/${tier}/${chapters[i].id}.mp4`;
  const off: (() => void)[] = [];
  const on = (
    el: EventTarget,
    type: string,
    fn: (e: Event) => void,
    opts?: AddEventListenerOptions,
  ) => {
    el.addEventListener(type, fn, opts);
    off.push(() => el.removeEventListener(type, fn, opts));
  };
  let playing = false;
  let gone = false;
  let shown = -1;
  let idx = 0; // the shot on screen
  let live = 0; // the player showing it
  let carding: number | undefined;
  const now = () => chapters[idx].start + players[live].currentTime;
  const cues = chapters
    .flatMap((c) => (EFFECTS[c.id] ?? []).map(([at, name]) => ({ at: c.start + at, name })))
    .sort((a, b) => a.at - b.at);
  let nextCue = 0;
  let nextLine = 0;
  const sounds = (t: number) => {
    while (nextCue < cues.length && cues[nextCue].at <= t) {
      // A cue more than a second late (a seek, a stall) is skipped, not fired out of place.
      if (t - cues[nextCue].at < 1) filmCue(cues[nextCue].name);
      nextCue++;
    }
    while (nextLine < lines.length && lines[nextLine].at <= t) {
      const l = lines[nextLine];
      if (t - l.at < 1) {
        filmCue('radio');
        if (l.voice) radioVoice(l.voice);
      }
      nextLine++;
    }
  };
  const inerted: HTMLElement[] = [];

  // Points a player at shot i (or at nothing past the end) unless it already has it.
  const cue = (el: HTMLVideoElement, i: number) => {
    const src = i < chapters.length ? part(i) : '';
    if ((el.dataset.part ?? '') === src) return;
    el.dataset.part = src;
    if (!src) {
      el.removeAttribute('src');
      el.load();
      return;
    }
    el.preload = 'auto';
    el.src = src;
    el.load();
  };
  const load = () => {
    cue(players[0], 0);
    cue(players[1], 1);
  };

  const lock = (yes: boolean) => {
    document.documentElement.classList.toggle('film-on', yes);
    if (yes) {
      for (const el of [
        ...document.querySelectorAll<HTMLElement>('body > header, body > footer, main > *'),
      ]) {
        if (el === root || el.contains(root) || el.inert) continue;
        el.inert = true;
        inerted.push(el);
      }
    } else {
      while (inerted.length) {
        const el = inerted.pop();
        if (el) el.inert = false;
      }
    }
  };

  // A line stays up long enough to read (longer for longer lines), or until the next one.
  const hold = (l: Line) => Math.min(4, Math.max(1.8, 1.2 + 0.06 * l.text.length));
  const subtitle = (t: number) => {
    let k = -1;
    for (let i = 0; i < lines.length && lines[i].at <= t; i++) k = i;
    const visible = k >= 0 && t < lines[k].at + hold(lines[k]) ? k : -1;
    if (visible === shown) return;
    shown = visible;
    subEl.classList.remove('is-on');
    if (visible < 0) return;
    who.textContent = lines[visible].who;
    line.textContent = lines[visible].text;
    void subEl.offsetWidth; // restart the fade
    subEl.classList.add('is-on');
  };

  // The cut: the waiting player takes over at its first frame; the other loads the shot after.
  // If the next shot has not arrived yet, the last frame holds until it can play.
  let waiting = false;
  function advance() {
    if (!playing || waiting) return;
    if (idx + 1 >= chapters.length) return titleCard();
    const cur = players[live];
    const nxt = players[1 - live];
    cue(nxt, idx + 1);
    const go = () => {
      waiting = false;
      if (!playing) return;
      idx += 1;
      live = 1 - live;
      nxt.currentTime = 0;
      void nxt.play().catch(() => {});
      nxt.classList.add('is-live');
      cur.classList.remove('is-live');
      cur.pause();
      cue(cur, idx + 1);
    };
    if (nxt.readyState >= 2) return go();
    waiting = true;
    nxt.addEventListener('canplay', go, { once: true });
  }

  // The end: the picture goes to black and the title holds, then the lab.
  function titleCard() {
    if (!playing || carding !== undefined) return;
    subEl.classList.remove('is-on');
    shown = -1;
    if (!card || reducedMotion()) return finish();
    root.classList.add('film-stage--card');
    filmCue('title');
    carding = window.setTimeout(() => finish(), CARD_MS);
  }

  const tick = () => {
    if (!playing) return;
    const t = now();
    const d = Number(root.dataset.duration) || chapters[chapters.length - 1].end || 1;
    progress.style.transform = `scaleX(${Math.min(1, t / d)})`;
    if (carding === undefined) {
      subtitle(t);
      sounds(t);
      signal?.classList.toggle('is-on', t > 0.8 && t < signalEnd);
    }
    // Cut a frame early rather than wait for the ended event, so the switch is not a pause.
    const cur = players[live];
    if (cur.duration && cur.duration - cur.currentTime < 0.03 && idx + 1 < chapters.length) {
      advance();
    }
    requestAnimationFrame(tick);
  };

  async function start() {
    if (playing || gone) return;
    root.hidden = false;
    root.classList.remove('film-stage--out', 'film-stage--card');
    lock(true);
    idx = 0;
    live = 0;
    waiting = false;
    carding = undefined;
    load();
    players[0].classList.add('is-live');
    players[1].classList.remove('is-live');
    players[0].currentTime = 0;
    nextCue = 0;
    nextLine = 0;
    playing = true;
    try {
      await players[0].play();
    } catch {
      // Autoplay refused (a low-power mode): straight to the lab.
      finish(false);
      return;
    }
    root.classList.add('film-stage--playing');
    skipBtn.focus({ preventScroll: true });
    requestAnimationFrame(tick);
  }

  function finish(fade = true) {
    if (!playing && root.hidden) return;
    playing = false;
    waiting = false;
    window.clearTimeout(carding);
    carding = undefined;
    store.set(SEEN, '1');
    for (const p of players) p.pause();
    filmCue('engine-cut');
    subEl.classList.remove('is-on');
    signal?.classList.remove('is-on');
    shown = -1;
    const done = () => {
      if (gone) return;
      root.hidden = true;
      root.classList.remove('film-stage--playing', 'film-stage--out', 'film-stage--card');
      lock(false);
      window.dispatchEvent(new CustomEvent('archive:film-end'));
      document.querySelector<HTMLElement>('#lab-title')?.focus({ preventScroll: true });
    };
    if (!fade || reducedMotion()) return done();
    root.classList.add('film-stage--out');
    setTimeout(done, FADE_MS);
  }

  for (const p of players) {
    // The last shot's end is the title card; any other end is a cut the tick did not catch in time.
    on(p, 'ended', () => {
      if (p === players[live]) advance();
    });
    on(p, 'error', () => {
      if (playing && p === players[live]) finish(false);
    });
  }
  on(skipBtn, 'click', () => finish());
  on(document, 'keydown', (e) => {
    if ((e as KeyboardEvent).key === 'Escape' && playing) finish();
  });
  on(document, 'visibilitychange', () => {
    if (!playing || carding !== undefined) return;
    if (document.hidden) players[live].pause();
    else void players[live].play().catch(() => {});
  });
  on(window, 'archive:film-play', () => void start());

  const first = store.get(SEEN) !== '1' && !reducedMotion() && !location.hash;
  if (first) {
    // Buffer during the cold open (after the page has loaded), then play when it ends.
    const early = () => {
      if ('requestIdleCallback' in window) requestIdleCallback(load, { timeout: 1200 });
      else setTimeout(load, 200);
    };
    if (document.readyState === 'complete') early();
    else on(window, 'load', early, { once: true });
    void whenIntroDone().then(() => void start());
  }

  return () => {
    gone = true;
    playing = false;
    window.clearTimeout(carding);
    lock(false);
    for (const fn of off) fn();
    for (const p of players) {
      p.pause();
      delete p.dataset.part;
      p.removeAttribute('src');
      p.load();
    }
  };
}

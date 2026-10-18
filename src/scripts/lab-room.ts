// The lab's camera (the home page). Two moves, both on the rendered set:
//   push-in   choosing a record: the room scales towards it while its close-up comes up out of the
//             dark, then the record opens (~0.7 s)
//   pull-out  coming back from a record: the close-up of the record you left falls away as the room
//             returns, and focus lands on that record
// Hover, focus, or a first tap aims a pool of light at a record and names it; on touch the second
// tap opens it. Arrow keys move between records. Without JS, or with reduced motion, the camera
// does not move: the still and its links are the room.
import { navigate } from 'astro:transitions/client';
import { reducedMotion } from './lifecycle';

const LAST = 'archive:lab-last';
const PUSH_MS = 700;
const PULL_MS = 820;
const PUSH_SCALE = 2.6;
const EASE_IN = 'cubic-bezier(.7,0,.84,0)';
const EASE_OUT = 'cubic-bezier(.16,1,.3,1)';

// The router tells us how we arrived (push, replace, traverse); the pull-out needs a traverse.
let navType: string | undefined;
document.addEventListener('astro:before-preparation', (e) => {
  navType = (e as Event & { navigationType?: string }).navigationType;
});

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
      /* private mode: coming back, the room simply does not pull out */
    }
  },
};

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const decoded = (img: HTMLImageElement) =>
  img.decode().then(
    () => true,
    () => false,
  );

export function initLabRoom(root: HTMLElement): () => void {
  const frameEl = root.querySelector<HTMLElement>('[data-lab-frame]');
  const closeEl = root.querySelector<HTMLImageElement>('[data-lab-close]');
  const listEl = root.querySelector<HTMLElement>('[data-lab-items]');
  const pan = root.querySelector<HTMLElement>('[data-lab-pan]');
  if (!frameEl || !closeEl || !listEl) return () => {};
  // Narrowed once, so the closures below keep the non-null types.
  const [frame, closeImg, list] = [frameEl, closeEl, listEl];
  const closeIds = new Set((root.dataset.close ?? '').split(',').filter(Boolean));
  const closeSrc = (id: string) => (closeIds.has(id) ? `/set/lab/close/${id}.avif` : null);
  const touchUI = matchMedia('(hover: none)').matches;
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
  let busy = false;

  // ---- Aim: a pool of light on the record under the pointer, focus, or tap.
  const anchor = (li: HTMLElement) => {
    const cs = getComputedStyle(li);
    return {
      x: parseFloat(cs.getPropertyValue('--ax')) || 0.5,
      y: parseFloat(cs.getPropertyValue('--ay')) || 0.5,
    };
  };
  const aim = (li: HTMLElement | null) => {
    if (!li) {
      root.classList.remove('lab-room--aim');
      return;
    }
    const a = anchor(li);
    frame.style.setProperty('--lx', `${a.x * 100}%`);
    frame.style.setProperty('--ly', `${a.y * 100}%`);
    root.classList.add('lab-room--aim');
    const src = closeSrc(li.dataset.labItem ?? '');
    if (src) new Image().src = src; // warm the close-up for the push-in
  };
  // Tall screens pan across the room: bring a record (the bench, at first) to the middle.
  const centre = (li: HTMLElement | null, smooth = false) => {
    if (!pan || pan.scrollWidth <= pan.clientWidth + 1) return;
    const x = li ? anchor(li).x : 0.5;
    pan.scrollTo({
      left: x * frame.clientWidth - pan.clientWidth / 2,
      behavior: smooth && !reducedMotion() ? 'smooth' : 'instant',
    });
  };
  let selected: HTMLElement | null = null;
  const select = (li: HTMLElement | null) => {
    selected?.classList.remove('is-selected');
    selected = li;
    li?.classList.add('is-selected');
    aim(li);
    centre(li, true);
  };
  const itemOf = (e: Event) => (e.target as HTMLElement).closest<HTMLElement>('[data-lab-item]');
  on(list, 'pointerover', (e) => {
    if ((e as PointerEvent).pointerType === 'mouse') aim(itemOf(e));
  });
  on(list, 'pointerleave', () => aim(selected));
  on(list, 'focusin', (e) => aim(itemOf(e)));
  on(list, 'focusout', () => aim(selected));

  // ---- Arrow keys move between the records that are in this composition.
  const links = () =>
    [...list.querySelectorAll<HTMLAnchorElement>('[data-lab-link]')].filter(
      (a) => a.offsetParent !== null,
    );
  on(list, 'keydown', (e) => {
    const k = (e as KeyboardEvent).key;
    const step =
      k === 'ArrowRight' || k === 'ArrowDown' ? 1 : k === 'ArrowLeft' || k === 'ArrowUp' ? -1 : 0;
    if (!step) return;
    const all = links();
    const i = all.indexOf(document.activeElement as HTMLAnchorElement);
    if (i < 0) return;
    e.preventDefault();
    all[(i + step + all.length) % all.length].focus();
  });

  // ---- Push-in, then open the record.
  async function pushIn(li: HTMLElement, href: string) {
    busy = true;
    const a = anchor(li);
    root.classList.add('lab-room--moving');
    frame.style.transformOrigin = `${a.x * 100}% ${a.y * 100}%`;
    const moves = [
      frame.animate(
        [
          { transform: 'scale(1)', filter: 'brightness(1)' },
          { transform: `scale(${PUSH_SCALE})`, filter: 'brightness(0.55)' },
        ],
        { duration: PUSH_MS, easing: EASE_IN, fill: 'forwards' },
      ),
    ];
    const src = closeSrc(li.dataset.labItem ?? '');
    if (src) {
      closeImg.src = src;
      // Only if the close-up is ready almost at once; the push never waits on a download.
      if (await Promise.race([decoded(closeImg), wait(160).then(() => false)])) {
        moves.push(
          closeImg.animate(
            [
              { opacity: 0, transform: 'scale(1.18)' },
              { opacity: 0, transform: 'scale(1.18)', offset: 0.3 },
              { opacity: 1, transform: 'scale(1)' },
            ],
            { duration: PUSH_MS, easing: EASE_OUT, fill: 'forwards' },
          ),
        );
      }
    }
    await Promise.all(moves.map((m) => m.finished.catch(() => {})));
    await navigate(href);
  }

  on(list, 'click', (e) => {
    const me = e as MouseEvent;
    const link = (e.target as HTMLElement).closest<HTMLAnchorElement>('[data-lab-link]');
    const li = itemOf(e);
    if (!link || !li || me.defaultPrevented || me.button !== 0) return;
    // The projector plays the transmission further down this page: no push-in, just the way there.
    if (link.getAttribute('href')?.startsWith('#')) return;
    if (me.metaKey || me.ctrlKey || me.shiftKey || me.altKey) return;
    if (touchUI && selected !== li) {
      // First tap names the record; the second opens it.
      e.preventDefault();
      select(li);
      return;
    }
    store.set(LAST, li.dataset.labItem ?? '');
    if (reducedMotion() || busy) return;
    e.preventDefault();
    void pushIn(li, link.href);
  });

  // ---- Pull-out: back from a record, the camera returns from it to the room.
  function pullOut(id: string) {
    const li = list.querySelector<HTMLElement>(`[data-lab-item="${CSS.escape(id)}"]`);
    const link = li?.querySelector<HTMLAnchorElement>('[data-lab-link]');
    if (!li || !link || li.offsetParent === null) return;
    const a = anchor(li);
    frame.style.transformOrigin = `${a.x * 100}% ${a.y * 100}%`;
    frame.animate(
      [
        { transform: `scale(${PUSH_SCALE})`, filter: 'brightness(0.55)' },
        { transform: 'scale(1)', filter: 'brightness(1)' },
      ],
      { duration: PULL_MS, easing: EASE_OUT },
    );
    const src = closeSrc(id);
    if (src) {
      closeImg.src = src;
      closeImg.animate(
        [
          { opacity: 1, transform: 'scale(1)' },
          { opacity: 0, transform: 'scale(1.18)' },
        ],
        { duration: PULL_MS * 0.6, easing: EASE_OUT },
      );
    }
    link.focus({ preventScroll: true });
  }

  const traverse =
    navType === 'traverse' ||
    (performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined)
      ?.type === 'back_forward';
  navType = undefined;
  const last = store.get(LAST);
  const box = root.getBoundingClientRect();
  const inView = box.top < innerHeight * 0.3 && box.bottom > innerHeight * 0.6;

  const bench = list.querySelector<HTMLElement>('[data-lab-item="saarthi"]');
  const back =
    traverse && last
      ? list.querySelector<HTMLElement>(`[data-lab-item="${CSS.escape(last)}"]`)
      : null;
  centre(back ?? bench);
  if (back && inView && !reducedMotion()) pullOut(last as string);

  return () => {
    for (const fn of off) fn();
    frame.getAnimations().forEach((a) => a.cancel());
    closeImg.getAnimations().forEach((a) => a.cancel());
  };
}

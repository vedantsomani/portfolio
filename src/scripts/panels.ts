// The home page's panels (Files.astro, Transmission.astro). Without JS they are sections under the
// lab; with it they become sheets that slide over the lab from the right, opened by anything marked
// data-panel-open, by links to /#files or /#transmission, or by arriving at those addresses. Open,
// the rest of the page is inert, focus moves to the panel's title, Escape or the scrim closes it,
// and focus goes back to what opened it. The transmission's hologram plays only while it is open.
import { reducedMotion } from './lifecycle';

export function initPanels(): () => void {
  const panels = new Map(
    [...document.querySelectorAll<HTMLElement>('[data-panel]')].map((p) => [
      p.dataset.panel ?? '',
      p,
    ]),
  );
  const scrim = document.querySelector<HTMLElement>('[data-panel-scrim]');
  if (!panels.size || !scrim) return () => {};
  const scrimEl = scrim;
  const html = document.documentElement;
  html.dataset.panels = 'on';
  const off: (() => void)[] = [];
  const on = (el: EventTarget, type: string, fn: (e: Event) => void, capture = false) => {
    el.addEventListener(type, fn, capture);
    off.push(() => el.removeEventListener(type, fn, capture));
  };
  let open: HTMLElement | null = null;
  let opener: HTMLElement | null = null;
  const inerted: HTMLElement[] = [];

  for (const p of panels.values()) {
    p.setAttribute('role', 'dialog');
    p.setAttribute('aria-modal', 'true');
    p.querySelectorAll<HTMLButtonElement>('[data-panel-close]').forEach((b) => (b.hidden = false));
  }

  const film = (p: HTMLElement, play: boolean) => {
    const v = p.querySelector<HTMLVideoElement>('[data-tx-film]');
    if (!v || !v.dataset.video || reducedMotion()) return;
    if (play) {
      if (!v.getAttribute('src')) {
        const small = matchMedia('(max-width: 56rem), (max-aspect-ratio: 4/5)').matches;
        v.src = `/set/holo/${small ? 'phone' : 'desk'}.mp4`;
      }
      void v.play().catch(() => {});
    } else v.pause();
  };

  function show(id: string, from: HTMLElement | null) {
    const p = panels.get(id);
    if (!p) return;
    if (open && open !== p) hide(false);
    open = p;
    opener = from;
    for (const el of document.querySelectorAll<HTMLElement>(
      'body > header, body > footer, main > *',
    )) {
      if (el === p || el === scrimEl || el.inert || el.hasAttribute('data-film')) continue;
      el.inert = true;
      inerted.push(el);
    }
    scrimEl.hidden = false;
    html.classList.add('panel-on');
    // Open at once (focus needs it visible); the slide is a transition from where it was.
    p.classList.add('is-open');
    requestAnimationFrame(() => scrimEl.classList.add('is-on'));
    p.scrollTop = 0;
    p.querySelector<HTMLElement>('.panel__title')?.focus({ preventScroll: true });
    film(p, true);
    history.replaceState(history.state, '', `#${id}`);
  }

  function hide(restore = true) {
    if (!open) return;
    const p = open;
    open = null;
    p.classList.remove('is-open');
    scrimEl.classList.remove('is-on');
    film(p, false);
    while (inerted.length) {
      const el = inerted.pop();
      if (el) el.inert = false;
    }
    html.classList.remove('panel-on');
    setTimeout(() => {
      if (!open) scrimEl.hidden = true;
    }, 400);
    history.replaceState(history.state, '', location.pathname + location.search);
    if (restore)
      (opener ?? document.querySelector<HTMLElement>('#lab-title'))?.focus({ preventScroll: true });
  }

  // Capture phase: the router handles same-page '#' links on the way up; the panels come first.
  on(
    document,
    'click',
    (e) => {
      const me = e as MouseEvent;
      if (me.button !== 0 || me.metaKey || me.ctrlKey || me.shiftKey) return;
      onClick(e);
    },
    true,
  );
  function onClick(e: Event) {
    const t = e.target as HTMLElement;
    if (t.closest('[data-panel-close]')) return hide();
    const trigger = t.closest<HTMLElement>(
      '[data-panel-open], a[href="#files"], a[href="/#files"], a[href="#transmission"], a[href="/#transmission"]',
    );
    if (!trigger) return;
    const id =
      trigger.dataset.panelOpen ?? (trigger.getAttribute('href') ?? '').replace(/^\/?#/, '');
    if (!panels.has(id)) return;
    e.preventDefault();
    show(id, trigger);
  }
  on(scrimEl, 'click', () => hide());
  on(document, 'keydown', (e) => {
    if ((e as KeyboardEvent).key === 'Escape' && open) hide();
  });

  const fromHash = () => {
    const id = location.hash.replace('#', '');
    if (panels.has(id) && open !== panels.get(id)) show(id, null);
  };
  fromHash();
  // A link to /#files from this same page changes only the hash.
  on(window, 'hashchange', fromHash);

  return () => {
    hide(false);
    for (const fn of off) fn();
    delete html.dataset.panels;
  };
}

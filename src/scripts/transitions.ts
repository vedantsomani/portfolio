// Page transitions (03_PHASE3_MOTION §4). Between main routes an --oxblood panel wipes up from the
// bottom (250 ms, ease-in), the page swaps under it, and it leaves through the top (300 ms,
// ease-out). A project card → case study navigation skips the wipe: the cover morphs instead
// (transition:name). Reduced motion: an instant swap.
import { reducedMotion } from './lifecycle';

const EASE_IN = 'cubic-bezier(0.7, 0, 0.84, 0)';
const EASE_OUT = 'cubic-bezier(0.16, 1, 0.3, 1)';
const CASE = /^\/projects\/[^/]+$/;
const LIST = /^\/(projects)?$/;

// Back/forward between a list and a case study is the same pair, morphing the other way.
const isMorphPair = (from: URL, to: URL) =>
  (CASE.test(from.pathname) && LIST.test(to.pathname)) ||
  (LIST.test(from.pathname) && CASE.test(to.pathname));

export function initTransitions(): void {
  let covering = false;

  document.addEventListener('astro:before-preparation', (event) => {
    const panel = document.querySelector<HTMLElement>('[data-wipe]');
    const fromCard = (event.sourceElement as Element | null)?.closest('[data-morph]');
    const morph =
      fromCard || (event.navigationType === 'traverse' && isMorphPair(event.from, event.to));
    if (!panel || reducedMotion() || morph) return;

    const load = event.loader;
    event.loader = async () => {
      covering = true;
      panel.classList.add('is-active');
      const cover = panel.animate(
        [{ transform: 'translateY(100%)' }, { transform: 'translateY(0)' }],
        { duration: 250, easing: EASE_IN, fill: 'forwards' },
      );
      await Promise.all([cover.finished, load()]);
      // Commit the covered state so it survives the swap (the panel is transition:persist).
      panel.style.transform = 'translateY(0)';
      cover.cancel();
    };
  });

  document.addEventListener('astro:page-load', () => {
    const panel = document.querySelector<HTMLElement>('[data-wipe]');
    if (!panel || !covering) return;
    covering = false;
    const uncover = panel.animate(
      [{ transform: 'translateY(0)' }, { transform: 'translateY(-100%)' }],
      { duration: 300, easing: EASE_OUT },
    );
    panel.style.transform = '';
    uncover.finished.then(
      () => panel.classList.remove('is-active'),
      () => panel.classList.remove('is-active'),
    );
  });
}

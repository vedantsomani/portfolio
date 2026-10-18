// Saarthi, system by system (BoardStory.astro): the step crossing the middle of the viewport names
// the group the board map lights. Without this script the map keeps every group lit.
export function initBoardStory(root: HTMLElement): () => void {
  const map = root.querySelector<SVGElement>('[data-board-map]');
  const steps = [...root.querySelectorAll<HTMLElement>('[data-step]')];
  if (!map || !steps.length) return () => {};
  root.classList.add('board-story--live');
  map.dataset.view = 'overview';

  const show = (step: HTMLElement) => {
    for (const s of steps) s.classList.toggle('is-active', s === step);
    map.dataset.view = step.dataset.step ?? 'overview';
  };

  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) if (e.isIntersecting) show(e.target as HTMLElement);
    },
    // A thin band across the middle of the screen: one step at a time is "being read".
    { rootMargin: '-48% 0px -48% 0px' },
  );
  steps.forEach((s) => io.observe(s));

  return () => {
    io.disconnect();
    root.classList.remove('board-story--live');
    map.dataset.view = 'all';
  };
}

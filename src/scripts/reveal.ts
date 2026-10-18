// Once-only reveals (SITE_SPEC §4.6). BaseLayout's head script sets <html data-reveals="pending">
// before first paint, and only when motion is allowed; motion.css then holds every [data-reveal]
// block 12 px low and transparent, with a failsafe that shows it after 2.5 s. This flips the page to
// "on" (dropping the failsafe) and adds .is-in as each block enters, 70 ms apart when several enter
// together. Nothing is ever hidden again once shown.
const STAGGER = 70;
const MAX_STEPS = 4;

export function initReveals(): (() => void) | undefined {
  const html = document.documentElement;
  if (html.dataset.reveals !== 'pending') return undefined;
  const blocks = document.querySelectorAll<HTMLElement>('[data-reveal]');
  html.dataset.reveals = 'on';
  if (!blocks.length) return undefined;

  const io = new IntersectionObserver(
    (entries) => {
      let step = 0;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const el = entry.target as HTMLElement;
        el.style.setProperty('--reveal-delay', `${Math.min(step++, MAX_STEPS) * STAGGER}ms`);
        el.classList.add('is-in');
        io.unobserve(el);
      }
    },
    { rootMargin: '0px 0px -8% 0px' },
  );
  blocks.forEach((el) => io.observe(el));
  return () => io.disconnect();
}

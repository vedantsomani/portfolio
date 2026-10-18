// Case-study chapter rail: marks the section being read (aria-current="location") as the reader
// scrolls. Without JS the rail is still a plain list of links.
export function initSpy(nav: HTMLElement): () => void {
  const links = [...nav.querySelectorAll<HTMLAnchorElement>('a[href^="#"]')];
  const sections = links
    .map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1))))
    .filter((s): s is HTMLElement => Boolean(s));
  if (!sections.length) return () => {};
  const visible = new Set<HTMLElement>();

  const mark = () => {
    // The first section (in page order) that is in the reading band wins.
    const current = sections.find((s) => visible.has(s));
    if (!current) return;
    links.forEach((a) => {
      if (a.hash.slice(1) === current.id) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
  };

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        const el = e.target as HTMLElement;
        if (e.isIntersecting) visible.add(el);
        else visible.delete(el);
      });
      mark();
    },
    // The reading band: from 20% below the top of the viewport to 40% above the bottom.
    { rootMargin: '-20% 0px -40% 0px' },
  );
  sections.forEach((s) => io.observe(s));
  return () => io.disconnect();
}

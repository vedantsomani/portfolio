// Scroll moment 2 (03_PHASE3_MOTION §5): one PCB-style trace in the left gutter, drawn by scroll
// (DrawSVG + ScrollTrigger, scrub 0.5). It runs down a trunk and jogs out at 45° to a pad beside
// each section heading ([data-trace-stop]). Desktop only (it needs a gutter), --rule-strong (the
// red usage rule keeps oxblood-hi off decoration). Reduced motion: drawn in full, no scrub.
import { reducedMotion } from './lifecycle';

const SVG = 'http://www.w3.org/2000/svg';
const JOG = 10;

export function initTrace(scope: HTMLElement): () => void {
  const desktop = matchMedia('(min-width: 64rem)');
  let teardown: (() => void) | null = null;
  let disposed = false;

  async function build() {
    teardown?.();
    teardown = null;
    if (!desktop.matches || disposed) return;

    const stops = [...scope.querySelectorAll<HTMLElement>('[data-trace-stop]')]
      .map((el) => el.querySelector<HTMLElement>('h2') ?? el)
      .filter((el) => el.offsetParent !== null);
    if (stops.length < 2) return;

    const base = scope.getBoundingClientRect();
    const firstLeft = stops[0].getBoundingClientRect().left - base.left;
    if (firstLeft < 48) return;
    const trunk = Math.round(firstLeft * 0.35);
    const padX = Math.round(firstLeft - 20);
    const ys = stops.map((el) => {
      const r = el.getBoundingClientRect();
      const lh = parseFloat(getComputedStyle(el).lineHeight) || r.height;
      return Math.round(r.top - base.top + Math.min(r.height, lh) / 2);
    });

    const d: string[] = [`M${padX} ${ys[0]} H${trunk + JOG} L${trunk} ${ys[0] + JOG}`];
    for (let i = 1; i < ys.length; i++) {
      if (i > 1) d.push(`M${trunk + JOG} ${ys[i - 1]} L${trunk} ${ys[i - 1] + JOG}`);
      d.push(`V${ys[i] - JOG} L${trunk + JOG} ${ys[i]} H${padX}`);
    }

    const svg = document.createElementNS(SVG, 'svg');
    svg.classList.add('trace');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('width', String(firstLeft));
    svg.setAttribute('height', String(Math.ceil(base.height)));
    const path = document.createElementNS(SVG, 'path');
    path.setAttribute('d', d.join(' '));
    path.classList.add('trace__path');
    svg.append(path);
    const pads = ys.map((y) => {
      const c = document.createElementNS(SVG, 'circle');
      c.setAttribute('cx', String(padX));
      c.setAttribute('cy', String(y));
      c.setAttribute('r', '4.5');
      c.classList.add('trace__pad');
      svg.append(c);
      return c;
    });
    scope.prepend(svg);

    if (reducedMotion()) {
      pads.forEach((p) => p.classList.add('is-on'));
      teardown = () => svg.remove();
      return;
    }

    const [{ gsap }, { ScrollTrigger }, { DrawSVGPlugin }] = await Promise.all([
      import('gsap'),
      import('gsap/ScrollTrigger'),
      import('gsap/DrawSVGPlugin'),
    ]);
    if (disposed) {
      svg.remove();
      return;
    }
    gsap.registerPlugin(ScrollTrigger, DrawSVGPlugin);
    // Pad i lights once the drawn tip passes its heading: fractions of the scroll range by y.
    const top = ys[0];
    const span = ys[ys.length - 1] - top;
    const at = ys.map((y) => (y - top) / span);
    const tween = gsap.fromTo(
      path,
      { drawSVG: '0%' },
      {
        drawSVG: '100%',
        ease: 'none',
        scrollTrigger: {
          trigger: stops[0],
          endTrigger: stops[stops.length - 1],
          start: 'center 60%',
          end: 'center 60%',
          scrub: 0.5,
          onUpdate: (self) =>
            pads.forEach((p, i) => p.classList.toggle('is-on', self.progress >= at[i] - 0.001)),
        },
      },
    );
    teardown = () => {
      tween.scrollTrigger?.kill();
      tween.kill();
      svg.remove();
    };
  }

  let timer = 0;
  const ro = new ResizeObserver(() => {
    clearTimeout(timer);
    timer = window.setTimeout(() => void build(), 150);
  });
  ro.observe(scope);
  const onMedia = () => void build();
  desktop.addEventListener('change', onMedia);

  return () => {
    disposed = true;
    clearTimeout(timer);
    ro.disconnect();
    desktop.removeEventListener('change', onMedia);
    teardown?.();
  };
}

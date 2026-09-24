// Hero load sequence (03_PHASE3_MOTION §2), once per session:
//   0 ms photo visible → 150 ms headline lines rise (SplitText by lines, each in its own mask,
//   700 ms expo.out, 80 ms stagger) → 650 ms supporting line + CTAs fade → 900 ms lens activates.
// The head script in BaseLayout sets <html data-reveal="pending"> before first paint so nothing
// flashes; motion.css shows everything anyway if this never runs. Repeat visits and reduced
// motion get the final state immediately.
import { gsap } from 'gsap';
import { SplitText } from 'gsap/SplitText';

gsap.registerPlugin(SplitText);

const TOTAL = 1.3;

export function revealHeadline(root: HTMLElement, activateLens: () => void): () => void {
  const html = document.documentElement;
  const title = root.querySelector<HTMLElement>('[data-hero-title]');
  const copy = root.querySelector<HTMLElement>('[data-hero-copy]');
  if (html.dataset.reveal !== 'pending' || !title || !copy) {
    delete html.dataset.reveal;
    activateLens();
    return () => {};
  }

  const split = SplitText.create(title, { type: 'lines', mask: 'lines', linesClass: 'hero-line' });
  const lines = split.lines;
  // Keep the whole sequence inside 1.3 s however many lines the headline wraps to.
  const stagger = Math.min(0.08, (TOTAL - 0.15 - 0.7) / Math.max(1, lines.length - 1));
  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    split.revert();
    try {
      sessionStorage.setItem('hero-revealed', '1');
    } catch {
      /* private mode: the reveal just plays again next time */
    }
  };

  gsap.set(lines, { yPercent: 100 });
  gsap.set(copy, { opacity: 0 });
  delete html.dataset.reveal;

  const tl = gsap.timeline({ onComplete: finish });
  tl.to(lines, { yPercent: 0, duration: 0.7, ease: 'expo.out', stagger }, 0.15)
    .to(copy, { opacity: 1, duration: 0.25, ease: 'none' }, 0.65)
    .call(activateLens, [], 0.9);

  return () => {
    tl.kill();
    gsap.set(copy, { clearProps: 'opacity' });
    finish();
  };
}

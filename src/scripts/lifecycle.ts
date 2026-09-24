// Every motion module registers here. Inits run on astro:page-load (first load and every
// ClientRouter navigation); their cleanups run on astro:before-swap, so no ScrollTrigger, RAF loop,
// observer, or WebGL context outlives its page.
type Cleanup = () => void;
type InitResult = Cleanup | undefined;

const cleanups: Cleanup[] = [];

document.addEventListener('astro:before-swap', () => {
  while (cleanups.length) cleanups.pop()?.();
});

export function onPage(init: () => InitResult | Promise<InitResult>): void {
  document.addEventListener('astro:page-load', async () => {
    const cleanup = await init();
    if (cleanup) cleanups.push(cleanup);
  });
}

export const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

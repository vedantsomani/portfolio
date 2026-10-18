// The Archive walkthrough: the cold open (gate, credits, traces, cut), the hand-over to the film
// and its end into the lab, and an Escape skip at the gate in a fresh session. Screens to qa/film/.
// Usage: node scripts/qa/film.mjs [baseURL] [outDir] [width] [height]
//   (default http://127.0.0.1:8787, qa/film, 1440 × 900; system Edge, SwiftShader GL)
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const base = process.argv[2] ?? 'http://127.0.0.1:8787';
const out = process.argv[3] ?? 'qa/film';
const width = Number(process.argv[4] ?? 1440);
const height = Number(process.argv[5] ?? 900);
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({
  channel: 'msedge',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
let failed = 0;
const report = (ok, label) => {
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
};

// 1. The full sequence.
{
  const page = await browser.newPage({ viewport: { width, height } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const shot = (name) => page.screenshot({ path: `${out}/${width}-${name}.png` });
  await page.goto(base + '/', { waitUntil: 'load' });
  await page.waitForTimeout(1800);
  await shot('01-gate');
  report(
    await page.evaluate(() => document.getElementById('main')?.closest('[inert]') !== null),
    'gate: page behind is inert',
  );
  report(
    (await page.evaluate(() => document.activeElement?.textContent?.trim())) === 'Enter with sound',
    'gate: focus starts on "Enter with sound"',
  );
  await page.click('[data-intro-enter="silent"]');
  for (const [t, name] of [
    [1900, '02-presents'],
    [2600, '03-flight-hardware'],
    [3300, '04-space-data'],
    [2200, '05-silicon'],
    [2600, '06-name'],
  ]) {
    await page.waitForTimeout(t);
    await shot(name);
  }
  await page.waitForFunction(() => !document.documentElement.dataset.intro, null, {
    timeout: 15000,
  });
  await page.waitForTimeout(1500);
  await shot('07-film');
  // The cold open hands over to the film (focus on its Skip, the page behind it inert), or, where
  // there is no film, to the page (focus on <main>, nothing inert).
  const after = await page.evaluate(() => ({
    film: !!document.querySelector('[data-film]:not([hidden])'),
    focus: document.activeElement?.matches('[data-film-skip], #main') ?? false,
    inertMain: !!document.querySelector('main > [inert]'),
  }));
  report(after.focus, 'after: focus is on the film Skip (or <main> without a film)');
  report(after.film ? after.inertMain : !after.inertMain, 'after: only the film is live while it plays');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  report(
    await page.evaluate(() => !document.querySelector('[inert]') && document.activeElement?.id === 'lab-title'),
    'Escape ends the film into the lab: nothing inert, focus on the name',
  );
  await shot('08-lab');
  report(errors.length === 0, `no page errors${errors.length ? `: ${errors.join('; ')}` : ''}`);
  await page.close();
}

// 2. Escape skips at once, in a fresh session.
{
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(base + '/', { waitUntil: 'load' });
  await page.waitForTimeout(1200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(900);
  report(
    await page.evaluate(() => !document.documentElement.dataset.intro),
    'Escape at the gate skips the cold open',
  );
  // A second home visit in the same session never shows it.
  await page.goto(base + '/', { waitUntil: 'load' });
  report(
    await page.evaluate(() => !document.querySelector('[data-intro-root]')),
    'second visit this session: no cold open',
  );
  await page.close();
}

await browser.close();
process.exit(failed ? 1 : 0);

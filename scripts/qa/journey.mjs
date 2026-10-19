// Walks the home page like a first-time visitor and screenshots it: the intro gate, the film at
// points along its length (checking it really plays), its end into the lab, both panels, a record
// opened from the room and Back to it. Usage: node scripts/qa/journey.mjs [out dir] [full]
// ("full" watches the film to its end instead of skipping the last part). Preview on BASE.
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { BASE } from './routes.mjs';

const out = process.argv[2] ?? 'qa/journey';
const full = process.argv[3] === 'full';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge' });
let ok = true;
const report = (pass, text) => {
  ok &&= pass;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${text}`);
};

for (const [name, viewport] of [
  ['desk', { width: 1440, height: 900 }],
  ['phone', { width: 390, height: 844 }],
]) {
  const ctx = await browser.newContext({
    viewport,
    isMobile: name === 'phone',
    hasTouch: name === 'phone',
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(BASE + '/', { waitUntil: 'load' });
  const gate = page.locator('[data-intro-enter="silent"]');
  if (await gate.isVisible().catch(() => false)) await gate.click();
  await page.waitForFunction(() => !document.documentElement.dataset.intro, null, {
    timeout: 30000,
  });
  // The film's clock is past `at`: the live player's shot start plus its time (the shots are
  // separate files).
  const past = (at) => {
    const root = document.querySelector('[data-film]');
    const v = document.querySelector('[data-film-video].is-live');
    if (!root || !v) return false;
    const chapters = JSON.parse(root.dataset.chapters || '[]');
    const c = chapters.find((x) => (v.dataset.part || '').endsWith(`/${x.id}.mp4`));
    return (c ? c.start : 0) + v.currentTime >= at;
  };
  // A phone has no cold open and no film by itself: its home is the simple page, and the film is
  // its button.
  if (name === 'phone') {
    report(
      await page.locator('[data-phone-home]').isVisible(),
      'phone: the simple home, no cold open, no film by itself',
    );
    await page.screenshot({ path: `${out}/phone-home.png` });
    await page.locator('[data-phone-film]').click();
  }
  const playing = await page
    .waitForFunction(
      () => {
        const v = document.querySelector('[data-film-video].is-live');
        return v && !v.paused && v.currentTime > 0.3;
      },
      null,
      { timeout: 20000 },
    )
    .then(() => true)
    .catch(() => false);
  report(playing, `${name}: the film plays ${name === 'phone' ? 'from its button' : 'by itself after the cold open'}`);
  const duration = await page.evaluate(() =>
    Number(document.querySelector('[data-film]')?.dataset.duration ?? 0),
  );
  for (const at of [3, 10, 18, 26, 34, 42, 52]) {
    if (!playing || at > duration) break;
    await page.waitForFunction(past, at, { timeout: 60000 });
    const sub = await page.evaluate(() =>
      document.querySelector('[data-film-sub].is-on')?.textContent?.replace(/\s+/g, ' ').trim(),
    );
    await page.screenshot({ path: `${out}/${name}-film-${String(at).padStart(2, '0')}s.png` });
    console.log(`      ${name} ${at}s: ${sub ?? '(no subtitle)'}`);
  }
  if (playing && full) {
    await page.waitForSelector('[data-film]', { state: 'hidden', timeout: 90000 });
  } else if (playing) {
    await page.locator('[data-film-skip]').click();
    await page.waitForSelector('[data-film]', { state: 'hidden', timeout: 5000 });
  }
  await page.waitForTimeout(500);
  report(
    (await page.evaluate(() => document.activeElement?.id)) ===
      (name === 'phone' ? 'phone-name' : 'lab-title'),
    `${name}: the film ends ${name === 'phone' ? 'back on the home' : 'in the lab'}, focus on the name`,
  );
  await page.screenshot({ path: `${out}/${name}-lab.png` });
  for (const id of ['files', 'transmission']) {
    // The site's navigation opens them (/#files, /#transmission); on a phone it is in the menu.
    await page.evaluate((x) => (location.hash = x), id);
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `${out}/${name}-${id}.png` });
    report(
      await page.evaluate((x) => document.getElementById(x)?.classList.contains('is-open'), id),
      `${name}: the ${id} panel opens`,
    );
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }
  report(errors.length === 0, `${name}: no page errors${errors.length ? ' — ' + errors.join(' | ') : ''}`);
  await ctx.close();
}

// A record from the room: the push-in, then the record over its close-up; Back to the room.
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => {
    sessionStorage.setItem('intro-seen', '1');
    sessionStorage.setItem('archive:film-seen', '1');
  });
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load' });
  await page.waitForTimeout(600);
  await page.locator('[data-lab-item="vajra"] [data-lab-link]').click();
  await page.waitForURL('**/projects/vajra', { timeout: 10000 });
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${out}/record-vajra.png` });
  await page.goBack();
  await page.waitForSelector('[data-lab]', { timeout: 10000 });
  await page.waitForTimeout(900);
  const focus = await page.evaluate(() =>
    document.activeElement?.closest('[data-lab-item]')?.getAttribute('data-lab-item'),
  );
  report(focus === 'vajra', `Back from a record returns to the lab, focus on it (${focus})`);
  await ctx.close();
}

await browser.close();
if (!ok) process.exit(1);

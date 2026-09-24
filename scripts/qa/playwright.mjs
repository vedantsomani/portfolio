// Checks 8 and 9.
//  8. JS disabled: every route renders its main heading, the nav, and its content.
//  9. prefers-reduced-motion: no running animations on Home or a project page, and the hero shows
//     the "Show circuit layout" toggle (which works from the keyboard).
import { chromium } from 'playwright';
import { BASE, NOT_FOUND, ROUTES } from './routes.mjs';

const browser = await chromium.launch({ channel: 'msedge' });
let ok = true;
const report = (pass, text) => {
  ok &&= pass;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${text}`);
};

console.log('— Check 8: JavaScript disabled —');
{
  const ctx = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await ctx.newPage();
  for (const route of [...ROUTES, NOT_FOUND]) {
    await page.goto(BASE + route, { waitUntil: 'load' });
    const r = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      const visible = (el) =>
        !!el &&
        el.getBoundingClientRect().height > 0 &&
        getComputedStyle(el).visibility !== 'hidden' &&
        getComputedStyle(el).opacity !== '0';
      const main = document.querySelector('main');
      return {
        h1: h1?.textContent?.trim().slice(0, 50),
        h1Visible: visible(h1),
        nav:
          !!document.querySelector('header.nav a[href="/"]') &&
          visible(
            document.querySelector('[data-menu-fallback]') ??
              document.querySelector('.nav__primary'),
          ),
        footerNav: document.querySelectorAll('#footer-nav a').length,
        text: (main?.innerText ?? '').trim().length,
      };
    });
    report(
      r.h1Visible && r.nav && r.footerNav >= 4 && r.text > 60,
      `${route.padEnd(28)} h1 "${r.h1}" · nav ✓ · footer links ${r.footerNav} · ${r.text} chars of content`,
    );
  }
  await ctx.close();
}

console.log('\n— Check 9: prefers-reduced-motion: reduce —');
{
  const ctx = await browser.newContext({
    reducedMotion: 'reduce',
    viewport: { width: 1440, height: 900 },
  });
  const page = await ctx.newPage();
  for (const route of ['/', '/projects/saarthi']) {
    await page.goto(BASE + route, { waitUntil: 'networkidle' });
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 300) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 50));
      }
    });
    await page.waitForTimeout(800);
    const running = await page.evaluate(() =>
      document
        .getAnimations()
        .filter((a) => a.playState === 'running')
        .map(
          (a) =>
            `${a.constructor.name}:${a.animationName ?? a.id ?? ''} on ${a.effect?.target?.className ?? ''}`,
        ),
    );
    report(
      running.length === 0,
      `${route}: ${running.length} running animations${running.length ? ' — ' + running.join(', ') : ''}`,
    );
  }
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  const toggle = page.getByRole('button', { name: 'Show circuit layout' });
  report(await toggle.isVisible(), 'Home: "Show circuit layout" toggle is visible');
  report(
    (await page.locator('.lens__canvas').count()) === 0,
    'Home: no lens canvas under reduced motion',
  );
  await toggle.focus();
  await page.keyboard.press('Enter');
  report(
    (await toggle.getAttribute('aria-pressed')) === 'true' &&
      (await page.locator('[data-lens-xray]').isVisible()),
    'Home: Enter on the toggle cuts to the circuit layout (aria-pressed=true)',
  );
  await page.keyboard.press('Space');
  report(
    (await toggle.getAttribute('aria-pressed')) === 'false' &&
      !(await page.locator('[data-lens-xray]').isVisible()),
    'Home: Space cuts back to the photo (aria-pressed=false)',
  );
  const title = await page.evaluate(() => {
    const t = document.querySelector('.hero__title');
    return { vis: getComputedStyle(t).visibility, split: !!t.querySelector('.hero-line') };
  });
  report(
    title.vis === 'visible' && !title.split,
    'Home: headline is in its final state (no SplitText masks)',
  );
  await ctx.close();
}

await browser.close();
if (!ok) process.exit(1);

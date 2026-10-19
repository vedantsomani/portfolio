// Checks 8, 9 and 10.
//  8. JS disabled: every route renders its main heading, the nav, and its content; on the home page
//     the lab is a still room whose records are all working links, with the files and the
//     transmission as sections under it.
//  9. prefers-reduced-motion: no running animations on Home, a project page, or the briefing; the
//     film does not play by itself; the panels open from the keyboard, Escape closes them and focus
//     goes back; the briefing film does not play.
// 10. With motion: a first visit plays the film by itself; Skip ends it into the lab, focus on the
//     name; a record opens from the room and Back returns to it with focus on that record; the files
//     panel opens at /#files; the briefing film hands over to the page.
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
  await page.goto(BASE + '/', { waitUntil: 'load' });
  const home = await page.evaluate(() => {
    const shown = (sel) => {
      const el = document.querySelector(sel);
      return (
        !!el &&
        el.getBoundingClientRect().height > 0 &&
        getComputedStyle(el).visibility !== 'hidden'
      );
    };
    return {
      // The room's record links, or on a phone the simple home's project cards (PhoneHome).
      links: [...document.querySelectorAll('[data-lab-link], .phone-card')].filter((a) => {
        const r = a.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      }).length,
      files: document.querySelectorAll('#files a[href^="/projects/"], #files a[href^="/lab/"]')
        .length,
      sections: shown('#files') && shown('#transmission'),
      film: shown('[data-film]'),
    };
  });
  report(home.links >= 8, `/ home: ${home.links} record links (the still room, or a phone's cards)`);
  report(
    home.sections && home.files >= 9 && !home.film,
    `/ files and transmission are sections under it (${home.files} record links), no film`,
  );
  await ctx.close();
}

console.log('\n— Check 9: prefers-reduced-motion: reduce —');
{
  const ctx = await browser.newContext({
    reducedMotion: 'reduce',
    viewport: { width: 1440, height: 900 },
  });
  const page = await ctx.newPage();
  for (const route of ['/', '/projects/saarthi', '/briefing']) {
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
  await page.waitForTimeout(600);
  report(
    (await page.locator('[data-film]').count()) === 0 ||
      (await page.locator('[data-film]').isHidden()),
    '/: the film does not play by itself',
  );
  const files = page.locator('header a[href="/#files"]').first();
  await files.focus();
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  const opened = await page.evaluate(() => ({
    open: document.querySelector('#files')?.classList.contains('is-open'),
    focus: document.activeElement?.id,
    modal: document.querySelector('#files')?.getAttribute('aria-modal'),
  }));
  report(
    opened.open && opened.focus === 'files-title' && opened.modal === 'true',
    `/: Enter on "Files" opens the panel, focus on its title (${opened.focus})`,
  );
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  report(
    !(await page.evaluate(() => document.querySelector('#files')?.classList.contains('is-open'))) &&
      (await page.evaluate(() => document.activeElement?.textContent?.includes('Files'))),
    '/: Escape closes it and focus goes back to "Files"',
  );
  await page.goto(BASE + '/briefing', { waitUntil: 'networkidle' });
  report(
    (await page.locator('[data-handoff]').count()) === 0 ||
      (await page.locator('[data-handoff]').isHidden()),
    '/briefing: no handoff film under reduced motion',
  );
  await ctx.close();
}

console.log('\n— Check 10: the film, the lab and the briefing, with motion —');
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => sessionStorage.setItem('intro-seen', '1'));
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load' });
  if ((await page.locator('[data-film]').count()) > 0) {
    await page.waitForFunction(
      () => {
        const v = document.querySelector('[data-film-video]');
        return v && !v.paused && v.currentTime > 0.5;
      },
      null,
      { timeout: 20000 },
    );
    report(true, '/: a first visit plays the film by itself');
    await page.locator('[data-film-skip]').click();
    await page.waitForTimeout(1500);
    report(
      (await page.locator('[data-film]').isHidden()) &&
        (await page.evaluate(() => document.activeElement?.id)) === 'lab-title',
      '/: Skip ends it into the lab, focus on the name',
    );
  } else report(false, '/: the film is built');
  await page.locator('[data-lab-item="tessera"] [data-lab-link]').click();
  await page.waitForURL('**/projects/tessera', { timeout: 10000 });
  report(true, '/: choosing TESSERA in the room opens its record');
  await page.goBack();
  await page.waitForSelector('[data-lab]', { timeout: 10000 });
  await page.waitForTimeout(900);
  const focus = await page.evaluate(() =>
    document.activeElement?.closest('[data-lab-item]')?.getAttribute('data-lab-item'),
  );
  report(focus === 'tessera', `Back: focus returns to the record left (${focus})`);
  await page.goto(BASE + '/#files', { waitUntil: 'load' });
  await page.waitForTimeout(600);
  report(
    await page.evaluate(() => document.querySelector('#files')?.classList.contains('is-open')),
    '/#files opens the files panel',
  );
  await ctx.close();

  const film = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const fp = await film.newPage();
  await fp.goto(BASE + '/briefing', { waitUntil: 'load' });
  const shown =
    (await fp.locator('[data-handoff]').count()) > 0 &&
    (await fp.locator('[data-handoff]').isVisible());
  if (shown) {
    await fp.keyboard.press('Escape');
    await fp.waitForTimeout(900);
    report(
      (await fp.locator('[data-handoff]').isHidden()) &&
        (await fp.evaluate(() => document.activeElement?.id)) === 'brief-name',
      '/briefing: Escape hands over from the film to the page, focus on the name',
    );
  } else report(false, '/briefing: the handoff film shows on a first visit');
  await film.close();
}

await browser.close();
if (!ok) process.exit(1);

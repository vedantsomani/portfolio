// Keyboard and form checks. Usage: node scripts/qa-flows.mjs [baseURL]
import { chromium } from 'playwright';

const base = process.argv[2] ?? 'http://localhost:4321';
const browser = await chromium.launch({ channel: 'msedge' });
const results = [];
const check = (name, ok, detail = '') =>
  results.push(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`);
const focused = (page) =>
  page.evaluate(() => {
    const el = document.activeElement;
    return `${el?.tagName.toLowerCase()}${el?.id ? '#' + el.id : ''} "${(el?.textContent ?? '').trim().slice(0, 30)}"`;
  });

// 1. Desktop keyboard: skip link, then nav order.
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(base + '/', { waitUntil: 'networkidle' });
  await page.keyboard.press('Tab');
  check('skip link is first tab stop', (await focused(page)).includes('Skip to content'));
  const order = [];
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press('Tab');
    order.push(await focused(page));
  }
  check(
    'desktop nav tab order',
    order.join(' | ').includes('Projects') && order.join(' | ').includes('Get in touch'),
    order.join(' | '),
  );
  await page.goto(base + '/', { waitUntil: 'networkidle' });
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  check('skip link moves focus to main', (await focused(page)).startsWith('main#main'));
  await page.close();
}

// 2. Mobile menu: opens, traps focus, Esc closes, focus returns to the Menu button.
{
  const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
  await page.goto(base + '/', { waitUntil: 'networkidle' });
  await page.focus('[data-menu-open]');
  await page.keyboard.press('Enter');
  check(
    'menu opens as modal',
    await page.evaluate(() => document.querySelector('dialog')?.matches(':modal')),
  );
  const inside = [];
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    inside.push(
      await page.evaluate(
        () =>
          !!document.activeElement?.closest('dialog') || document.activeElement === document.body,
      ),
    );
  }
  check('focus stays inside the menu', inside.every(Boolean));
  await page.keyboard.press('Escape');
  check('Esc closes the menu', await page.evaluate(() => !document.querySelector('dialog')?.open));
  check('focus returns to Menu button', (await focused(page)).includes('Menu'));
  await page.close();
}

// 3. Mobile menu without JS falls back to the footer nav.
{
  const ctx = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await ctx.newPage();
  await page.goto(base + '/', { waitUntil: 'networkidle' });
  const fallback = page.locator('[data-menu-fallback]');
  check('no-JS menu link visible', await fallback.isVisible());
  check(
    'no-JS menu link targets footer nav',
    (await fallback.getAttribute('href')) === '#footer-nav',
  );
  await ctx.close();
}

// 4. Form with JS: empty submit → inline errors + focused summary; valid → success.
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(base + '/contact?reason=research', { waitUntil: 'networkidle' });
  check('?reason= prefills the reason', (await page.inputValue('#reason')) === 'research');
  await page.fill('#name', 'Test Person');
  await page.click('[data-submit]');
  await page.waitForSelector('[data-form-summary]:not([hidden])');
  check('JS: error summary focused', (await focused(page)).startsWith('div'));
  check('JS: typed values kept', (await page.inputValue('#name')) === 'Test Person');
  check('JS: email marked invalid', (await page.getAttribute('#email', 'aria-invalid')) === 'true');
  check(
    'JS: error linked via aria-describedby',
    ((await page.getAttribute('#email', 'aria-describedby')) ?? '').includes('email-error'),
  );
  await page.fill('#email', 'test@example.com');
  await page.fill('#message', 'I run a drone lab and would like to talk about a collaboration.');
  await page.click('[data-submit]');
  await page
    .waitForSelector('[data-form-success]:not([hidden])', { timeout: 10000 })
    .catch(() => {});
  check('JS: success state shown and focused', (await focused(page)).includes('Sent.'));
  await page.close();
}

// 5. Form without JS: server-rendered errors keep values; valid POST shows success.
{
  const ctx = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 900 },
  });
  const page = await ctx.newPage();
  await page.goto(base + '/contact', { waitUntil: 'networkidle' });
  // Native validation blocks obviously bad input without JS; this case passes the browser but not Zod.
  check(
    'no-JS: native validation blocks a bad email',
    (await page.getAttribute('#email', 'type')) === 'email',
  );
  await page.fill('#name', '   ');
  await page.fill('#email', 'kept@example.com');
  await page.selectOption('#reason', 'hardware');
  await page.fill('#message', 'A hardware project about flight controllers for a student team.');
  await page.click('[data-submit]');
  await page.waitForLoadState('networkidle');
  check(
    'no-JS: server error summary rendered',
    await page.locator('[data-form-summary]').isVisible(),
  );
  check('no-JS: name error shown', await page.locator('#name-error').isVisible());
  check(
    'no-JS: values kept after POST',
    (await page.inputValue('#email')) === 'kept@example.com' &&
      (await page.inputValue('#reason')) === 'hardware',
  );
  await page.fill('#name', 'No Script');
  await page.fill('#email', 'test@example.com');
  await page.selectOption('#reason', 'internship');
  await page.fill('#message', 'Asking about a summer internship on embedded firmware.');
  await page.click('[data-submit]');
  await page.waitForLoadState('networkidle');
  check('no-JS: success rendered', await page.locator('[data-form-success]').isVisible());
  await ctx.close();
}

// 6. Honeypot: a filled trap field reports success but nothing is sent (see server log).
{
  const page = await browser.newPage();
  await page.goto(base + '/contact', { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    document.querySelector('#website').value = 'http://spam.example';
  });
  await page.fill('#name', 'Bot');
  await page.fill('#email', 'bot@example.com');
  await page.selectOption('#reason', 'other');
  await page.fill('#message', 'Buy cheap backlinks now, limited offer for your site.');
  await page.click('[data-submit]');
  await page
    .waitForSelector('[data-form-success]:not([hidden])', { timeout: 10000 })
    .catch(() => {});
  check('honeypot: bot sees success', await page.locator('[data-form-success]').isVisible());
  await page.close();
}

await browser.close();
console.log(results.join('\n'));

// Check 10: the contact form end to end under wrangler dev, with Resend replaced by a local stub.
// A second wrangler dev instance runs with RESEND_API_URL pointing at the stub; the form is filled
// in Edge (JS on, arriving with ?reason=internship), and the request Resend would have received is
// printed: from, to, reply-to, subject, and both bodies.
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const STUB_PORT = 8790;
const APP_PORT = 8788;
const APP = `http://127.0.0.1:${APP_PORT}`;

const captured = [];
const stub = createServer((req, res) => {
  let body = '';
  req.on('data', (c) => (body += c));
  req.on('end', () => {
    captured.push({
      method: req.method,
      url: req.url,
      auth: req.headers.authorization,
      body: JSON.parse(body || '{}'),
    });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ id: 'stub-1' }));
  });
});
await new Promise((r) => stub.listen(STUB_PORT, '127.0.0.1', r));

const wrangler = spawn(
  'npx',
  [
    'wrangler',
    'dev',
    '--port',
    String(APP_PORT),
    '--ip',
    '127.0.0.1',
    '--var',
    'RESEND_API_KEY:re_stub_key',
    '--var',
    `RESEND_API_URL:http://127.0.0.1:${STUB_PORT}`,
    '--var',
    'PRE_LAUNCH:false',
  ],
  { shell: true, stdio: ['ignore', 'pipe', 'ignore'] },
);
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('wrangler dev did not start')), 90000);
  wrangler.stdout.on('data', (d) => {
    if (String(d).includes('Ready on')) {
      clearTimeout(timer);
      resolve();
    }
  });
});

let ok = true;
const report = (pass, text) => {
  ok &&= pass;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${text}`);
};

const browser = await chromium.launch({ channel: 'msedge' });
try {
  const page = await browser.newPage();
  await page.goto(`${APP}/contact?reason=internship`, { waitUntil: 'networkidle' });
  report(
    (await page.inputValue('#reason')) === 'internship',
    '?reason=internship preselects "Internship"',
  );
  await page.fill('#name', 'Asha <Test>');
  await page.fill('#email', 'asha@example.com');
  await page.fill(
    '#message',
    'Hello Vedant,\nI would like to talk about a summer internship on flight software.',
  );
  await page.click('[data-submit]');
  await page.waitForSelector('[data-form-success]:not([hidden])', { timeout: 15000 });
  report(true, 'success state shown after submit');

  const sent = captured.find((c) => c.url === '/emails');
  report(Boolean(sent), `stub received ${captured.length} request(s)`);
  if (sent) {
    const b = sent.body;
    console.log('\nCaptured request to the Resend stub:');
    console.log(`  ${sent.method} ${sent.url}   Authorization: ${sent.auth}`);
    console.log(`  from:     ${b.from}`);
    console.log(`  to:       ${JSON.stringify(b.to)}`);
    console.log(`  reply_to: ${b.reply_to}`);
    console.log(`  subject:  ${b.subject}`);
    console.log(
      '  text:\n' +
        b.text
          .split('\n')
          .map((l) => '    | ' + l)
          .join('\n'),
    );
    console.log(
      '  html:\n' +
        b.html
          .split('\n')
          .map((l) => '    | ' + l)
          .join('\n'),
    );
    report(
      b.from === 'Vedant Somani <hello@vedantsomani.tech>',
      'from is Vedant Somani <hello@vedantsomani.tech>',
    );
    report(
      JSON.stringify(b.to) === '["hello@vedantsomani.tech"]',
      'to defaults to hello@vedantsomani.tech (CONTACT_TO_EMAIL unset)',
    );
    report(b.reply_to === 'asha@example.com', 'reply-to is the sender');
    report(
      b.subject === 'New message — Asha <Test> (Internship)',
      'subject is "New message — {name} ({reason})"',
    );
    report(
      b.text.startsWith(
        'Name: Asha <Test>\nEmail: asha@example.com\nReason: Internship\n\nMessage:\n',
      ),
      'text body: one field per line, then Message:',
    );
    report(
      b.html.includes('Asha &lt;Test&gt;') && !b.html.includes('<Test>'),
      'html body escapes input',
    );
  }

  // The same form with JavaScript off: a plain POST, answered by the on-demand /contact page.
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const nojs = await ctx.newPage();
  await nojs.goto(`${APP}/contact?reason=research`, { waitUntil: 'load' });
  report(
    (await nojs.inputValue('#reason')) === 'research',
    'no-JS: ?reason=research preselects "Research collaboration"',
  );
  await nojs.fill('#name', 'No Script');
  await nojs.fill('#email', 'noscript@example.com');
  await nojs.fill('#message', 'Writing with JavaScript off about a research collaboration.');
  await nojs.click('[data-submit]');
  await nojs.waitForLoadState('load');
  report(
    await nojs.locator('[data-form-success]').isVisible(),
    'no-JS: success page rendered by the server',
  );
  const second = captured.filter((c) => c.url === '/emails')[1];
  report(
    second?.body.subject === 'New message — No Script (Research collaboration)',
    `no-JS: stub received "${second?.body.subject}"`,
  );
  await ctx.close();
} finally {
  await browser.close();
  wrangler.kill();
  stub.close();
  // npx on Windows leaves the workerd child running; end the process tree.
  if (process.platform === 'win32') spawn('taskkill', ['/pid', String(wrangler.pid), '/T', '/F']);
}
// The wrangler child's pipes would keep Node alive; exit explicitly.
process.exit(ok ? 0 : 1);

// Contact as a transmission (SITE_SPEC §4.5): a decorative trace that answers the visitor's typing.
// It measures nothing but keystrokes in this form, and says so on the page. It idles as a faint
// flat line, swells while you type, and pulses while the real request is in flight
// (data-sending on the form). Draws only on screen and while the tab is visible; under reduced
// motion it draws one still frame.
import { reducedMotion } from './lifecycle';

export function initTransmit(form: HTMLFormElement, canvas: HTMLCanvasElement): () => void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return () => {};
  const reduce = reducedMotion();
  let energy = 0;
  let raf = 0;
  let last = 0;
  let t = 0;
  let onScreen = true;
  let w = 1;
  let h = 1;

  const size = () => {
    const r = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = Math.max(1, r.width);
    h = Math.max(1, r.height);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  const draw = () => {
    const sending = form.dataset.sending !== undefined;
    const amp = Math.min(1, energy) * h * 0.38 + (sending ? h * 0.3 : 0) + 1;
    ctx.clearRect(0, 0, w, h);
    // Rules: a centre line and the frame's ticks.
    ctx.strokeStyle = 'rgb(93 101 91 / 0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    for (let x = 0; x <= w; x += 40) {
      ctx.moveTo(x, h / 2 - 3);
      ctx.lineTo(x, h / 2 + 3);
    }
    ctx.stroke();
    // The trace.
    ctx.strokeStyle = '#ff2e3b';
    ctx.shadowColor = 'rgb(255 46 59 / 0.7)';
    ctx.shadowBlur = 6;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let x = 0; x <= w; x += 2) {
      const u = x / w;
      const env = Math.sin(Math.PI * u);
      const y =
        h / 2 +
        env *
          amp *
          (0.6 * Math.sin(u * 38 + t * 9) +
            0.3 * Math.sin(u * 91 - t * 14) +
            0.1 * Math.sin(u * 210 + t * 30));
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  };

  const frame = (now: number) => {
    raf = 0;
    if (!onScreen || document.hidden) return;
    const dt = Math.min(0.05, last ? (now - last) / 1000 : 1 / 60);
    last = now;
    t += dt;
    energy *= Math.exp(-dt * 1.6);
    draw();
    raf = requestAnimationFrame(frame);
  };
  const wake = () => {
    if (reduce) return draw();
    if (!raf) {
      last = 0;
      raf = requestAnimationFrame(frame);
    }
  };

  const onInput = () => {
    energy = Math.min(1.2, energy + 0.18);
    wake();
  };
  form.addEventListener('input', onInput);
  const io = new IntersectionObserver(([e]) => {
    onScreen = e.isIntersecting;
    wake();
  });
  io.observe(canvas);
  const ro = new ResizeObserver(() => {
    size();
    draw();
  });
  ro.observe(canvas);
  const mo = new MutationObserver(wake);
  mo.observe(form, { attributes: true, attributeFilter: ['data-sending'] });
  document.addEventListener('visibilitychange', wake);
  size();
  wake();

  return () => {
    cancelAnimationFrame(raf);
    form.removeEventListener('input', onInput);
    io.disconnect();
    ro.disconnect();
    mo.disconnect();
    document.removeEventListener('visibilitychange', wake);
  };
}

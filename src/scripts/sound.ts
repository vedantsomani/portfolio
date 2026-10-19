// Sound design (SITE_SPEC §4.9): everything is synthesised with Web Audio, so there are no files to
// license or load. Off by default; the choice is remembered. A context only starts inside a user
// gesture (the title gate or the nav toggle), as browsers require.
//   drone      two detuned low oscillators and filtered noise under a slow-moving low-pass
//   heartbeat  two thumps, the second softer: the tear opening
//   boom       a sub hit with a noise tail: each opening credit
//   static     a band-passed noise burst: signal cuts
//   tick       a short click: HUD lock
// The film's effects (scheduled by film.ts against its timeline):
//   engine / engine-cut   the lander's rumble on the way down, cut at touchdown
//   clunk      a heavy landing hit with a metal ring
//   hiss       hydraulics: the ramp going down
//   servo      the machine's head turning: a whine gliding up
//   creak      a door swinging (the lab's glass door, the breaker panel's)
//   holo       the hologram waking: two shimmering tones and a crackle
//   radio      the squelch that opens each radio line: a burst of static and a short tone
//   scan       the machine's scanner: a pulsing whine
//   powerdown  the machine giving up: a falling tone
//   breaker    the main going back on: a hard click, then the hum of the mains
//   tube       a fluorescent tube striking: ticks and a buzz
//   seal       the helmet coming off: two latch clicks and the seal breaking (a short hiss)
//   title      the title card: a low hit
//   step-metal a boot on the lander's ramp: a dull hit and a short ring
//   step       a boot on broken concrete and grit: soft, a little gravelly
//   amb-*      the place under it all, crossfaded shot to shot: wind (the street), dark (the dead
//              lab's room tone), hum (the mains back on: 50 Hz and its harmonics, the tubes'
//              buzz); amb-off fades it out
// radioVoice() plays a recorded line through a radio's narrow band.
type Cue = 'heartbeat' | 'boom' | 'static' | 'tick';
export type FilmCue =
  | 'engine'
  | 'engine-cut'
  | 'clunk'
  | 'hiss'
  | 'servo'
  | 'creak'
  | 'holo'
  | 'radio'
  | 'scan'
  | 'powerdown'
  | 'breaker'
  | 'tube'
  | 'seal'
  | 'title'
  | 'step-metal'
  | 'step'
  | 'amb-wind'
  | 'amb-dark'
  | 'amb-hum'
  | 'amb-off';
let engine: { stop: (at: number) => void } | null = null;
let bed: { kind: string; stop: (at: number) => void } | null = null;

const KEY = 'sound';
let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let noise: AudioBuffer | null = null;
let droneOn = false;
const listeners = new Set<(on: boolean) => void>();

const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

export function soundOn(): boolean {
  try {
    return localStorage.getItem(KEY) === 'on';
  } catch {
    return false;
  }
}

function save(on: boolean) {
  try {
    localStorage.setItem(KEY, on ? 'on' : 'off');
  } catch {
    /* blocked storage: the choice lasts this page only */
  }
}

function boot(): AudioContext | null {
  if (ctx) return ctx;
  const AC =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  ctx = new AC();
  master = ctx.createGain();
  master.gain.value = 0;
  master.connect(ctx.destination);
  noise = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
  const data = noise.getChannelData(0);
  for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  return ctx;
}

function noiseSource(c: AudioContext) {
  const src = c.createBufferSource();
  src.buffer = noise;
  src.loop = true;
  return src;
}

function drone(c: AudioContext, out: AudioNode) {
  if (droneOn) return;
  droneOn = true;
  const bus = c.createGain();
  bus.gain.value = 0;
  bus.gain.setTargetAtTime(0.5, c.currentTime, 3);
  const lp = c.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 160;
  lp.Q.value = 6;
  const lfo = c.createOscillator();
  const lfoGain = c.createGain();
  lfo.frequency.value = 0.05;
  lfoGain.gain.value = 70;
  lfo.connect(lfoGain).connect(lp.frequency);
  lfo.start();
  for (const [f, type, g] of [
    [41.2, 'sawtooth', 0.09],
    [41.7, 'sawtooth', 0.09],
    [61.7, 'triangle', 0.05],
  ] as const) {
    const o = c.createOscillator();
    const og = c.createGain();
    o.type = type;
    o.frequency.value = f;
    og.gain.value = g;
    o.connect(og).connect(lp);
    o.start();
  }
  const wind = noiseSource(c);
  const bp = c.createBiquadFilter();
  bp.type = 'bandpass';
  bp.frequency.value = 420;
  bp.Q.value = 0.7;
  const wg = c.createGain();
  wg.gain.value = 0.025;
  wind.connect(bp).connect(wg).connect(bus);
  wind.start();
  lp.connect(bus).connect(out);
}

function thump(c: AudioContext, out: AudioNode, at: number, level: number) {
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = 'sine';
  o.frequency.setValueAtTime(70, at);
  o.frequency.exponentialRampToValueAtTime(34, at + 0.14);
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(level, at + 0.012);
  g.gain.exponentialRampToValueAtTime(0.0001, at + 0.22);
  o.connect(g).connect(out);
  o.start(at);
  o.stop(at + 0.3);
}

function burst(
  c: AudioContext,
  out: AudioNode,
  at: number,
  dur: number,
  freq: number,
  q: number,
  level: number,
) {
  const src = noiseSource(c);
  const bp = c.createBiquadFilter();
  bp.type = 'bandpass';
  bp.frequency.value = freq;
  bp.Q.value = q;
  const g = c.createGain();
  g.gain.setValueAtTime(level, at);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  src.connect(bp).connect(g).connect(out);
  src.start(at, Math.random());
  src.stop(at + dur + 0.05);
}

// The ambient bed: one at a time, the old one fading out over a second as the new one fades in.
function ambient(c: AudioContext, out: AudioNode, kind: string | null, at: number) {
  if (bed?.kind === kind) return;
  bed?.stop(at);
  bed = null;
  if (!kind) return;
  const bus = c.createGain();
  bus.gain.setValueAtTime(0.0001, at);
  bus.gain.exponentialRampToValueAtTime(1, at + 1.4);
  bus.connect(out);
  const stops: AudioScheduledSourceNode[] = [];
  const osc = (f: number, type: OscillatorType, level: number) => {
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = type;
    o.frequency.value = f;
    g.gain.value = level;
    o.connect(g).connect(bus);
    o.start(at);
    stops.push(o);
  };
  const hiss = (type: BiquadFilterType, f: number, q: number, level: number, wobble = 0) => {
    const src = noiseSource(c);
    const flt = c.createBiquadFilter();
    flt.type = type;
    flt.frequency.value = f;
    flt.Q.value = q;
    const g = c.createGain();
    g.gain.value = level;
    if (wobble) {
      // Gusts: the filter and the level drift slowly, out of step with each other.
      for (const [rate, depth, target] of [
        [0.11, f * 0.45, flt.frequency],
        [0.07, level * 0.6, g.gain],
      ] as const) {
        const lfo = c.createOscillator();
        const lg = c.createGain();
        lfo.frequency.value = rate * wobble;
        lg.gain.value = depth;
        lfo.connect(lg).connect(target);
        lfo.start(at);
        stops.push(lfo);
      }
    }
    src.connect(flt).connect(g).connect(bus);
    src.start(at, Math.random() * 1.5);
    stops.push(src);
  };
  if (kind === 'wind') {
    hiss('lowpass', 650, 0.6, 0.06, 1);
    hiss('bandpass', 1600, 0.5, 0.012, 1.7);
  } else if (kind === 'dark') {
    hiss('lowpass', 120, 0.7, 0.07);
    osc(38, 'sine', 0.018);
  } else if (kind === 'hum') {
    osc(50, 'sine', 0.03);
    osc(100, 'triangle', 0.012);
    osc(150, 'sine', 0.006);
    hiss('lowpass', 220, 0.8, 0.025);
    hiss('bandpass', 3000, 9, 0.004);
  }
  bed = {
    kind,
    stop(t) {
      bus.gain.cancelScheduledValues(t);
      bus.gain.setTargetAtTime(0.0001, t, 0.4);
      for (const n of stops) n.stop(t + 2.5);
    },
  };
}

export function cue(name: Cue): void {
  if (!ctx || !master || !soundOn() || ctx.state !== 'running') return;
  const now = ctx.currentTime + 0.01;
  switch (name) {
    case 'heartbeat':
      thump(ctx, master, now, 0.9);
      thump(ctx, master, now + 0.26, 0.55);
      break;
    case 'boom': {
      thump(ctx, master, now, 1);
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.frequency.setValueAtTime(38, now);
      g.gain.setValueAtTime(0.5, now);
      g.gain.exponentialRampToValueAtTime(0.0001, now + 3);
      o.connect(g).connect(master);
      o.start(now);
      o.stop(now + 3.1);
      burst(ctx, master, now, 2.4, 180, 0.5, 0.12);
      break;
    }
    case 'static':
      burst(ctx, master, now, 0.28, 2400, 0.6, 0.18);
      break;
    case 'tick':
      burst(ctx, master, now, 0.03, 5200, 2, 0.12);
      break;
  }
}

function tone(
  c: AudioContext,
  out: AudioNode,
  at: number,
  f0: number,
  f1: number,
  dur: number,
  type: OscillatorType,
  level: number,
) {
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = type;
  o.frequency.setValueAtTime(f0, at);
  o.frequency.exponentialRampToValueAtTime(f1, at + dur);
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(level, at + Math.min(0.3, dur / 3));
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  o.connect(g).connect(out);
  o.start(at);
  o.stop(at + dur + 0.05);
}

/** One of the film's sound effects, now (if sound is on). */
export function filmCue(name: FilmCue): void {
  if (!ctx || !master || !soundOn() || ctx.state !== 'running') return;
  const c = ctx;
  const out = master;
  const now = c.currentTime + 0.01;
  switch (name) {
    case 'engine': {
      engine?.stop(now);
      const src = noiseSource(c);
      const lp = c.createBiquadFilter();
      lp.type = 'lowpass';
      lp.frequency.setValueAtTime(220, now);
      lp.frequency.linearRampToValueAtTime(420, now + 4);
      const g = c.createGain();
      g.gain.setValueAtTime(0.0001, now);
      g.gain.exponentialRampToValueAtTime(0.5, now + 2.5);
      src.connect(lp).connect(g).connect(out);
      src.start(now);
      const sub = c.createOscillator();
      const sg = c.createGain();
      sub.frequency.value = 31;
      sg.gain.setValueAtTime(0.0001, now);
      sg.gain.exponentialRampToValueAtTime(0.35, now + 2);
      sub.connect(sg).connect(out);
      sub.start(now);
      engine = {
        stop(at) {
          g.gain.cancelScheduledValues(at);
          g.gain.setTargetAtTime(0.0001, at, 0.25);
          sg.gain.cancelScheduledValues(at);
          sg.gain.setTargetAtTime(0.0001, at, 0.25);
          src.stop(at + 1.5);
          sub.stop(at + 1.5);
        },
      };
      break;
    }
    case 'engine-cut':
      engine?.stop(now);
      engine = null;
      break;
    case 'clunk':
      thump(c, out, now, 1);
      burst(c, out, now, 0.6, 1900, 9, 0.07);
      break;
    case 'hiss':
      burst(c, out, now, 2.6, 3200, 0.9, 0.06);
      tone(c, out, now, 90, 70, 2.6, 'sawtooth', 0.03);
      break;
    case 'servo':
      tone(c, out, now, 180, 340, 0.9, 'sawtooth', 0.025);
      tone(c, out, now + 0.05, 362, 680, 0.85, 'square', 0.008);
      break;
    case 'creak':
      burst(c, out, now, 0.9, 520, 14, 0.09);
      tone(c, out, now, 140, 95, 0.8, 'triangle', 0.03);
      break;
    case 'holo':
      tone(c, out, now, 880, 884, 3.2, 'sine', 0.05);
      tone(c, out, now + 0.15, 1320, 1318, 3.0, 'sine', 0.03);
      for (let k = 0; k < 5; k++) burst(c, out, now + k * 0.13, 0.08, 4200, 1.2, 0.05);
      break;
    case 'radio':
      burst(c, out, now, 0.14, 1800, 0.8, 0.09);
      tone(c, out, now + 0.02, 1240, 1240, 0.07, 'sine', 0.035);
      break;
    case 'scan': {
      // A whine pulsing six times a second for the three seconds the beam is up.
      const o = c.createOscillator();
      const am = c.createOscillator();
      const amg = c.createGain();
      const g = c.createGain();
      o.type = 'sine';
      o.frequency.setValueAtTime(820, now);
      o.frequency.linearRampToValueAtTime(980, now + 3.2);
      am.frequency.value = 6;
      amg.gain.value = 0.012;
      g.gain.setValueAtTime(0.0001, now);
      g.gain.linearRampToValueAtTime(0.014, now + 0.3);
      g.gain.setValueAtTime(0.014, now + 2.9);
      g.gain.linearRampToValueAtTime(0.0001, now + 3.3);
      am.connect(amg).connect(g.gain);
      o.connect(g).connect(out);
      o.start(now);
      am.start(now);
      o.stop(now + 3.4);
      am.stop(now + 3.4);
      break;
    }
    case 'powerdown':
      tone(c, out, now, 420, 55, 1.3, 'sawtooth', 0.02);
      burst(c, out, now + 0.1, 0.5, 900, 1.5, 0.03);
      break;
    case 'breaker':
      thump(c, out, now, 0.6);
      burst(c, out, now, 0.035, 4200, 2, 0.16);
      tone(c, out, now + 0.15, 50, 50, 3.2, 'sine', 0.05);
      tone(c, out, now + 0.15, 100, 100, 3.2, 'triangle', 0.015);
      break;
    case 'tube':
      for (let k = 0; k < 3; k++)
        burst(c, out, now + k * 0.07 + Math.random() * 0.04, 0.02, 3000, 3, 0.05);
      tone(c, out, now + 0.2, 100, 100, 1.6, 'sawtooth', 0.006);
      break;
    case 'seal':
      burst(c, out, now, 0.02, 3600, 4, 0.08);
      burst(c, out, now + 0.11, 0.02, 3300, 4, 0.07);
      burst(c, out, now + 0.2, 0.7, 5200, 0.7, 0.035);
      break;
    case 'step-metal':
      thump(c, out, now, 0.22);
      burst(c, out, now, 0.12, 1900, 12, 0.035);
      tone(c, out, now, 540, 520, 0.18, 'triangle', 0.008);
      break;
    case 'step':
      thump(c, out, now, 0.08);
      burst(c, out, now, 0.07, 700 + Math.random() * 300, 0.9, 0.03);
      break;
    case 'amb-wind':
    case 'amb-dark':
    case 'amb-hum':
      ambient(c, out, name.slice(4), now);
      break;
    case 'amb-off':
      ambient(c, out, null, now);
      break;
    case 'title':
      thump(c, out, now, 0.8);
      tone(c, out, now, 41, 38, 3, 'sine', 0.3);
      break;
  }
}

const voices = new Map<string, Promise<AudioBuffer | null>>();

/** A recorded radio line (if sound is on): band-limited and lightly driven, with static under it. */
export function radioVoice(url: string): void {
  if (!ctx || !master || !soundOn() || ctx.state !== 'running') return;
  const c = ctx;
  const out = master;
  if (!voices.has(url)) {
    voices.set(
      url,
      fetch(url)
        .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(String(r.status)))))
        .then((b) => c.decodeAudioData(b))
        .catch(() => null),
    );
  }
  void voices.get(url)?.then((buf) => {
    if (!buf || !soundOn()) return;
    const now = c.currentTime + 0.12; // after the squelch
    const src = c.createBufferSource();
    src.buffer = buf;
    const hp = c.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 320;
    const lp = c.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 3000;
    const drive = c.createWaveShaper();
    const curve = new Float32Array(256);
    for (let i = 0; i < 256; i++) {
      const x = (i / 255) * 2 - 1;
      curve[i] = Math.tanh(2.2 * x);
    }
    drive.curve = curve;
    const g = c.createGain();
    g.gain.value = 0.55;
    src.connect(hp).connect(lp).connect(drive).connect(g).connect(out);
    src.start(now);
    burst(c, out, now, buf.duration + 0.1, 2200, 0.5, 0.012);
    burst(c, out, now + buf.duration, 0.09, 1800, 0.8, 0.06);
  });
}

/** Turn sound on or off. Call from inside a click or key handler. */
export function setSound(on: boolean): void {
  save(on);
  if (on) {
    const c = boot();
    if (c && master) {
      void c.resume();
      if (!reduce()) drone(c, master);
      master.gain.setTargetAtTime(0.6, c.currentTime, 0.4);
    }
  } else if (ctx && master) {
    master.gain.setTargetAtTime(0, ctx.currentTime, 0.2);
  }
  listeners.forEach((fn) => fn(on));
}

export function onSoundChange(fn: (on: boolean) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Sound was left on last visit: resume on the first gesture, as browsers require. */
export function resumeOnGesture(): void {
  if (!soundOn() || ctx) return;
  const go = () => {
    window.removeEventListener('pointerdown', go);
    window.removeEventListener('keydown', go);
    if (soundOn()) setSound(true);
  };
  window.addEventListener('pointerdown', go, { once: true });
  window.addEventListener('keydown', go, { once: true });
}

// Hidden tab: suspend the context, so nothing plays (or burns CPU) out of sight; resume on return
// if sound is still on.
document.addEventListener('visibilitychange', () => {
  if (!ctx) return;
  if (document.hidden) void ctx.suspend();
  else if (soundOn()) void ctx.resume();
});

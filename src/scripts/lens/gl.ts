// OGL renderer for the X-ray lens. Two passes per frame:
//   1. mask: a soft brush at the lens position is max-blended into a ping-pong target that decays
//      every frame (0.92 per 60 Hz frame), so fast strokes leave a fading trail;
//   2. composite: photo and x-ray mixed by the mask, its edge pushed around by 2D simplex noise
//      (~12 px, slow drift) with a thin --oxblood-hi rim where the copper layer begins.
// Textures are the <img> elements the page already decoded, mapped with object-fit: cover maths so
// the canvas lines up with the photo underneath it pixel for pixel.
import { Mesh, Program, Renderer, RenderTarget, Texture, Triangle } from 'ogl';
import type { LensFrame, LensRenderer } from './index';

const DPR_CAP = 1.5;
const DECAY = 0.92;
const NOISE_PX = 12;

const vertex = /* glsl */ `
  attribute vec2 uv;
  attribute vec2 position;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position, 0.0, 1.0);
  }
`;

const maskFragment = /* glsl */ `
  precision highp float;
  uniform sampler2D tPrev;
  uniform vec2 uRes;
  uniform vec2 uPos;
  uniform float uRadius;
  uniform float uDecay;
  varying vec2 vUv;
  void main() {
    float prev = texture2D(tPrev, vUv).r * uDecay;
    float d = distance(vUv * uRes, uPos);
    float brush = uRadius > 0.5 ? 1.0 - smoothstep(uRadius * 0.6, uRadius, d) : 0.0;
    gl_FragColor = vec4(max(prev, brush), 0.0, 0.0, 1.0);
  }
`;

// 2D simplex noise: Ashima Arts / Stefan Gustavson (MIT).
const compositeFragment = /* glsl */ `
  precision highp float;
  uniform sampler2D tPhoto;
  uniform sampler2D tXray;
  uniform sampler2D tMask;
  uniform vec2 uRes;
  uniform vec2 uImg;
  uniform float uTime;
  uniform float uNoise;
  uniform vec3 uRim;
  varying vec2 vUv;

  vec3 permute(vec3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
  float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
    vec2 i = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod(i, 289.0);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m;
    m = m * m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
    vec3 g;
    g.x = a0.x * x0.x + h.x * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
  }

  void main() {
    // object-fit: cover, centred.
    float scale = max(uRes.x / uImg.x, uRes.y / uImg.y);
    vec2 size = uImg * scale;
    vec2 uv = (vUv * uRes - (uRes - size) * 0.5) / size;

    vec2 p = vUv * uRes;
    vec2 n = vec2(snoise(p * 0.006 + uTime * 0.05), snoise(p * 0.006 + 17.0 - uTime * 0.05));
    float m = texture2D(tMask, vUv + n * uNoise / uRes).r;

    float reveal = smoothstep(0.46, 0.54, m);
    float rim = (1.0 - smoothstep(0.0, 0.035, abs(m - 0.5))) * step(0.02, m);

    vec3 photo = texture2D(tPhoto, uv).rgb;
    vec3 xray = texture2D(tXray, uv).rgb;
    vec3 color = mix(photo, xray, reveal);
    gl_FragColor = vec4(mix(color, uRim, rim * 0.9), 1.0);
  }
`;

const loaded = (img: HTMLImageElement) =>
  img.complete && img.naturalWidth ? img.decode().catch(() => {}) : img.decode();

export async function createGLLens(
  stage: HTMLElement,
  photo: HTMLImageElement,
  xray: HTMLImageElement,
): Promise<LensRenderer> {
  await Promise.all([loaded(photo), loaded(xray)]);

  const renderer = new Renderer({
    dpr: Math.min(window.devicePixelRatio || 1, DPR_CAP),
    alpha: false,
    antialias: false,
    depth: false,
    powerPreference: 'low-power',
    preserveDrawingBuffer: true,
  });
  const gl = renderer.gl;
  if (!gl) throw new Error('No WebGL context');
  const canvas = gl.canvas as HTMLCanvasElement;
  canvas.className = 'lens__canvas';
  canvas.setAttribute('aria-hidden', 'true');

  const texture = (image: HTMLImageElement) =>
    new Texture(gl, { image, generateMipmaps: false, minFilter: gl.LINEAR });
  const tPhoto = texture(photo);
  const tXray = texture(xray);

  const geometry = new Triangle(gl);
  let css = { w: 1, h: 1 };
  // Mask at half resolution: it is soft everywhere, so the saving is free.
  const target = () =>
    new RenderTarget(gl, {
      width: Math.max(1, Math.round(css.w / 2)),
      height: Math.max(1, Math.round(css.h / 2)),
      depth: false,
    });
  let read = target();
  let write = target();

  const maskProgram = new Program(gl, {
    vertex,
    fragment: maskFragment,
    uniforms: {
      tPrev: { value: read.texture },
      uRes: { value: [1, 1] },
      uPos: { value: [0, 0] },
      uRadius: { value: 0 },
      uDecay: { value: DECAY },
    },
    depthTest: false,
  });
  const compositeProgram = new Program(gl, {
    vertex,
    fragment: compositeFragment,
    uniforms: {
      tPhoto: { value: tPhoto },
      tXray: { value: tXray },
      tMask: { value: write.texture },
      uRes: { value: [1, 1] },
      uImg: { value: [photo.naturalWidth, photo.naturalHeight] },
      uTime: { value: 0 },
      uNoise: { value: NOISE_PX },
      uRim: { value: [0xe2 / 255, 0x59 / 255, 0x64 / 255] },
    },
    depthTest: false,
  });
  const maskMesh = new Mesh(gl, { geometry, program: maskProgram });
  const compositeMesh = new Mesh(gl, { geometry, program: compositeProgram });

  // Swap textures if the art-directed <picture> switches source (e.g. crossing 1024 px).
  const refresh = () => {
    tPhoto.image = photo;
    tXray.image = xray;
    tPhoto.needsUpdate = true;
    tXray.needsUpdate = true;
    compositeProgram.uniforms.uImg.value = [photo.naturalWidth, photo.naturalHeight];
  };
  photo.addEventListener('load', refresh);
  xray.addEventListener('load', refresh);

  function resize() {
    const rect = stage.getBoundingClientRect();
    css = { w: Math.max(1, rect.width), h: Math.max(1, rect.height) };
    renderer.setSize(css.w, css.h);
    read = target();
    write = target();
    maskProgram.uniforms.uRes.value = [css.w, css.h];
    compositeProgram.uniforms.uRes.value = [css.w, css.h];
  }
  resize();
  stage.append(canvas);

  let shown = false;
  return {
    render({ x, y, r, dt, time }: LensFrame) {
      maskProgram.uniforms.tPrev.value = read.texture;
      maskProgram.uniforms.uPos.value = [x, css.h - y];
      maskProgram.uniforms.uRadius.value = r;
      maskProgram.uniforms.uDecay.value = Math.pow(DECAY, dt * 60);
      renderer.render({ scene: maskMesh, target: write });

      compositeProgram.uniforms.tMask.value = write.texture;
      compositeProgram.uniforms.uTime.value = time;
      renderer.render({ scene: compositeMesh });
      [read, write] = [write, read];

      if (!shown) {
        shown = true;
        // Cross-fade over the photo once the first frame exists: no flash, no layout shift.
        requestAnimationFrame(() => canvas.classList.add('is-ready'));
      }
    },
    resize,
    dispose() {
      photo.removeEventListener('load', refresh);
      xray.removeEventListener('load', refresh);
      canvas.remove();
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    },
  };
}

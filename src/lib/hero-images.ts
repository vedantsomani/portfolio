import { getImage } from 'astro:assets';
import type { ImageMetadata } from 'astro';
import standIn from '../assets/work/workspace.jpg';
import { hero } from '../data/site';

// Hero portrait. Drop a photo of Vedant at src/assets/portrait/vedant.(jpg|jpeg|png|webp) and it
// replaces the workspace stand-in on the next build; nothing else changes. The machine-vision layer
// is computed from this same photo in the lens shader, so there is no second image to keep aligned.
const found = import.meta.glob<ImageMetadata>('../assets/portrait/vedant.{jpg,jpeg,png,webp}', {
  eager: true,
  import: 'default',
});
const portrait = Object.values(found)[0] as ImageMetadata | undefined;
const heroPhoto = portrait ?? standIn;
/** The hero photo itself, for the briefing's identity card. */
export const HERO_PHOTO = heroPhoto;
export const HERO_IS_STAND_IN = !portrait;
// The crop's focal point, shared by the CSS object-position and the lens shader. The desk photo's is
// the laptop and the printer arm; the portrait's is hero.focus.
export const HERO_FOCUS: [number, number] = portrait ? hero.focus : [0.6, 0.46];

// Desktop (≥ 1024px): preloaded with fetchpriority="high" through a media-scoped <link>. Mobile:
// normal priority. The photo is object-fit: cover, so the width it is drawn at depends on its
// aspect: a landscape portrait in a tall frame is drawn much wider than the frame. The sizes below
// follow the frames in src/styles/archive/hero.css (desktop: 66vw wide, full height; phones: full
// width, min(68svh, 130vw) tall), so the browser picks a sharp file without over-fetching.
const aspect = heroPhoto.width / heroPhoto.height;
const r = (n: number) => Math.round(n);
export const DESKTOP = '(min-width: 64rem)';
export const DESK_SIZES = `max(66vw, ${r(100 * aspect)}vh)`;
export const MOB_SIZES =
  aspect > 0.75 ? `max(100vw, min(${r(68 * aspect)}vh, ${r(130 * aspect)}vw))` : '100vw';

type Img = Awaited<ReturnType<typeof getImage>>;

const variants = (widths: number[], format: 'avif' | 'jpg', q: number) =>
  Promise.all(widths.map((width) => getImage({ src: heroPhoto, width, format, quality: q })));

const srcset = (imgs: Img[]) => imgs.map((i) => `${i.src} ${i.attributes.width}w`).join(', ');

export async function getHeroImages() {
  const desk = [1280, 1600, 2000, 2400].filter((w) => w <= heroPhoto.width);
  const mob = (aspect > 0.75 ? [640, 1000, 1400, 2000] : [480, 760, 1080]).filter(
    (w) => w <= heroPhoto.width,
  );
  const [deskAvif, deskJpg, mobAvif, mobJpg] = await Promise.all([
    variants(desk.length ? desk : [heroPhoto.width], 'avif', 60),
    variants(desk.length ? desk : [heroPhoto.width], 'jpg', 70),
    variants(mob, 'avif', 42),
    variants(mob, 'jpg', 60),
  ]);
  const fallback = mobJpg[mobJpg.length - 1];
  return {
    width: heroPhoto.width,
    height: heroPhoto.height,
    deskAvif: srcset(deskAvif),
    deskJpg: srcset(deskJpg),
    mobAvif: srcset(mobAvif),
    mobJpg: srcset(mobJpg),
    fallback: {
      src: fallback.src,
      width: Number(fallback.attributes.width),
      height: Number(fallback.attributes.height),
    },
  };
}

export type HeroImages = Awaited<ReturnType<typeof getHeroImages>>;

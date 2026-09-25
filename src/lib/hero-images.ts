import { getImage } from 'astro:assets';
// Both come from one KiCad board file, pixel-aligned via the mounting holes (scripts/kicad-hero.mjs).
import heroPhoto from '../assets/work/saarthi-hero.jpg';
import heroXray from '../assets/work/saarthi-xray.jpg';
// Mobile: a 4:3 cut around the board, taken at identical coordinates from both layers.
import heroPhotoMobile from '../assets/work/saarthi-hero-mobile.jpg';
import heroXrayMobile from '../assets/work/saarthi-xray-mobile.jpg';

// Hero art direction. Mobile: 4:3 crop, ≤ 60 KB, normal priority, so the headline is the intended
// LCP element. Desktop (≥ 1024px): full frame ≤ 150 KB, preloaded with fetchpriority="high"
// through a media-scoped <link> (an <img> can't scope fetchpriority).
// The x-ray layer is AVIF only: it needs JS to appear at all, and every such browser decodes AVIF.
export const DESKTOP = '(min-width: 64rem)';
export const DESK_SIZES = '60vw';

type Src = typeof heroPhoto;
type Img = Awaited<ReturnType<typeof getImage>>;

const variants = (src: Src, widths: number[], format: 'avif' | 'jpg', crop: boolean, q: number) =>
  Promise.all(
    widths.map((width) =>
      getImage({
        src,
        width,
        ...(crop ? { height: Math.round((width * 3) / 4), fit: 'cover' as const } : {}),
        format,
        quality: q,
      }),
    ),
  );

const srcset = (imgs: Img[]) => imgs.map((i) => `${i.src} ${i.attributes.width}w`).join(', ');

export async function getHeroImages() {
  const desk = [1280, 1600, 2400];
  const mob = [480, 760, 1080];
  const [deskAvif, deskJpg, mobAvif, mobJpg, xDesk, xMob] = await Promise.all([
    variants(heroPhoto, desk, 'avif', false, 60),
    variants(heroPhoto, desk, 'jpg', false, 70),
    variants(heroPhotoMobile, mob, 'avif', true, 50),
    variants(heroPhotoMobile, mob, 'jpg', true, 60),
    variants(heroXray, desk, 'avif', false, 60),
    variants(heroXrayMobile, mob, 'avif', true, 55),
  ]);
  const fallback = mobJpg[mobJpg.length - 1];
  return {
    width: heroPhoto.width,
    height: heroPhoto.height,
    deskAvif: srcset(deskAvif),
    deskJpg: srcset(deskJpg),
    mobAvif: srcset(mobAvif),
    mobJpg: srcset(mobJpg),
    xrayDesk: srcset(xDesk),
    xrayMob: srcset(xMob),
    fallback: {
      src: fallback.src,
      width: Number(fallback.attributes.width),
      height: Number(fallback.attributes.height),
    },
  };
}

export type HeroImages = Awaited<ReturnType<typeof getHeroImages>>;

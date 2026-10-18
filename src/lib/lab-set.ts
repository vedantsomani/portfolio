import { getImage } from 'astro:assets';
import type { ImageMetadata } from 'astro';
import { getLabEntries, getProjects, recordIds, statusLabel } from './content';

// The lab set (the home page's hub): Cycles renders of an abandoned laboratory, made by
// blender/lab.py, encoded by scripts/set-images.mjs. Until those files exist the room is simply
// absent and the home page goes from the arrival to the index, so the site always builds.
//   src/data/lab-set.json        each record's on-screen anchor and box in the 16:9 frame, and
//                                which records have a close-up
//   src/assets/set/lab-rest-desk.jpg   the room at rest, the hologram awake (the interface)
//   public/set/lab/close         one close-up per record (the push-in's last frame)
// One composition serves every screen: on tall screens the frame keeps its full height and the
// room pans sideways under a swipe (LabRoom.astro).

export interface Anchor {
  x: number;
  y: number;
  box: [number, number, number, number];
}
interface LabSetData {
  desk: { width: number; height: number; items: Record<string, Anchor> };
  close?: string[];
}

const data = Object.values(
  import.meta.glob<LabSetData>('../data/lab-set.json', { eager: true, import: 'default' }),
)[0];
const stills = import.meta.glob<ImageMetadata>('../assets/set/*.jpg', {
  eager: true,
  import: 'default',
});
const still = (name: string) => stills[`../assets/set/${name}.jpg`];

/** Tall screens pan across the room instead of cropping it. */
export const PAN_ART = '(max-aspect-ratio: 4/5)';

type Img = Awaited<ReturnType<typeof getImage>>;
const srcset = (imgs: Img[]) => imgs.map((i) => `${i.src} ${i.attributes.width}w`).join(', ');

async function art(src: ImageMetadata) {
  const make = (widths: number[], format: 'avif' | 'jpg', quality: number) =>
    Promise.all(
      widths
        .filter((w) => w <= src.width)
        .map((width) => getImage({ src, width, format, quality })),
    );
  const [avif, jpg] = await Promise.all([
    // Quality is set so the dark frames keep enough detail to count as the page's contentful
    // paint (Chrome ignores very low bits-per-pixel images for LCP) while staying small.
    // AVIF up to 4K for large, dense screens (only when the render is that big); JPEG, the
    // fallback, stops at 2400.
    make([960, 1440, 1920, 2400, 3200, 3840], 'avif', 60),
    make([960, 1440, 1920, 2400], 'jpg', 74),
  ]);
  const fallback = jpg[1] ?? jpg[0];
  // Tall screens pan across the frame at the stage's height: 1440 px wide is enough there, and it
  // keeps the first paint light on a phone connection.
  const small = (imgs: Img[]) => imgs.filter((i) => Number(i.attributes.width) <= 1440);
  return {
    avif: srcset(avif),
    jpg: srcset(jpg),
    avifPan: srcset(small(avif)),
    jpgPan: srcset(small(jpg)),
    src: fallback.src,
    width: Number(fallback.attributes.width),
    height: Number(fallback.attributes.height),
  };
}

export interface LabItem {
  id: string;
  href: string;
  record: string;
  title: string;
  status?: string;
  restricted: boolean;
  /** What choosing it does, read out on the label. */
  action: string;
  at: Anchor;
}

// The projector on the bench is the room's one place that is not a record: it plays the
// transmission (the hologram and the subject file further down the home page).
const TRANSMISSION = {
  id: 'transmission',
  href: '#transmission',
  record: 'TX',
  title: 'The transmission',
  status: 'Recorded',
  restricted: false,
  action: 'Play the transmission',
};

const inFrame = (a?: Anchor): a is Anchor =>
  a !== undefined && a.box[0] > -0.02 && a.box[1] > -0.02 && a.box[2] < 1.02 && a.box[3] < 1.02;

export async function getLabSet() {
  const rest = still('lab-rest-desk');
  if (!data || !rest) return null;
  const [projects, lab, ids] = await Promise.all([getProjects(), getLabEntries(), recordIds()]);
  const records = [
    ...projects.map((p) => ({ key: `projects/${p.id}`, id: p.id, data: p.data })),
    ...lab.map((e) => ({ key: `lab/${e.id}`, id: e.id, data: e.data })),
  ];
  const items: LabItem[] = [];
  for (const [id, at] of Object.entries(data.desk.items)) {
    if (id === TRANSMISSION.id) {
      if (inFrame(at)) items.push({ ...TRANSMISSION, at });
      continue;
    }
    const r = records.find((x) => x.id === id);
    const record = r && ids.get(r.key);
    // Only records that exist (and are published) and are in frame get a place in the room.
    if (!r || !record || !inFrame(at)) continue;
    const d = r.data as { title: string; status?: string; restricted?: boolean };
    items.push({
      id,
      href: `/${r.key}`,
      record,
      title: d.title,
      status: statusLabel(d.status),
      restricted: Boolean(d.restricted),
      action: d.restricted ? 'Open the restricted record' : 'Open the record',
      at,
    });
  }
  // Record order: the case studies (R-01…), then the lab entries (L-01…). Tab and the arrow keys
  // follow it.
  items.sort((a, b) =>
    a.record[0] === b.record[0] ? a.record.localeCompare(b.record) : a.record[0] === 'R' ? -1 : 1,
  );
  return {
    items,
    rest: await art(rest),
    close: data.close ?? [],
  };
}

/** The rendered close-up of a record on its shelf (the push-in's last frame), if there is one. */
export function closeUp(id: string): string | undefined {
  return data?.close?.includes(id) ? `/set/lab/close/${id}.avif` : undefined;
}

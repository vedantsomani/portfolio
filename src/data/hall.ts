// Hardware hall objects (03_PHASE3_MOTION §3). Specs are real part numbers from SITE_SPEC §6.
// The model is public/models/<id>.glb when it exists (saarthi.glb is exported from the same KiCad
// file as the hero); otherwise the hall shows a procedural placeholder mesh.
// SETU is out until its airframe is confirmed (ASSET_INVENTORY item 5).
import hallSaarthi from '../assets/work/hall-saarthi.jpg';

export const hall = [
  {
    id: 'saarthi',
    name: 'Saarthi PCB',
    line: 'The H7-Pro flight controller board.',
    specs: ['STM32H753 + STM32G431', 'BMI088 + 2× ICM-42688-P', 'MS5611 + DPS310'] as (
      string | null
    )[],
    href: '/projects/saarthi' as string | null,
    linkLabel: 'Saarthi case study',
    poster: hallSaarthi,
    posterAlt: 'KiCad 3D render of the Saarthi H7-Pro board at an angle, on a dark background.',
  },
] as const;

export type HallObject = (typeof hall)[number];

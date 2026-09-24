// Hardware hall objects (03_PHASE3_MOTION §3). Specs are real part numbers from SITE_SPEC §6.
// `model` is the GLB name under public/models/; until it exists the hall shows a procedural
// placeholder mesh. `href` null → no case-study link yet.
import hallSaarthi from '../assets/placeholders/hall-saarthi.jpg';
import hallSetu from '../assets/placeholders/hall-setu.jpg';

export const hall = [
  {
    id: 'saarthi',
    name: 'Saarthi PCB',
    line: 'The H7-Pro flight controller board.',
    specs: ['STM32H753', '2× ICM-42688-P', 'DPS310 + BMP390'] as (string | null)[],
    href: '/projects/saarthi' as string | null,
    linkLabel: 'Saarthi case study',
    poster: hallSaarthi,
    posterAlt: 'Placeholder for a render of the Saarthi PCB',
  },
  {
    id: 'setu',
    name: 'SETU frame',
    line: 'The F450-class airframe behind the swarm work.',
    // TODO(vedant): a third verified SETU spec (e.g. AUW, motor/prop, flight time)
    specs: ['F450 frame', 'FC + Linux SBC', null] as (string | null)[],
    // Links to the lab entry once it has a status (hidden in production until then).
    href: '/lab/skynet-setu' as string | null,
    linkLabel: 'SKYNET / SETU lab entry',
    poster: hallSetu,
    posterAlt: 'Placeholder for a render of the SETU airframe',
  },
] as const;

export type HallObject = (typeof hall)[number];

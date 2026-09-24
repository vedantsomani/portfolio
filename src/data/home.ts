// Home page content from SITE_SPEC §6. Phase 2 replaces this with the content collections.
import clientCover from '../assets/placeholders/client-cover.jpg';
import saarthiCover from '../assets/placeholders/saarthi-cover.jpg';
import skynetCover from '../assets/placeholders/skynet-cover.jpg';
import hallSaarthi from '../assets/placeholders/hall-saarthi.jpg';
import hallSetu from '../assets/placeholders/hall-setu.jpg';

export const clientCase = {
  // TODO(vedant): client case #1 (candidate: Bennett University IoT & Robotics Club website redesign, Next.js). Needs scope, role, screens, outcome.
  title: null as string | null,
  outcome: null as string | null,
  href: null as string | null,
  cover: clientCover,
  coverAlt: 'Placeholder for the first client case cover',
};

export const engineering = [
  {
    title: 'Saarthi (H7-Pro)',
    summary: 'Flight-controller firmware on STM32H753.',
    status: 'Prototype' as string | null,
    href: '/projects/saarthi',
    cover: saarthiCover,
    coverAlt: 'Placeholder for the Saarthi board photo',
  },
  {
    title: 'SKYNET / SETU',
    summary:
      'Heterogeneous autonomous swarm on a dual-brain pattern: real-time flight controller plus Linux SBC.',
    // TODO(vedant): SKYNET / SETU status
    status: null as string | null,
    href: '/lab/skynet-setu',
    cover: skynetCover,
    coverAlt: 'Placeholder for a SETU airframe photo',
  },
];

export const hall = [
  {
    name: 'Saarthi PCB',
    line: 'The H7-Pro flight controller board.',
    specs: ['STM32H753', '2× ICM-42688-P', 'DPS310 + BMP390'] as (string | null)[],
    image: hallSaarthi,
    imageAlt: 'Placeholder for the Saarthi PCB model',
  },
  {
    name: 'SETU frame',
    line: 'The F450-class airframe behind the swarm work.',
    // TODO(vedant): a third verified SETU spec
    specs: ['F450 frame', 'FC + Linux SBC', null] as (string | null)[],
    image: hallSetu,
    imageAlt: 'Placeholder for the SETU airframe model',
  },
];

export const lab = [
  {
    title: 'Saarthi fusion benchmark',
    discipline: 'Firmware',
    // TODO(vedant): status, date, one-line result for the fusion benchmark entry
    status: null as string | null,
    date: null as string | null,
    line: null as string | null,
  },
  {
    title: 'SKYNET / SETU',
    discipline: 'Swarm',
    // TODO(vedant): status, date, one-line hypothesis for SKYNET / SETU
    status: null as string | null,
    date: null as string | null,
    line: null as string | null,
  },
  {
    // TODO(vedant): third lab entry
    title: null as string | null,
    discipline: null as string | null,
    status: null as string | null,
    date: null as string | null,
    line: null as string | null,
  },
];

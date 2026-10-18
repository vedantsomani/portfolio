// Restricted records (AGENTS.md hard rule 3): PRAHARI, VAJRA, SKYNET as dossiers, architecture and
// results only. Every line restates the entry's own page (frontmatter or body); nothing else is
// published, and no repository is linked.
import { getEntry } from 'astro:content';
import { formatDate, statusLabel } from './content';
import type { Discipline } from './disciplines';

export interface Dossier {
  id: string;
  title: string;
  href: string;
  /** Where the full record lives. */
  where: 'Case study' | 'Lab entry';
  status: string;
  when: string;
  disciplines: Discipline[];
  line: string;
  architecture: { label: string; value: string }[];
  results: string[];
  withheld: string;
}

const need = <T>(v: T | undefined, what: string): T => {
  if (v === undefined) throw new Error(`Dossier needs ${what}`);
  return v;
};

export async function getDossiers(): Promise<Dossier[]> {
  const vajra = need(await getEntry('projects', 'vajra'), 'vajra');
  const skynet = need(await getEntry('lab', 'skynet'), 'skynet');
  const prahari = need(await getEntry('lab', 'prahari'), 'prahari');

  return [
    {
      id: 'vajra',
      title: vajra.data.title,
      href: '/projects/vajra',
      where: 'Case study',
      status: need(statusLabel(vajra.data.status), 'VAJRA status'),
      when: vajra.data.year ?? '',
      disciplines: vajra.data.disciplines,
      line: vajra.data.summary,
      architecture: (vajra.data.architecture?.columns ?? []).map((c) => ({
        label: c.title,
        value: c.nodes.join(', '),
      })),
      results: (vajra.data.results ?? []).map((r) => `${r.label}: ${r.value}`),
      withheld: 'protocol internals, key handling, and the repository',
    },
    {
      id: 'skynet',
      title: skynet.data.title,
      href: '/lab/skynet',
      where: 'Lab entry',
      status: need(statusLabel(skynet.data.status), 'SKYNET status'),
      when: formatDate(skynet.data.date) ?? '',
      disciplines: ['autonomy'],
      line: 'A dual-brain aircraft stack: a flight controller for real-time control and a companion computer for the mission.',
      // src/content/lab/skynet.mdx, "What it is".
      architecture: [
        { label: 'Flight control', value: 'Pixhawk flight controller' },
        {
          label: 'Companion',
          value: 'Raspberry Pi: the mission, safety gates, and a live telemetry dashboard',
        },
        { label: 'Sensors', value: 'GPS, optical flow, barometer' },
      ],
      results: skynet.data.result ? [skynet.data.result] : [],
      withheld: 'control logic and code',
    },
    {
      id: 'prahari',
      title: prahari.data.title,
      href: '/lab/prahari',
      where: 'Lab entry',
      status: need(statusLabel(prahari.data.status), 'PRAHARI status'),
      when: 'Design stage',
      disciplines: ['autonomy'],
      line: prahari.data.hypothesis ?? '',
      // src/content/lab/prahari.mdx, "Architecture".
      architecture: [
        { label: 'Sensing', value: 'PMW3901 optical flow, VL53L0X rangefinder' },
        { label: 'Policy', value: 'PPO / SAC over a belief state, trained in Isaac Lab' },
        { label: 'Shield', value: 'LTL → Büchi shield synthesis, Mealy mission controller' },
        { label: 'Vehicle', value: 'Saarthi flight controller' },
      ],
      results: ['None yet: a design with no public artifacts.'],
      withheld: 'control laws and code',
    },
  ];
}

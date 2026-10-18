// The discipline filter on /projects (SITE_SPEC §2). A grouping, not a claim: a project is in a
// discipline only when its own page or archive entry shows work of that kind.
export const DISCIPLINES = ['hardware', 'autonomy', 'ai', 'security', 'software'] as const;

export type Discipline = (typeof DISCIPLINES)[number];

export const DISCIPLINE_LABEL: Record<Discipline, string> = {
  hardware: 'Hardware',
  autonomy: 'Autonomy',
  ai: 'AI',
  security: 'Security',
  software: 'Software',
};

// Site-wide facts. Anything unknown is null and renders as a visible TODO, never a guess.

export const site = {
  name: 'Vedant Somani',
  location: 'Greater Noida',
  // TODO(vedant): contact email (also used as the Resend destination and the mailto fallback)
  email: null as string | null,
  // TODO(vedant): GitHub profile URL
  github: null as string | null,
  // TODO(vedant): LinkedIn profile URL
  linkedin: null as string | null,
  // TODO(vedant): confirm availability line
  availability: 'Taking select freelance projects',
} as const;

export const nav = [
  { href: '/projects', label: 'Projects' },
  { href: '/lab', label: 'Lab' },
  { href: '/services', label: 'Services' },
  { href: '/about', label: 'About' },
] as const;

export const hero = {
  title: 'Websites and apps, engineered.',
  supporting:
    'By the same person who writes flight-controller firmware for STM32H7. Designed, built, and deployed end to end — from Greater Noida, for clients anywhere.',
  // TODO(vedant): hero photo alt text, describing the real Saarthi photo once it exists
  photoAlt: 'Placeholder for a top-down photo of the Saarthi H7-Pro flight controller',
} as const;

export const process = [
  // TODO(vedant): confirm the one-line description for each step
  { name: 'Scope', line: 'Pin down goals, pages, and budget in writing.' },
  { name: 'Prototype', line: 'A clickable draft of the key screens before the full build.' },
  { name: 'Build', line: 'Development, content, and integrations.' },
  { name: 'Test', line: 'Real devices, speed, and accessibility checks.' },
  { name: 'Launch', line: 'Deploy, hand over, and switch on analytics.' },
] as const;

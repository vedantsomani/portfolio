// Site-wide facts. Anything unknown is null and renders as a visible TODO, never a guess.

export const site = {
  name: 'Vedant Somani',
  location: 'Greater Noida',
  // Also the Resend recipient (unless CONTACT_TO_EMAIL overrides it) and the mailto fallback.
  email: 'hello@vedantsomani.tech' as string | null,
  github: 'https://github.com/vedantsomani/' as string | null,
  linkedin: 'https://www.linkedin.com/in/vedantsomani12/' as string | null,
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
  { name: 'Scope', line: 'Pin down goals, pages, and budget in writing.' },
  { name: 'Prototype', line: 'A clickable draft of the key screens before the full build.' },
  { name: 'Build', line: 'Development, content, and integrations.' },
  { name: 'Test', line: 'Real devices, speed, and accessibility checks.' },
  { name: 'Launch', line: 'Deploy, hand over, and switch on analytics.' },
] as const;

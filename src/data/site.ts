// Site-wide facts. Anything unknown is null and renders as a visible TODO in dev, never a guess.

export const site = {
  name: 'Vedant Somani',
  location: 'Greater Noida',
  // Also the Resend recipient (unless CONTACT_TO_EMAIL overrides it) and the mailto fallback.
  email: 'hello@vedantsomani.tech' as string | null,
  github: 'https://github.com/vedantsomani/' as string | null,
  linkedin: 'https://www.linkedin.com/in/vedantsomani12/' as string | null,
} as const;

export const nav = [
  { href: '/projects', label: 'Projects' },
  { href: '/lab', label: 'Lab' },
  { href: '/about', label: 'About' },
] as const;

export const hero = {
  title: 'Flight hardware, secure comms, and space data — built from the silicon up.',
  supporting:
    "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them.",
  photoAlt:
    'Top-down KiCad render of the Saarthi H7-Pro flight controller board: the STM32H753, three IMUs in the centre, connectors along the edges, and four corner mounting holes.',
  xrayAlt: 'The same board as a copper plot from KiCad: front copper, back copper, and silkscreen.',
} as const;

// Contact form reasons. The label is what the email subject and the <select> show.
export const reasons = [
  { value: 'internship', label: 'Internship' },
  { value: 'research', label: 'Research collaboration' },
  { value: 'hardware', label: 'Hardware project' },
  { value: 'other', label: 'Other' },
] as const;

export const about = {
  // Roles with what each one involved, from cv (4) p1 (May 2026) and cv-2 p1 (Aug 2026).
  roles: [
    {
      title: 'Head of Research',
      org: 'Technotix BU, the IoT & Robotics Club at Bennett University',
      when: 'since Feb 2026',
      detail:
        'Coordinated drone, ESP32, and sensor-integration work in a five-member robotics subgroup; ran two workshops on UAV basics and ESP32 sensor interfacing for 250+ attendees; mentored 50+ juniors on hardware debugging and embedded protocols.',
    },
    {
      title: 'Head of Research',
      org: 'BC3, the Bennett Cloud Computing Club',
      when: 'since Oct 2025',
      detail: 'Organised workshops on edge computing and deployment pipelines for club members.',
    },
    {
      title: 'Member',
      org: 'BURS, the Bennett Undergraduate Research Society',
      when: '2024–25',
      detail: 'First-year member of the undergraduate research community.',
    },
  ],
  // cv-2 p2.
  awards: ['Altium Global Scholarship Program 2026: selected.'],
  education: 'B.Tech CSE, Bennett University, 2024–28',
  // Vedant's photo (sent 2026-09-26), re-encoded without metadata.
  photoAlt:
    "Vedant's desk at night: two laptops, one showing a CAD model, a 3D printer, printed wing panels, and a drone frame at the edge.",
} as const;

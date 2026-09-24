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
  title: 'Flight controllers, autonomy, and secure comms — built from the silicon up.',
  supporting:
    "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them.",
  // TODO(vedant): hero photo alt text, describing the real Saarthi photo once it exists
  photoAlt: 'Placeholder for a top-down photo of the Saarthi H7-Pro flight controller',
  xrayAlt: 'Placeholder for the Saarthi copper layout, aligned to the photo',
} as const;

// Contact form reasons. The label is what the email subject and the <select> show.
export const reasons = [
  { value: 'internship', label: 'Internship' },
  { value: 'research', label: 'Research collaboration' },
  { value: 'hardware', label: 'Hardware project' },
  { value: 'other', label: 'Other' },
] as const;

export const about = {
  roles: [
    { title: 'Head of Research', org: 'Technotix BU' },
    { title: 'Head of Research', org: 'BC3' },
    { title: 'Core member', org: 'BURS' },
  ],
  education: 'B.Tech CSE, Bennett University, 2024–28',
  // TODO(vedant): portrait or workspace photo alt text once the photo exists
  photoAlt: 'Placeholder for a photo of Vedant at the bench',
} as const;

// Site-wide facts. Anything unknown is null and renders as a visible TODO in dev, never a guess.

export const site = {
  name: 'Vedant Somani',
  location: 'Greater Noida',
  // Also the Resend recipient (unless CONTACT_TO_EMAIL overrides it) and the mailto fallback.
  email: 'hello@vedantsomani.tech' as string | null,
  github: 'https://github.com/vedantsomani/' as string | null,
  linkedin: 'https://www.linkedin.com/in/vedantsomani12/' as string | null,
} as const;

// Three places: the archive (the home page: the film, then the lab, with the files and the
// transmission opening over it), the recruiter briefing, and contact.
export const nav = [
  { href: '/#files', label: 'Files' },
  { href: '/#transmission', label: 'Transmission' },
  { href: '/briefing', label: 'Briefing' },
] as const;

// The film (src/components/Film.astro): fiction told over the renders, so nothing in it is a claim
// about the work. Few words: the radio between the one crew member on the ground and command in
// orbit, timed in seconds into each shot (the shot ids are blender/film.py's). A line with a voice
// file plays it, through a radio filter, when sound is on; the subtitle shows either way.
export const film = {
  signal: 'Signal · 28.47° N, 77.50° E · Greater Noida',
  lines: [
    { shot: 'orbit', at: 3.0, who: 'Command', text: 'There. Still transmitting.' },
    { shot: 'descent', at: 0.8, who: 'Command', text: 'Ground team, you’re clear.' },
    { shot: 'street', at: 3.9, who: 'Ground', text: 'Hold.' },
    { shot: 'street', at: 4.8, who: 'Command', text: 'Don’t move. It’s scanning.' },
    { shot: 'street', at: 8.0, who: 'Ground', text: '…It’s gone dark.' },
    { shot: 'approach', at: 5.2, who: 'Ground', text: 'It’s watching us again.' },
    { shot: 'lab-enter', at: 2.4, who: 'Ground', text: 'No power. Just the transmitter.' },
    { shot: 'lab-power', at: 3.2, who: 'Command', text: 'What is this place?' },
    { shot: 'lab-bench', at: 5.7, who: 'Command', text: 'Who is that?' },
  ] as { shot: string; at: number; who: string; text: string; voice?: string }[],
  // The card the film ends on, before it fades into the lab.
  title: { name: 'The Archive', by: 'Vedant Somani' },
  credit:
    'Rendered in Blender. The Earth is NASA’s Blue Marble; the plants, props and surfaces are photo-scanned (Poly Haven, CC0). The city, the machines, the crew and the craft are set dressing.',
};

export const hero = {
  title: 'Flight hardware, secure comms, and space data — built from the silicon up.',
  supporting:
    "I'm Vedant Somani, a CSE student at Bennett University building embedded systems, drones, and the software around them.",
  // Alt for src/assets/portrait/vedant.jpg (sent 2026-10-17): Vedant's own photo; the background and
  // lighting were changed with an AI image editor, the face was not (SITE_SPEC §3). Cropped above the
  // editor's watermark and re-encoded without metadata.
  photoAlt:
    'Vedant Somani, smiling, in a blue shirt, standing in a dark, empty concrete hall. Background and lighting AI-edited.',
  // The lens layer is decorative: the same photo seen as machine vision.
  machineAlt: 'The same photo in red machine vision: edges traced, scan lines over it.',
  // Where the eye glows in machine vision: [x, y] as fractions of the portrait from its top-left.
  // Measured on the 2624 × 1460 file: the eye on the viewer's right, pupil at 1950, 537.
  eye: [0.743, 0.368] as [number, number] | null,
  // The crop's focal point in the portrait, [x, y] as fractions from its top-left: the face. The CSS
  // crop and the lens shader both use it, so the machine layer lands on the photo.
  focus: [0.71, 0.4] as [number, number],
} as const;

// Cold open (SITE_SPEC §4.0): the title gate and the credit cards. Every line restates the hero.
export const archive = {
  title: 'The Archive',
  tagline: 'From the silicon up.',
} as const;

export const credits = [
  { kicker: 'Vedant Somani', line: 'presents' },
  { kicker: '', line: 'Flight hardware' },
  { kicker: '', line: 'Secure comms' },
  { kicker: '', line: 'Space data' },
  { kicker: 'built from', line: 'the silicon up' },
] as const;

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

type Ref = { label: string; href: string };
const saarthi: Ref = { label: 'Saarthi', href: '/projects/saarthi' };
const tessera: Ref = { label: 'TESSERA', href: '/projects/tessera' };
const anav: Ref = { label: 'ANAV', href: '/projects/anav' };
const vajra: Ref = { label: 'VAJRA', href: '/projects/vajra' };
const smriti: Ref = { label: 'SMRITI', href: '/projects/smriti' };
const dhwani: Ref = { label: 'Dhwani-Kavach', href: '/projects/dhwani-kavach' };
const pitsense: Ref = { label: 'PitSense', href: '/projects/pitsense' };
const clubSite: Ref = { label: 'Club website', href: '/projects/iot-club-website' };
const skynet: Ref = { label: 'SKYNET', href: '/lab/skynet' };
const irocu: Ref = { label: 'IRoC-U quadrotor', href: '/#irocu-2026' };
const drones: Ref = { label: 'Club drone builds', href: '/#club-drones' };
const smartcan: Ref = { label: 'SmartCan', href: '/#smartcan' };
const lineBot: Ref = { label: 'Line-following robot', href: '/#line-follower' };
const codesaas: Ref = { label: 'CodeSaaS', href: '/#codesaas' };
const krishi: Ref = { label: 'Krishi Darpan', href: '/#krishi-darpan' };
const netAnalyzer: Ref = { label: 'Network analyzer', href: '/#network-analyzer' };
const focusflow: Ref = { label: 'FocusFlow', href: '/#focusflow' };

// Timeline on /about (SITE_SPEC §5): dated facts only, newest first, each restating its project
// page or archive entry. A year alone where the month isn't recorded.
export const timeline: { when: string; title: string; line: string; href: string }[] = [
  {
    when: 'Sep 2026',
    title: 'Saarthi H7-Pro',
    line: 'Board file at 0 ERC errors: schematic complete, routing in progress.',
    href: saarthi.href,
  },
  {
    when: 'Jul 2026',
    title: 'SKYNET',
    line: 'A companion-computer mission, and the autopilot landing on its own when the companion is killed, in ArduPilot simulation.',
    href: skynet.href,
  },
  {
    when: 'Jan–Apr 2026',
    title: 'IRoC-U 2026 indoor quadrotor',
    line: 'GPS-denied flight tests in a 5 m × 5 m arena, with teammates, for the ISRO Robotics Competition.',
    href: irocu.href,
  },
  {
    when: '2026',
    title: 'TESSERA',
    line: "Team leader on ISRO's Bharatiya Antariksh Hackathon: thermal infrared to colour, with a risk map.",
    href: tessera.href,
  },
  {
    when: '2026',
    title: 'Dhwani-Kavach',
    line: 'Live dual-microphone speech enhancement for Smart India Hackathon 2026, bench-tested.',
    href: dhwani.href,
  },
  {
    when: '2026',
    title: 'VAJRA',
    line: 'A point-to-point post-quantum link, frozen at v1.0 in Rust.',
    href: vajra.href,
  },
  {
    when: 'Aug 2024 – Apr 2025',
    title: 'ANAV',
    line: 'An autonomous landing UAV for an ISRO competition, built and tested in a tent hall and outdoors.',
    href: anav.href,
  },
  {
    when: 'Apr–Jun 2023',
    title: 'Line-following robot',
    line: 'Arduino, PID line following, and ultrasonic obstacle avoidance.',
    href: lineBot.href,
  },
];

// Toolchain on /about (SITE_SPEC §5): plain text, grouped by domain, and every tool links to where it
// was used (a project's stack or text says so). No logos, no counts.
export const toolchain: { domain: string; tools: { name: string; used: Ref[] }[] }[] = [
  {
    domain: 'Embedded and PCB',
    tools: [
      { name: 'KiCad', used: [saarthi] },
      { name: 'STM32H7, STM32G4', used: [saarthi] },
      { name: 'C11, CMake', used: [saarthi] },
      { name: 'Raspberry Pi', used: [skynet, smartcan] },
      { name: 'Arduino', used: [lineBot] },
    ],
  },
  {
    domain: 'Flight and autonomy',
    tools: [
      { name: 'ArduPilot SITL', used: [skynet] },
      { name: 'Pixhawk', used: [skynet, drones] },
      { name: 'PX4, Jetson Nano', used: [irocu] },
      { name: 'MAVLink, QGroundControl', used: [anav] },
      { name: 'Mission Planner', used: [drones] },
    ],
  },
  {
    domain: 'ML and vision',
    tools: [
      { name: 'PyTorch', used: [tessera] },
      { name: 'ONNX Runtime', used: [dhwani] },
      { name: 'OpenCV', used: [smartcan] },
      { name: 'XGBoost', used: [krishi, pitsense] },
      { name: 'TensorFlow Lite', used: [krishi] },
      { name: 'LangGraph, AWS Bedrock', used: [codesaas] },
    ],
  },
  {
    domain: 'Security',
    tools: [
      { name: 'Rust', used: [vajra] },
      { name: 'ML-KEM-768, ML-DSA-65', used: [vajra] },
      { name: 'ProVerif', used: [vajra] },
      { name: 'scapy', used: [netAnalyzer] },
    ],
  },
  {
    domain: 'Software',
    tools: [
      { name: 'Python', used: [tessera, dhwani, pitsense] },
      { name: 'Next.js', used: [clubSite, codesaas] },
      { name: 'TypeScript', used: [focusflow] },
      { name: 'React Native, Expo', used: [smriti] },
      { name: 'Express, SQLite, Socket.IO', used: [smriti] },
      { name: 'Streamlit', used: [pitsense] },
    ],
  },
];

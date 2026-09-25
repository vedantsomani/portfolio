// More projects: work without a full case study. Every line comes from one of Vedant's own sources,
// named in `source` (not rendered): the old portfolio's project list (Downloads/cv/content.py), the
// résumés (cv-2, Aug 2026; cv (4), May 2026), LinkedIn project entries (screenshots Vedant sent,
// 2026-09-25), the repo READMEs, or the live site itself. `evidence`
// says which kind, so a résumé claim never reads like a verified measurement (AGENTS.md rule 8).
// Links are only ones checked to load (2026-09-25).

import type { ImageMetadata } from 'astro';
import clubHex from '../assets/work/club-hex.jpg';
import clubF450 from '../assets/work/club-f450.jpg';

export type Evidence =
  'Live site' | 'Public repo' | 'Résumé' | 'LinkedIn' | 'Photos' | 'Local only';

export interface ArchiveEntry {
  title: string;
  year: string;
  line: string;
  stack: string;
  evidence: Evidence;
  links: { label: string; href: string }[];
  /** Real photos, shown small beside the entry. */
  photos?: { src: ImageMetadata; alt: string }[];
  /** Where each claim comes from. Not rendered. */
  source: string;
  /** Dev-only TODO for anything that still needs Vedant. */
  todo?: string;
}

const gh = (repo: string) => ({ label: 'Source', href: `https://github.com/vedantsomani/${repo}` });

export const archive: ArchiveEntry[] = [
  {
    title: 'CodeSaaS',
    year: '2026',
    line: 'Seven agents build a full-stack app from one prompt. A supervisor agent reads the prompt and assigns frontend, backend, database, DevOps, and integration agents; a QA agent runs the whole project in a cloud sandbox and sends each failure back to the agent that caused it, not to the start. The build streams live into a browser IDE. Krish Singh built the shared memory and inter-agent coordination layer.',
    stack: 'LangGraph, AWS Bedrock, E2B, Next.js, WebSockets',
    evidence: 'Live site',
    links: [{ label: 'Live', href: 'https://aws-six-omega.vercel.app' }, gh('AWS')],
    source:
      'LinkedIn post (architecture, credit to Krish Singh for shared memory and coordination); cv-2 p1; cv (4) p1 ("CodeSaaS"); live page title "CodeSaaS".',
    todo: 'CodeSaaS screenshots from the LinkedIn post, as files',
  },
  {
    title: 'IRoC-U 2026 indoor quadrotor',
    year: '2026',
    line: 'A GPS-denied autonomous indoor quadrotor for the ISRO Robotics Competition. With teammates I wrote flight-control and sensor-integration code, built the frame, and ran flight tests in a 5 m × 5 m indoor arena.',
    stack: 'PX4, Jetson Nano, stereo depth camera, optical flow',
    evidence: 'Résumé',
    // The repo (irocu-2026) is not linked: its README is not presentable.
    links: [],
    source: 'cv (4) p1 ("IRoC-U 2026", Jan–Apr 2026); cv-2 p2 ("ISRO Robotics Competition 2026").',
    todo: 'link irocu-2026 once its README is replaced; your exact part',
  },
  {
    title: 'Krishi Darpan',
    year: '2025–',
    line: 'A multilingual Android farming assistant, built with Krish Singh, Devender Singh Shekhawat, Vansh Mittal, Madhvi Jain, and Shruti. It gives field-level crop advice from Sentinel-1/2 imagery and ERA-5 weather through Google Earth Engine; an XGBoost model ranks crops from soil health cards (15+ crops, 78% accuracy on real field data); a quantized MobileNet under 6 MB spots pests and disease offline (80% on an open benchmark). Presented at Bennett University Project Showcase 2.0.',
    stack: 'React Native, Google Earth Engine, Python, XGBoost, TensorFlow Lite',
    evidence: 'LinkedIn',
    links: [],
    source:
      'LinkedIn project (Oct 2025 – Present) and Project Showcase 2.0 post (team names); cv (4) p1 (accuracies); cv-2 p2.',
    todo: 'Krishi Darpan site URL and source link (the showcase post shows both); your part in the team',
  },
  {
    title: 'GTR 2026 event site',
    year: '2026',
    line: 'The website for Grand Tech Racing 2026: a Vite and React front end with a chatbot API.',
    stack: 'Vite, React',
    evidence: 'Live site',
    links: [{ label: 'Live', href: 'https://gtr-2026.vercel.app' }, gh('GTR-2026')],
    source: 'Old site (content.py, "gtr-2026"); live page title "GTR 2026 — Grand Tech Racing".',
    todo: 'your role on GTR 2026',
  },
  {
    title: 'Line-following robot',
    year: '2023',
    line: 'An Arduino robot with PID line following, four IR sensors, ultrasonic obstacle avoidance, and Bluetooth control.',
    stack: 'Arduino, L298N, HC-05',
    evidence: 'Public repo',
    links: [gh('Line-follwing-Bot')],
    source: 'Line-follwing-Bot README; LinkedIn (Apr 2023 – Jun 2023).',
  },
  {
    title: 'Club drone builds',
    year: '—',
    line: 'My own builds in the IoT & Robotics Club lab: an S550 hexacopter and an F450 quadcopter, both on Pixhawk with a GPS mast, set up in Mission Planner.',
    stack: 'Pixhawk, ArduPilot, Mission Planner, GPS',
    evidence: 'Photos',
    links: [],
    photos: [
      {
        src: clubHex,
        alt: 'An S550 hexacopter with a Pixhawk and GPS mast on a lab table, beside a laptop running Mission Planner showing the vehicle disarmed.',
      },
      {
        src: clubF450,
        alt: 'An F450 quadcopter with a Pixhawk and GPS mast on a lab table.',
      },
    ],
    source: 'Photos Vedant sent (2026-09-26), described by him as his own builds in the club.',
    todo: 'build dates, and whether they flew',
  },
  {
    title: 'SmartCan',
    year: '2025',
    line: 'A prototype smart bin: a Raspberry Pi camera and an image model classify waste in real time, then drive the lid and the category-based disposal. I built the training set and deployed the model on the Pi.',
    stack: 'Raspberry Pi, OpenCV, Python',
    evidence: 'LinkedIn',
    links: [{ label: 'Web app source', href: 'https://github.com/vedantsomani/Smart-bin' }],
    source:
      'LinkedIn ("SmartCan – AI-Powered Waste Classification Bin"); Smart-bin repo (homepage "Smart Bin 1.0").',
    todo: "confirm the Smart-bin repo is SmartCan's web app",
  },
  {
    title: 'Cymbot',
    year: '2024',
    line: 'A mental-health support chatbot built as a team: assessment quizzes with personalised recommendations, and Python NLP for the conversation.',
    stack: 'Python, NLP, HTML, JavaScript',
    evidence: 'LinkedIn',
    links: [gh('cymbot')],
    source: 'LinkedIn ("Cymbot – Mental Health Chatbot", three contributors listed); cymbot tree.',
  },
  {
    title: 'Network analyzer',
    year: '2025',
    line: 'Packet capture in Python with scapy, anomaly flags from an Isolation Forest, and a tkinter window.',
    stack: 'Python, scapy, scikit-learn',
    evidence: 'Public repo',
    links: [gh('network_analyzer')],
    source: 'Old site ("network-analyzer", from the source file).',
  },
  {
    title: 'EduCon',
    year: '2025',
    line: 'An encrypted Java chat client with private and AI-assisted chat.',
    stack: 'Java, Swing',
    evidence: 'Public repo',
    links: [gh('chat-app')],
    source: 'chat-app README; old site ("educon").',
  },
  {
    title: 'FocusFlow',
    year: '2026',
    line: 'A concept for an ADHD- and dyslexia-first study app: lecture capture, transcription, and recovering what you missed.',
    stack: 'Next.js, TypeScript',
    evidence: 'Public repo',
    links: [gh('FOCUSFLOW')],
    source: 'FOCUSFLOW README; old site ("concept dump, not a shipped product").',
  },
  {
    title: 'Campusgram',
    year: '2025',
    line: 'A campus social app: a Vite and React front end with a JSON backend.',
    stack: 'Vite, React, Socket.IO',
    evidence: 'Public repo',
    links: [gh('java-social-media')],
    source: 'Old site ("campusgram", from the source tree).',
  },
];

// Small experiments: one line each.
export const experiments: ArchiveEntry[] = [
  {
    title: 'Agri',
    year: '2026',
    line: 'An Expo farming app with fields, tasks, weather, and market prices.',
    stack: 'Expo, React Native',
    evidence: 'Public repo',
    links: [gh('agri1now')],
    source: 'agri1now README.',
  },
  {
    title: 'Disaster-One',
    year: '2025',
    line: 'A small Flask app.',
    stack: 'Flask',
    evidence: 'Public repo',
    links: [gh('Disaster-One')],
    source: 'Old site ("disaster-one").',
    todo: 'one line on what Disaster-One does',
  },
  {
    title: 'YouTube ad blocker',
    year: '2025',
    line: 'A userscript that removes and skips YouTube ads with a MutationObserver.',
    stack: 'JavaScript',
    evidence: 'Public repo',
    links: [gh('YoutubeAdBlocker')],
    source: 'YoutubeAdBlocker README.',
  },
  {
    title: 'Autotyper',
    year: '2026',
    line: 'A keyboard helper for accessibility, demos, and testing.',
    stack: 'Python',
    evidence: 'Local only',
    links: [],
    source: 'Documents/Projects/Automation/autotypper; Downloads/Untitled-1.py L1.',
  },
];

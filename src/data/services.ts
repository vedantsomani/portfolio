// Packages and terms from SITE_SPEC §5 Services. Prices are the spec's, verbatim.

export interface Package {
  id: string;
  name: string;
  price: string;
  from: string;
  scope: string;
  target: string;
}

export const packages: Package[] = [
  {
    id: 'launch',
    name: 'Launch',
    price: 'from ₹15,000',
    from: 'from ₹15,000',
    scope: '1–3 pages, custom responsive UI, enquiry/WhatsApp, analytics, basic SEO, deploy',
    target: '~1 week',
  },
  {
    id: 'business',
    name: 'Business',
    price: '₹30,000–45,000',
    from: 'from ₹30,000',
    scope: '5–7 pages, CMS/Git content, forms, maps/booking hooks, technical SEO',
    target: '2–3 weeks',
  },
  {
    id: 'web-app',
    name: 'Web app / MVP',
    price: '₹60,000–1,20,000',
    from: 'from ₹60,000',
    scope: 'Auth, database, dashboard/admin, APIs, deploy',
    target: '3–6 weeks',
  },
  {
    id: 'care',
    name: 'Care',
    price: '₹3,000–8,000/month',
    from: 'from ₹3,000/month',
    scope: 'Updates, small changes, monitoring',
    target: 'Ongoing',
  },
];

export const connectedPrototypes = {
  name: 'Connected prototypes',
  scope: 'Software + embedded',
  price: 'Scoped individually',
};

// Stays off until a shipped mobile case exists (SITE_SPEC §5).
export const SHOW_MOBILE_MVP = false;

export const payment = [
  { label: 'Small sites', split: '50 / 50' },
  { label: 'Larger projects', split: '40 / 30 / 30' },
];

export const exclusions = ['Domains', 'Paid APIs', 'Third-party subscriptions', 'App-store fees'];

export const projectTypes = [
  { value: 'launch', label: 'Launch site (1–3 pages)' },
  { value: 'business', label: 'Business site (5–7 pages)' },
  { value: 'web-app', label: 'Web app / MVP' },
  { value: 'care', label: 'Care plan' },
  { value: 'prototype', label: 'Connected prototype' },
  { value: 'other', label: 'Something else' },
] as const;

export const budgets = [
  { value: 'lt-20k', label: '<₹20k' },
  { value: '20-50k', label: '₹20–50k' },
  { value: '50k-1l', label: '₹50k–1L' },
  { value: '1l-plus', label: '₹1L+' },
  { value: 'not-sure', label: 'Not sure' },
] as const;

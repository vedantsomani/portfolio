import { getCollection, type CollectionEntry } from 'astro:content';
import { SHOW_TODOS } from './todo';

export type Project = CollectionEntry<'projects'>;
export type LabEntry = CollectionEntry<'lab'>;

// Production ships engineering cases only (FINAL_GOAL §1: no client-case template in production).
export async function getProjects(): Promise<Project[]> {
  const all = await getCollection('projects', (p) => SHOW_TODOS || p.data.kind === 'engineering');
  return all.sort((a, b) => a.data.order - b.data.order);
}

// A lab entry without a status is hidden in production.
export async function getLabEntries(): Promise<LabEntry[]> {
  const all = await getCollection('lab', (e) => SHOW_TODOS || Boolean(e.data.status));
  return all.sort((a, b) => a.data.order - b.data.order);
}

const STATUS: Record<string, string> = {
  shipped: 'Shipped',
  prototype: 'Prototype',
  research: 'Research',
  concept: 'Concept',
  validated: 'Validated',
  archived: 'Archived',
};
export const statusLabel = (s?: string) => (s ? STATUS[s] : undefined);

export const formatDate = (d?: Date) =>
  d?.toLocaleDateString('en-IN', { year: 'numeric', month: 'short' });

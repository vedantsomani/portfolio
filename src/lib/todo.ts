// TODO markers are a dev-only aid. In production nothing renders in their place, and callers
// use this flag to drop the element that would otherwise be left empty.
export const SHOW_TODOS = import.meta.env.DEV;

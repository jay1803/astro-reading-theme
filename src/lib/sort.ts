// Newest first; ties on `date` are broken by `id` so pagination is stable across builds.
export function byDateDesc(
  a: { id: string; data: { date: Date } },
  b: { id: string; data: { date: Date } }
): number {
  return b.data.date.valueOf() - a.data.date.valueOf() || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
}

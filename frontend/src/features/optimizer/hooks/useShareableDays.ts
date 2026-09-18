import { useCallback, useState } from 'react';

const MAX_DAYS = 60;

/**
 * The number of days, kept in the URL.
 *
 * A plan is a pure function of its inputs, so the query string *is* the saved
 * plan: `?days=18` reproduces the same year on any device, forever, with no
 * account and nothing stored. Bookmark it, send it to a colleague, reopen it
 * next January.
 */
export function useShareableDays(): [number | null, (days: number) => void] {
  const [days, setDays] = useState<number | null>(readDays);

  const update = useCallback((next: number) => {
    setDays(next);
    const url = new URL(window.location.href);
    url.searchParams.set('days', String(next));
    // replace, not push: re-planning is refining one answer, not navigating,
    // so the back button should still leave the app rather than walk through
    // every number the user tried.
    window.history.replaceState(null, '', url);
  }, []);

  return [days, update];
}

function readDays(): number | null {
  const raw = new URLSearchParams(window.location.search).get('days');
  if (raw === null || raw.trim() === '') return null;

  const value = Number(raw);
  return Number.isInteger(value) && value >= 0 && value <= MAX_DAYS ? value : null;
}

import { useQuery } from '@tanstack/react-query';

import { calendarKeys, fetchYearOverview, type YearOverview } from '../api/calendarApi';

/** Every holiday in a year, so the calendar can show the ones a plan misses too. */
export function useYearOverview(year: number | undefined) {
  return useQuery<YearOverview>({
    queryKey: calendarKeys.year(year ?? -1),
    queryFn: () => fetchYearOverview(year ?? 0),
    enabled: year !== undefined,
  });
}

/**
 * Calendar endpoints, typed entirely from the generated OpenAPI schema.
 *
 * Nothing here declares a shape by hand. If the backend renames a field,
 * `npm run api:types` regenerates schema.d.ts and this file stops compiling --
 * which is the entire point.
 */

import { request } from '@/shared/api/client';
import type { components, operations } from '@/shared/api/schema';

export type YearOverview =
  operations['getYearOverview']['responses']['200']['content']['application/json'];
export type SupportedYears =
  operations['listSupportedYears']['responses']['200']['content']['application/json'];
export type Holiday = components['schemas']['Holiday'];
export type YearStats = components['schemas']['YearStats'];

export const calendarKeys = {
  all: ['calendar'] as const,
  years: () => [...calendarKeys.all, 'years'] as const,
  year: (year: number) => [...calendarKeys.all, 'year', year] as const,
};

export function fetchSupportedYears(): Promise<SupportedYears> {
  return request<SupportedYears>('/calendars/years/');
}

export function fetchYearOverview(year: number): Promise<YearOverview> {
  return request<YearOverview>(`/calendars/years/${year}/`);
}

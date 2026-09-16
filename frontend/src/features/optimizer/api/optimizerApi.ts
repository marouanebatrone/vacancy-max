/**
 * The plan endpoint: the product's entire surface.
 *
 * The request carries one field the user actually chose -- `days`. Year and
 * strategy exist for tooling and are deliberately absent from the UI (ADR 0002).
 * Every type here comes from the generated schema; none is written by hand.
 */

import { request } from '@/shared/api/client';
import type { components, operations } from '@/shared/api/schema';

export type Plan = operations['createPlan']['responses']['200']['content']['application/json'];
export type PlanRequest = NonNullable<
  operations['createPlan']['requestBody']
>['content']['application/json'];
export type Break = components['schemas']['Break'];
export type PlanSummary = components['schemas']['PlanSummary'];
export type HolidayRef = components['schemas']['HolidayRef'];

export const optimizerKeys = {
  all: ['optimizer'] as const,
  plan: (days: number) => [...optimizerKeys.all, 'plan', days] as const,
};

/** Ask for a plan. One number in, a year of holidays out. */
export function createPlan(body: PlanRequest): Promise<Plan> {
  return request<Plan>('/optimizer/plan/', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

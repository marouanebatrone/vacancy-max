import { useQuery } from '@tanstack/react-query';

import { createPlan, optimizerKeys, type Plan } from '../api/optimizerApi';

/**
 * Fetch a plan for `days` of leave. Idle until the user has actually asked,
 * so the page does not guess a number on their behalf.
 */
export function usePlan(days: number | null) {
  return useQuery<Plan>({
    queryKey: optimizerKeys.plan(days ?? -1),
    queryFn: () => createPlan({ days: days ?? 0 }),
    enabled: days !== null,
  });
}

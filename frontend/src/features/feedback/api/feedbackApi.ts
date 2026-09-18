/**
 * Sending feedback. Types come from the generated schema, as everywhere else.
 */

import { request } from '@/shared/api/client';
import type { operations } from '@/shared/api/schema';

export type FeedbackRequest = NonNullable<
  operations['submitFeedback']['requestBody']
>['content']['application/json'];
export type FeedbackReceipt =
  operations['submitFeedback']['responses']['201']['content']['application/json'];

export type Rating = FeedbackRequest['rating'];

export function submitFeedback(body: FeedbackRequest): Promise<FeedbackReceipt> {
  return request<FeedbackReceipt>('/feedback/', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

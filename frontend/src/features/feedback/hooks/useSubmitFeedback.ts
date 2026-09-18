import { useMutation } from '@tanstack/react-query';

import { submitFeedback, type FeedbackReceipt, type FeedbackRequest } from '../api/feedbackApi';

export function useSubmitFeedback() {
  return useMutation<FeedbackReceipt, Error, FeedbackRequest>({
    mutationFn: submitFeedback,
  });
}

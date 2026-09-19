import { useState, type FormEvent } from 'react';

import type { Rating } from '../api/feedbackApi';
import { useSubmitFeedback } from '../hooks/useSubmitFeedback';

/**
 * Asks how it went, once, at the end of the page.
 *
 * The rating is two radio inputs rather than toggle buttons: a real radio group
 * gives arrow-key navigation and announces "1 of 2" to a screen reader for
 * free, which hand-rolled buttons do not.
 */
export function FeedbackSection() {
  const [rating, setRating] = useState<Rating | null>(null);
  const [comment, setComment] = useState('');
  const submit = useSubmitFeedback();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (rating !== null) submit.mutate({ rating, comment: comment.trim() });
  }

  if (submit.isSuccess) {
    return (
      <section className="card feedback thanks" aria-live="polite">
        <h2>Thank you!</h2>
        <p className="muted">
          Your feedback is in. It genuinely shapes what gets built next — enjoy your time off.
        </p>
      </section>
    );
  }

  return (
    <section className="card feedback">
      <form onSubmit={handleSubmit}>
        <h2>How did you find it?</h2>
        <p className="muted">A quick verdict helps more than you&apos;d think.</p>

        <fieldset className="thumbs">
          <legend className="sr-only">Your verdict</legend>

          <label className={rating === 'up' ? 'thumb picked' : 'thumb'}>
            <input
              type="radio"
              name="rating"
              value="up"
              checked={rating === 'up'}
              onChange={() => setRating('up')}
            />
            Liked it
          </label>

          <label className={rating === 'down' ? 'thumb picked' : 'thumb'}>
            <input
              type="radio"
              name="rating"
              value="down"
              checked={rating === 'down'}
              onChange={() => setRating('down')}
            />
            Not really
          </label>
        </fieldset>

        <label className="suggest" htmlFor="comment">
          Anything to change, or add? <span className="muted">(optional)</span>
        </label>
        <textarea
          id="comment"
          name="comment"
          rows={3}
          maxLength={2000}
          value={comment}
          placeholder="What would make this better for you?"
          onChange={(event) => setComment(event.target.value)}
        />

        <div className="feedback-actions">
          <button type="submit" disabled={rating === null || submit.isPending}>
            {submit.isPending ? 'Sending…' : 'Send feedback'}
          </button>
          {rating === null && <span className="muted hint-inline">Choose one first</span>}
        </div>

        {submit.isError && (
          <p className="error" role="alert">
            That didn&apos;t send. Try once more?
          </p>
        )}
      </form>
    </section>
  );
}

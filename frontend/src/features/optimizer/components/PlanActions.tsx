import { useState } from 'react';

import type { Plan } from '../api/optimizerApi';

type Props = { plan: Plan };

/** Take the plan with you: into a calendar, or to someone else. */
export function PlanActions({ plan }: Props) {
  const [copied, setCopied] = useState(false);

  const calendarUrl = `/api/v1/optimizer/plan.ics?days=${plan.budget}&year=${plan.year}`;
  const shareUrl = `${window.location.origin}${window.location.pathname}?days=${plan.budget}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be refused; the link is visible in the address
      // bar either way, so this is not worth an error message.
    }
  }

  return (
    <div className="actions">
      <a className="btn" href={calendarUrl} download={`vacancy-max-${plan.year}.ics`}>
        📅 Add to your calendar
      </a>
      <button type="button" className="btn ghost" onClick={() => void copy()}>
        {copied ? '✓ Link copied' : '🔗 Copy link'}
      </button>
    </div>
  );
}

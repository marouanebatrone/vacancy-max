import { formatDay, formatRange } from '@/shared/lib/dates';

import type { Break } from '../api/optimizerApi';

type Props = { brk: Break };

export function BreakCard({ brk }: Props) {
  const holidays = brk.holidays.map((holiday) => holiday.name).join(' · ');

  return (
    <article className="brk">
      <div className="when">{formatRange(brk.start, brk.end)}</div>

      <div className="count">
        {brk.total_days} days off
        <small>
          costs {brk.cost} {brk.cost === 1 ? 'day' : 'days'}
        </small>
      </div>

      <div className="why">
        {holidays}
        {brk.has_estimated_holidays && (
          <>
            {' '}
            <span className="badge" title="Morocco confirms lunar dates by moon sighting">
              Date not confirmed
            </span>
          </>
        )}
      </div>

      <div className="take">
        Request: <strong>{brk.leave_days.map(formatDay).join(', ')}</strong>
      </div>
    </article>
  );
}

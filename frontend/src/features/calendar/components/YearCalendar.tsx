import { useMemo } from 'react';

import type { Break } from '@/features/optimizer/api/optimizerApi';
import { fromISO, isWeekend, monthGrid, monthName, WEEKDAY_INITIALS } from '@/shared/lib/dates';

import type { Holiday } from '../api/calendarApi';

type Props = {
  year: number;
  breaks: Break[];
  holidays: Holiday[];
};

type DayInfo = { leave: boolean; inBreak: boolean; holiday?: Holiday };

/**
 * The year at a glance.
 *
 * Four states, told apart by shape as well as colour so the calendar still
 * reads without colour vision: a filled square is a day you request, a ring is
 * a public holiday (dashed when it falls on a weekend and Morocco gives nothing
 * back), a soft wash is the rest of a break, and grey is an ordinary weekend.
 */
export function YearCalendar({ year, breaks, holidays }: Props) {
  const index = useMemo(() => buildIndex(breaks, holidays), [breaks, holidays]);

  return (
    <>
      <div className="year">
        {Array.from({ length: 12 }, (_, month) => (
          <div className="month" key={month}>
            <h3>{monthName(year, month)}</h3>

            <div className="weekdays" aria-hidden="true">
              {WEEKDAY_INITIALS.map((initial, position) => (
                <span key={position}>{initial}</span>
              ))}
            </div>

            <div className="days">
              {monthGrid(year, month).map((iso, position) =>
                iso === null ? (
                  <div className="day pad" key={`pad-${position}`} />
                ) : (
                  <DayCell key={iso} iso={iso} info={index.get(iso)} />
                ),
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="legend">
        <span>
          <i className="swatch leave" /> Day you request
        </span>
        <span>
          <i className="swatch inbreak" /> Rest of the break
        </span>
        <span>
          <i className="swatch holiday" /> Public holiday
        </span>
        <span>
          <i className="swatch weekend" /> Weekend
        </span>
      </div>
    </>
  );
}

function DayCell({ iso, info }: { iso: string; info: DayInfo | undefined }) {
  const day = fromISO(iso).getDate();
  const weekend = isWeekend(iso);
  const holiday = info?.holiday;
  const observed = holiday !== undefined && !weekend;

  const classes = ['day'];
  if (weekend) classes.push('weekend');
  if (info?.inBreak) classes.push('inbreak');
  if (holiday) classes.push('holiday');
  if (holiday && !observed) classes.push('lost');
  if (info?.leave) classes.push('leave');

  return (
    <div className={classes.join(' ')} title={describe(iso, info, weekend)}>
      {day}
    </div>
  );
}

function describe(iso: string, info: DayInfo | undefined, weekend: boolean): string {
  const parts: string[] = [iso];

  if (info?.holiday) {
    parts.push(info.holiday.name);
    if (!info.holiday.is_confirmed) parts.push('(date not confirmed)');
    if (weekend) parts.push('— falls on a weekend, no day in lieu');
  }
  if (info?.leave) parts.push('You request this day');
  else if (info?.inBreak) parts.push('Part of your break');

  return parts.join(' · ');
}

function buildIndex(breaks: Break[], holidays: Holiday[]): Map<string, DayInfo> {
  const index = new Map<string, DayInfo>();

  const touch = (iso: string): DayInfo => {
    const existing = index.get(iso) ?? { leave: false, inBreak: false };
    index.set(iso, existing);
    return existing;
  };

  for (const holiday of holidays) {
    touch(holiday.date).holiday = holiday;
  }

  for (const brk of breaks) {
    const cursor = fromISO(brk.start);
    const end = fromISO(brk.end);
    while (cursor <= end) {
      const iso = toKey(cursor);
      touch(iso).inBreak = true;
      cursor.setDate(cursor.getDate() + 1);
    }
    for (const iso of brk.leave_days) {
      touch(iso).leave = true;
    }
  }

  return index;
}

function toKey(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

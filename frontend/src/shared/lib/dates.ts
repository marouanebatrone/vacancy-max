/**
 * Date helpers.
 *
 * The API speaks ISO 'YYYY-MM-DD' strings with no timezone, because a public
 * holiday has no timezone. We keep them as strings for comparison and only
 * build Date objects from local components, never by parsing an ISO string --
 * `new Date('2026-03-20')` is UTC midnight, which renders as the 19th for
 * anyone west of Greenwich.
 */

const LOCALE = 'en-GB';

export function toISO(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

export function fromISO(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1);
}

export function formatDay(iso: string): string {
  return fromISO(iso).toLocaleDateString(LOCALE, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

/** "Fri 20 – Mon 23 March", collapsing the month when both ends share it. */
export function formatRange(startISO: string, endISO: string): string {
  const start = fromISO(startISO);
  const end = fromISO(endISO);
  const sameMonth = start.getMonth() === end.getMonth();

  const left = start.toLocaleDateString(LOCALE, {
    weekday: 'short',
    day: 'numeric',
    ...(sameMonth ? {} : { month: 'short' }),
  });
  const right = end.toLocaleDateString(LOCALE, {
    weekday: 'short',
    day: 'numeric',
    month: sameMonth ? 'long' : 'short',
  });

  return `${left} – ${right}`;
}

export function monthName(year: number, month: number): string {
  return new Date(year, month, 1).toLocaleDateString(LOCALE, { month: 'long' });
}

/** Weekday initials, Monday first — the working week in Morocco. */
export const WEEKDAY_INITIALS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'] as const;

/**
 * One month as rows of seven, Monday first, padded with nulls so every grid
 * lines up under the same weekday columns.
 */
export function monthGrid(year: number, month: number): (string | null)[] {
  const first = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const leadingBlanks = (first.getDay() + 6) % 7; // shift Sunday=0 to Monday=0

  const cells: (string | null)[] = Array.from({ length: leadingBlanks }, () => null);
  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push(toISO(new Date(year, month, day)));
  }
  return cells;
}

export function isWeekend(iso: string): boolean {
  const weekday = fromISO(iso).getDay();
  return weekday === 0 || weekday === 6;
}

import { useState, type FormEvent } from 'react';

const DEFAULT_DAYS = 18; // Moroccan law's annual minimum: 1.5 working days a month.
const MAX_DAYS = 60;

type Props = {
  onSubmit: (days: number) => void;
  busy: boolean;
};

/**
 * The whole input surface: one number. Year, weekends and the holiday calendar
 * are the app's job, not the user's (ADR 0002).
 */
export function DaysForm({ onSubmit, busy }: Props) {
  const [value, setValue] = useState(String(DEFAULT_DAYS));

  const days = Number(value);
  const valid = Number.isInteger(days) && days >= 0 && days <= MAX_DAYS;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (valid) onSubmit(days);
  }

  return (
    <form className="card ask" onSubmit={handleSubmit}>
      <label htmlFor="days">How many leave days do you get this year?</label>
      <p className="hint">We&apos;ll turn them into as much time off as Morocco allows.</p>

      <div className="ask-row">
        <input
          id="days"
          name="days"
          type="number"
          inputMode="numeric"
          min={0}
          max={MAX_DAYS}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          aria-describedby="days-help"
        />
        <button type="submit" disabled={!valid || busy}>
          {busy ? 'Planning…' : 'Plan my year'}
        </button>
      </div>

      <p id="days-help" className="hint" style={{ margin: '16px 0 0', fontSize: '0.85rem' }}>
        Most Moroccan employees start at 18.
      </p>
    </form>
  );
}

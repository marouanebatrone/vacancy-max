/**
 * The page as a user meets it: type a number, get a year.
 *
 * Network is stubbed at fetch, so these assert what the UI does with a plan,
 * not what the backend computes -- that is covered by the API tests.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { App } from '@/app/App';

const PLAN = {
  year: 2026,
  budget: 18,
  strategy: 'max_days_off',
  summary: {
    total_days_off: 59,
    leave_used: 18,
    leave_unused: 0,
    efficiency: 3.28,
    break_count: 2,
    longest_break: 11,
    has_estimated_holidays: true,
  },
  breaks: [
    {
      start: '2026-05-01',
      end: '2026-05-04',
      total_days: 4,
      cost: 1,
      efficiency: 4.0,
      leave_days: ['2026-05-04'],
      holidays: [{ date: '2026-05-01', name: 'Labour Day', is_confirmed: true }],
      has_estimated_holidays: false,
    },
    {
      start: '2026-08-20',
      end: '2026-08-30',
      total_days: 11,
      cost: 3,
      efficiency: 3.67,
      leave_days: ['2026-08-24', '2026-08-27', '2026-08-28'],
      holidays: [{ date: '2026-08-25', name: 'Aid Al Mawlid (day 1)', is_confirmed: false }],
      has_estimated_holidays: true,
    },
  ],
};

const YEAR = {
  year: 2026,
  weekend: ['saturday', 'sunday'],
  stats: {
    total_days: 365,
    workdays: 246,
    weekend_days: 104,
    holidays_observed: 15,
    holidays_lost_to_weekend: 2,
    has_estimated_holidays: true,
  },
  holidays: [
    {
      date: '2026-05-01',
      name: 'Labour Day',
      name_fr: '',
      name_ar: '',
      kind: 'fixed',
      weekday: 'Friday',
      is_confirmed: true,
      uncertainty_days: 0,
      is_observed: true,
    },
  ],
};

function stubApi(plan: unknown = PLAN) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(url.includes('optimizer') ? plan : YEAR),
      }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('the planner', () => {
  it('asks for one number and nothing else', () => {
    stubApi();
    const { container } = render(<App />);

    expect(screen.getByLabelText(/how many leave days/i)).toHaveValue(18);
    // No year picker, no strategy selector: the product is one field (ADR 0002).
    expect(container.querySelectorAll('input')).toHaveLength(1);
    expect(container.querySelectorAll('select')).toHaveLength(0);
  });

  it('congratulates you with the days gained before anything else', async () => {
    stubApi();
    render(<App />);

    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));

    expect(await screen.findByText(/congratulations/i)).toBeInTheDocument();
    expect(screen.getByText('59')).toBeInTheDocument();
    expect(screen.getByText(/days away from the office/i)).toBeInTheDocument();
    // 59 days off for 18 spent = 41 you never had to ask for.
    expect(screen.getByText(/41 extra days/i)).toBeInTheDocument();
  });

  it('shows each break with what it costs and what to request', async () => {
    stubApi();
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));

    expect(await screen.findByText(/Labour Day/)).toBeInTheDocument();
    expect(screen.getByText(/11 days off/)).toBeInTheDocument();
    expect(screen.getByText(/Mon 24 Aug, Thu 27 Aug, Fri 28 Aug/)).toBeInTheDocument();
  });

  it('badges only the breaks resting on an unconfirmed lunar date', async () => {
    stubApi();
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));

    await screen.findByText(/Labour Day/);

    // One badge, on the Mawlid break only -- not on Labour Day.
    const badges = document.querySelectorAll('.badge');
    expect(badges).toHaveLength(1);
    expect(badges[0]?.closest('.brk')?.textContent).toMatch(/Mawlid/);

    // And exactly one line about it in the summary -- scoped to the hero, since
    // the "How does it work?" section explains moon sighting too.
    const hero = document.querySelector('.hero');
    expect(within(hero as HTMLElement).getByText(/moon sighting/i)).toBeInTheDocument();
  });

  it('draws the year with the requested days marked', async () => {
    stubApi();
    const { container } = render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));

    await waitFor(() => expect(container.querySelectorAll('.day.leave')).toHaveLength(4));
    expect(container.querySelectorAll('.month')).toHaveLength(12);
    expect(container.querySelector('.day.holiday')).toBeInTheDocument();
  });

  it('says so kindly when there is nothing to plan', async () => {
    stubApi({
      ...PLAN,
      budget: 0,
      summary: { ...PLAN.summary, break_count: 0, total_days_off: 0, leave_used: 0 },
      breaks: [],
    });
    render(<App />);

    // A different number, so this does not read the cache from another test --
    // App holds one QueryClient for the session, as a real page does.
    const input = screen.getByLabelText(/how many leave days/i);
    await userEvent.clear(input);
    await userEvent.type(input, '0');
    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));

    expect(await screen.findByText(/nothing to plan yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/congratulations/i)).not.toBeInTheDocument();
  });
});

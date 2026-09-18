/**
 * A plan is a pure function of its inputs, so the URL is the saved plan.
 * These tests pin that promise: open a link, get the same year back.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { App } from '@/app/App';

const PLAN = {
  year: 2026,
  budget: 12,
  strategy: 'max_days_off',
  summary: {
    total_days_off: 44,
    leave_used: 12,
    leave_unused: 0,
    efficiency: 3.67,
    break_count: 1,
    longest_break: 11,
    has_estimated_holidays: false,
  },
  breaks: [
    {
      start: '2026-08-20',
      end: '2026-08-30',
      total_days: 11,
      cost: 3,
      efficiency: 3.67,
      leave_days: ['2026-08-24', '2026-08-27', '2026-08-28'],
      holidays: [{ date: '2026-08-21', name: 'Youth Day', is_confirmed: true }],
      has_estimated_holidays: false,
    },
  ],
};

const YEAR = { year: 2026, weekend: [], stats: {}, holidays: [] };

function stubApi() {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(url.includes('optimizer') ? PLAN : YEAR),
      }),
    ),
  );
}

beforeEach(() => {
  window.history.replaceState(null, '', '/');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('sharing a plan', () => {
  it('plans straight away when opened from a shared link', async () => {
    window.history.replaceState(null, '', '/?days=12');
    stubApi();

    render(<App />);

    // No click needed: the link already said what to plan.
    expect(await screen.findByText(/congratulations/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/how many leave days/i)).toHaveValue(12);
  });

  it('ignores a nonsense value in the link rather than erroring', () => {
    window.history.replaceState(null, '', '/?days=banana');
    stubApi();

    render(<App />);

    expect(screen.getByLabelText(/how many leave days/i)).toHaveValue(18);
    expect(screen.queryByText(/congratulations/i)).not.toBeInTheDocument();
  });

  it('puts the number in the URL once you ask, so the page is shareable', async () => {
    stubApi();
    render(<App />);

    await userEvent.click(screen.getByRole('button', { name: /plan my year/i }));
    await screen.findByText(/congratulations/i);

    expect(window.location.search).toBe('?days=18');
  });

  it('offers the plan as a calendar file', async () => {
    window.history.replaceState(null, '', '/?days=12');
    stubApi();
    render(<App />);

    const link = await screen.findByRole('link', { name: /add to your calendar/i });

    expect(link).toHaveAttribute('href', '/api/v1/optimizer/plan.ics?days=12&year=2026');
    expect(link).toHaveAttribute('download', 'vacancy-max-2026.ics');
  });

  it('copies a link that reproduces the same plan', async () => {
    window.history.replaceState(null, '', '/?days=12');
    stubApi();
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });

    render(<App />);
    await userEvent.click(await screen.findByRole('button', { name: /copy link/i }));

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringMatching(/\?days=12$/)),
    );
    expect(await screen.findByText(/link copied/i)).toBeInTheDocument();
  });
});

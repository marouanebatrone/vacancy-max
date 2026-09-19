/**
 * The explanation sits between the year and the feedback form, closed until
 * asked for -- available to anyone who wonders, in the way of nobody who doesn't.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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
  window.history.replaceState(null, '', '/?days=18');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('how it works', () => {
  it('starts closed, so it explains only when asked', async () => {
    stubApi();
    const { container } = render(<App />);

    const details = await screen.findByText(/how does it work/i);
    expect(details.closest('details')).not.toHaveAttribute('open');
    expect(container.querySelector('.how')).toBeInTheDocument();
  });

  it('opens on click', async () => {
    stubApi();
    render(<App />);

    const summary = await screen.findByText(/how does it work/i);
    await userEvent.click(summary);

    expect(summary.closest('details')).toHaveAttribute('open');
  });

  it('explains the bridge in plain terms, with the real numbers', async () => {
    stubApi();
    await screen.findByText(/how does it work/i, {}, { container: render(<App />).container });

    expect(screen.getByText(/11 days away from work for 3 days of leave/i)).toBeInTheDocument();
    expect(screen.getByText(/checks every possibility/i)).toBeInTheDocument();
  });

  it('is upfront about weekends and unconfirmed dates', async () => {
    stubApi();
    render(<App />);
    await screen.findByText(/how does it work/i);

    expect(screen.getByText(/no day in lieu/i)).toBeInTheDocument();
    expect(screen.getByText(/moon sighting/i)).toBeInTheDocument();
  });

  it('sits after the calendar and before the feedback form', async () => {
    stubApi();
    const { container } = render(<App />);
    await screen.findByText(/how does it work/i);

    const how = container.querySelector('.how');
    const feedback = container.querySelector('.feedback');
    const calendar = container.querySelector('.year');

    expect(how).toBeTruthy();
    expect(feedback).toBeTruthy();
    expect(calendar?.compareDocumentPosition(how!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(how?.compareDocumentPosition(feedback!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });
});

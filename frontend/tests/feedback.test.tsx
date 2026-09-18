/**
 * The feedback section: a verdict, an optional suggestion, then a thank you.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
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
      leave_days: ['2026-08-24'],
      holidays: [{ date: '2026-08-21', name: 'Youth Day', is_confirmed: true }],
      has_estimated_holidays: false,
    },
  ],
};

const YEAR = { year: 2026, weekend: [], stats: {}, holidays: [] };

type Call = { url: string; body: unknown };

function stubApi(feedbackFails = false) {
  const calls: Call[] = [];

  vi.stubGlobal(
    'fetch',
    vi.fn((url: string, init?: RequestInit) => {
      const body = typeof init?.body === 'string' ? (JSON.parse(init.body) as unknown) : undefined;
      calls.push({ url, body });

      if (url.includes('feedback')) {
        return Promise.resolve({
          ok: !feedbackFails,
          status: feedbackFails ? 500 : 201,
          json: () => Promise.resolve(feedbackFails ? {} : { id: 'a-uuid' }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(url.includes('optimizer') ? PLAN : YEAR),
      });
    }),
  );

  return calls;
}

/** The section only appears once there is a plan to have an opinion about. */
async function openPlan() {
  render(<App />);
  await screen.findByRole('heading', { name: /how did you find it/i });
}

beforeEach(() => {
  window.history.replaceState(null, '', '/?days=18');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('the feedback section', () => {
  it('asks in a friendly way and offers exactly two verdicts', async () => {
    stubApi();
    await openPlan();

    const group = screen.getByRole('group', { name: /your verdict/i });
    expect(within(group).getAllByRole('radio')).toHaveLength(2);
    expect(screen.getByLabelText(/liked it/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/not really/i)).toBeInTheDocument();
  });

  it('will not submit until a verdict is chosen', async () => {
    stubApi();
    await openPlan();

    expect(screen.getByRole('button', { name: /send feedback/i })).toBeDisabled();

    await userEvent.click(screen.getByLabelText(/liked it/i));

    expect(screen.getByRole('button', { name: /send feedback/i })).toBeEnabled();
  });

  it('sends a thumbs up on its own, with no comment', async () => {
    const calls = stubApi();
    await openPlan();

    await userEvent.click(screen.getByLabelText(/liked it/i));
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }));

    await waitFor(() => {
      const sent = calls.find((call) => call.url.includes('feedback'));
      expect(sent?.body).toEqual({ rating: 'up', comment: '' });
    });
  });

  it('sends a thumbs down with the suggestion', async () => {
    const calls = stubApi();
    await openPlan();

    await userEvent.click(screen.getByLabelText(/not really/i));
    await userEvent.type(screen.getByLabelText(/anything to change/i), 'Add 2028 please');
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }));

    await waitFor(() => {
      const sent = calls.find((call) => call.url.includes('feedback'));
      expect(sent?.body).toEqual({ rating: 'down', comment: 'Add 2028 please' });
    });
  });

  it('replaces the form with a thank you once sent', async () => {
    stubApi();
    await openPlan();

    await userEvent.click(screen.getByLabelText(/liked it/i));
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }));

    expect(await screen.findByText(/thank you/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /send feedback/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/liked it/i)).not.toBeInTheDocument();
  });

  it('keeps what you wrote if sending fails', async () => {
    stubApi(true);
    await openPlan();

    await userEvent.click(screen.getByLabelText(/not really/i));
    await userEvent.type(screen.getByLabelText(/anything to change/i), 'Slow on mobile');
    await userEvent.click(screen.getByRole('button', { name: /send feedback/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/didn't send/i);
    expect(screen.getByLabelText(/anything to change/i)).toHaveValue('Slow on mobile');
    expect(screen.queryByText(/thank you/i)).not.toBeInTheDocument();
  });
});

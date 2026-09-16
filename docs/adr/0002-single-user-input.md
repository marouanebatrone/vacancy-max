# ADR 0002 — The user supplies exactly one number

**Status:** accepted · 2026-09-16

## Context

A leave planner could plausibly ask for a year, a weekend convention, a country,
blackout dates, a company leave-year start. Every one of those is a field the
user must understand before seeing any value.

## Decision

The only input is **the number of leave days the company grants**. The year
defaults to the current one, the weekend is Sat-Sun, the holiday set is
Moroccan, all server-side.

    POST /api/v1/optimizer/plan/   {"days": 18}

The API may *accept* an optional `year`, but the UI must not ask for it.

## Consequences

- The first screen is one field and one button. Time-to-value is seconds.
- Personalization (blackout dates, company policy, carry-over) becomes an
  opt-in refinement layered on a working plan, never a prerequisite to one.
- The backend owns all calendar knowledge, which is where correctness lives.

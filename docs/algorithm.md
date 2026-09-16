# The optimizer

**Problem.** Given a leave budget `B` and a year's calendar, choose which
workdays to request off so that total time away from work is maximal.

This is exactly solvable. No heuristics, no greedy approximation.

## Step 1 — type the year

A 365/366-entry array, each day `WORKDAY`, `WEEKEND` or `HOLIDAY`.

## Step 2 — enumerate candidate breaks

A candidate is a window `[i..j]` where `i` and `j` are workdays. For each:

- `cost(i, j)` = number of workdays inside -- discard if `> B`
- expand the window outward across adjacent free days
- `value(i, j)` = calendar length of that expanded run

Prune windows whose endpoints are not adjacent to a free day: extending a break
into empty space costs leave and buys nothing. With ~250 workdays the full
enumeration is a few thousand candidates -- microseconds.

## Step 3 — choose a non-overlapping subset

Weighted interval scheduling crossed with a knapsack:

    dp[d][b] = best total value using days up to d having spent b leave days

Two transitions per state: skip day `d`, or take the candidate break ending at
`d` and jump to `dp[start - 2][b - cost]` (`- 2` keeps breaks from touching; two
adjacent breaks are a single longer candidate already in the set). Complexity
`O(days x B)` with `O(1)` work per candidate. Milliseconds for a full year.

## Step 4 — anchor to holidays

Steps 1-3 solve the stated problem exactly, and the result is useless.

Maximizing days off alone is degenerate: a lone Friday buys three days for one,
the same ratio as most real bridges, and a year has fifty-two Fridays but only
ten holidays. The true optimum for an 18-day budget is therefore *eighteen
scattered three-day weekends*, bridging nothing. Mathematically perfect, and
not what anyone asked for.

So a candidate is eligible only if the resulting break **contains a public
holiday**. Anchoring is a property of the break, not of each day: a workday far
from any holiday still qualifies when the whole stretch taken reaches one, which
is just a longer holiday. Leave that buys no bridge goes unspent and is reported
as `leave_unused`, staying the user's to take whenever they like.

With that one rule, 18 days in 2026 becomes 59 days off across 11 breaks, every
one of them wrapped around a real holiday.

## Step 5 — strategies

The objective is a parameter, not a hard-coded sum. The DP never changes and
stays exact for whichever scoring is chosen:

- `MAX_DAYS_OFF` (default) — score = break length. Maximizes total days off.
- `LONGEST_BREAK` — score = length². Convex, so concentrating always beats
  spreading: one 10-day break scores 100 where two 5-day breaks score 50.

A `SPREAD` strategy (rest distributed evenly through the year) is **not
implemented**. It needs positional state in the DP rather than a per-break
score, so it is deferred rather than faked.

## Tie-breaking

DP cells hold `(score, leave_left_over)`, so comparing the tuple gives the
tie-break for free: among equally good plans, prefer the one that spends less
leave. Getting 44 days off for 16 days beats getting them for 18.

## How it is verified

Three ways, in `tests/domain/test_solver.py`:

**A brute-force oracle.** On small calendars, every subset of workdays is
enumerated and the true maximum compared against the solver's answer, over 250
generated cases. "Exact" is a strong claim and this is the only honest way to
back it. Both mutations tried against it — letting breaks touch, and taking the
first candidate greedily — are caught.

**Hand-checked cases.** Small patterns with a known right answer.

**Invariants**, property-tested with Hypothesis over random calendars:

1. Leave days used ≤ budget
2. Every chosen leave day is a workday
3. No two returned breaks overlap or touch
4. Value is monotone non-decreasing in the budget
5. Efficiency ratio > 1 for every returned break
6. Every break contains a public holiday
7. Budget 0 returns an empty plan
8. The same inputs always produce the same plan

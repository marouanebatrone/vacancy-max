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

## Step 4 — strategies

The objective is a parameter, not a hard-coded sum:

- `MAX_DAYS_OFF` (default) — maximize total calendar days off
- `LONGEST_BREAK` — favour one long holiday over several short ones
- `SPREAD` — penalize clustering, aim for regular rest through the year

## Invariants for property-based tests

Hypothesis generates arbitrary calendars and budgets; these must always hold:

1. Leave days used `<=` B
2. Every chosen leave day is a workday
3. No two returned breaks overlap or touch
4. Value is monotone non-decreasing in `B`
5. Efficiency ratio `>= 1` for every returned break
6. `B = 0` returns an empty plan

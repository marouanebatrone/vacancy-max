# optimizer

## `domain/` — the crown jewel

Pure Python. **No Django import may ever appear in this package**, and CI enforces it.
Frozen dataclasses in, frozen dataclasses out; no I/O, no clock, no randomness.
That is what makes it property-testable with Hypothesis and fast enough to run
thousands of times in a test suite.

| module          | responsibility                                               |
| --------------- | ------------------------------------------------------------ |
| `types.py`      | `DayType`, `Day`, `Calendar`, `Break`, `Plan`                 |
| `candidates.py` | enumerate every feasible break and its (cost, value)          |
| `solver.py`     | pick the best non-overlapping subset under the leave budget   |
| `strategies.py` | the objective: max total days off, or longest single break     |

Days off, leave spent and efficiency are properties on `Break` and `Plan`
rather than a separate metrics module: they are facts about those values, not
a calculation anyone performs on them.

## `services.py` — the only bridge

DB models in → domain dataclasses → domain result → serializable output.
Views stay thin and call nothing but this.

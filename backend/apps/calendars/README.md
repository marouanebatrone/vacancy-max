# calendars

Owns *what days exist and what kind of day each one is*. Knows nothing about
optimization; it answers exactly one question: **is this day off?**

| file | role |
| --- | --- |
| `data/holidays_ma.yaml` | source of truth. Hand-edited, reviewed like code. |
| `models.py` | `Holiday` -- the queryable projection of that YAML |
| `services.py` | the only module importing both the ORM and the domain |
| `management/commands/seed_holidays.py` | idempotent loader, safe on every deploy |
| `api/` | thin read-only views over `services` |

## Decisions worth knowing

**One row per day.** A two-day Eid is two rows (`eid-al-fitr-1`, `-2`), so the
optimizer never expands anything: every row is exactly one day off.

**Identity is `(year, slug)`, not date.** A Hijri date corrected after the
official announcement updates its row in place instead of leaving the stale
date behind as a duplicate.

**Weekend beats holiday.** Morocco grants no day in lieu, so a holiday landing
on Sat/Sun stays `WEEKEND` -- the optimizer must never believe it bought a free
day it never got. The holiday name is still attached so the UI can show what the
year lost. In 2027 that is seven of seventeen holidays.

**Two holidays can share a date.** 2027-08-14 is both Oued Ed-Dahab and Aid Al
Mawlid. That is one day off; the names are joined, never silently overwritten.

**An unseeded year raises rather than returning an empty calendar.** A
holiday-free year looks plausible and would produce a confidently wrong plan.

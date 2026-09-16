# calendars

Owns *what days exist and what kind of day each one is*.

- `models.py`      — `Holiday` (fixed Gregorian or Hijri, confirmed or estimated)
- `data/*.yaml`    — the source of truth, seeded into the DB; reviewable in a PR
- `services.py`    — `build_year_calendar(year) -> optimizer.domain.Calendar`
- `management/commands/seed_holidays.py` — idempotent loader for the YAML

Nothing here knows about optimization. It answers one question: *is this day off?*

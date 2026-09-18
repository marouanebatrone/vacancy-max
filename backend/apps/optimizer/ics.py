"""Render a plan as an iCalendar file (RFC 5545).

Pure text generation over the service layer's PlanView -- no Django, no I/O --
so it is cheap to test and the awkward parts of the format (CRLF, octet-aware
line folding, TEXT escaping) can be pinned down exactly. Calendar clients are
unforgiving: a lone LF or an over-long line and the import silently fails.
"""

from __future__ import annotations

import datetime as dt

from .services import BreakView, PlanView

PRODID = "-//Vacancy Max//Moroccan leave planner//EN"

#: RFC 5545 §3.1: lines are at most 75 octets, excluding the CRLF.
MAX_OCTETS = 75


def render_calendar(plan: PlanView, *, now: dt.datetime | None = None) -> str:
    """The whole plan as one .ics document, ready to import."""
    stamp = (now or dt.datetime.now(dt.UTC)).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(f'Time off {plan.year}')}",
    ]
    for index, brk in enumerate(plan.breaks, start=1):
        lines.extend(_event(brk, plan.year, index, stamp))
    lines.append("END:VCALENDAR")

    # RFC 5545 §3.1 again: CRLF between lines, and a trailing one.
    return "".join(f"{folded}\r\n" for line in lines for folded in [_fold(line)])


def _event(brk: BreakView, year: int, index: int, stamp: str) -> list[str]:
    holidays = " + ".join(holiday.name for holiday in brk.holidays)

    return [
        "BEGIN:VEVENT",
        f"UID:{year}-{index}-{brk.start.isoformat()}@vacancy-max",
        f"DTSTAMP:{stamp}",
        # All-day events use DATE values, and DTEND is *exclusive* -- so a break
        # ending on the 30th ends the calendar entry on the 31st. Off by one
        # here and every holiday looks a day short.
        f"DTSTART;VALUE=DATE:{_date(brk.start)}",
        f"DTEND;VALUE=DATE:{_date(brk.end + dt.timedelta(days=1))}",
        f"SUMMARY:{_escape(f'{brk.total_days} days off — {holidays}')}",
        f"DESCRIPTION:{_escape(_description(brk, holidays))}",
        "TRANSP:OPAQUE",
        "END:VEVENT",
    ]


def _description(brk: BreakView, holidays: str) -> str:
    days = "\n".join(f"  - {day.strftime('%a %d %b %Y')}" for day in brk.leave_days)
    leave_word = "day" if brk.cost == 1 else "days"

    parts = [
        f"{brk.total_days} days off, from {brk.cost} {leave_word} of leave.",
        "",
        f"Request {'this day' if brk.cost == 1 else 'these days'} off:",
        days,
        "",
        f"Public holidays in this break: {holidays}",
    ]
    if brk.has_estimated_holidays:
        parts += [
            "",
            "Note: this break depends on an Islamic holiday whose date Morocco "
            "confirms by moon sighting. Check the official announcement before "
            "booking anything.",
        ]
    parts += ["", "Planned with Vacancy Max."]
    return "\n".join(parts)


def _date(day: dt.date) -> str:
    return day.strftime("%Y%m%d")


def _escape(text: str) -> str:
    """Escape a TEXT value: backslash first, or it would double-escape the rest."""
    return text.replace("\\", r"\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def _fold(line: str) -> str:
    """Fold to 75 octets per line, continuing with CRLF + one space.

    Counted in octets, not characters, and never split inside a multi-byte
    character -- Arabic and accented holiday names would otherwise be cut in
    half and arrive as mojibake.
    """
    if len(line.encode("utf-8")) <= MAX_OCTETS:
        return line

    chunks: list[str] = []
    current = ""
    budget = MAX_OCTETS

    for char in line:
        size = len(char.encode("utf-8"))
        if len(current.encode("utf-8")) + size > budget:
            chunks.append(current)
            current = char
            budget = MAX_OCTETS - 1  # the leading space on a continuation line
        else:
            current += char
    chunks.append(current)

    return "\r\n ".join(chunks)

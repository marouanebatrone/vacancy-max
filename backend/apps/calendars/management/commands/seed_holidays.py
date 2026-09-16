"""Load the curated holiday YAML into the database.

Idempotent by design: running it twice changes nothing, and running it after a
Hijri date is officially announced updates that row in place. Safe to run on
every deploy.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, TypedDict

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.calendars.models import Holiday, HolidayKind
from apps.calendars.services import supported_years

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "holidays_ma.yaml"


class SeedResult(TypedDict):
    created: int
    updated: int


class Command(BaseCommand):
    help = "Seed Moroccan public holidays from data/holidays_ma.yaml (idempotent)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--years",
            nargs="+",
            type=int,
            default=supported_years(),
            help="Years to seed. Defaults to every supported year.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if not DATA_FILE.exists():
            raise CommandError(f"Holiday data file not found: {DATA_FILE}")

        data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
        years: list[int] = options["years"]

        totals: SeedResult = {"created": 0, "updated": 0}
        for year in years:
            result = self._seed_year(data, year)
            totals["created"] += result["created"]
            totals["updated"] += result["updated"]
            self.stdout.write(f"  {year}: {result['created']} created, {result['updated']} updated")

        estimated = Holiday.objects.filter(year__in=years, is_confirmed=False).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {totals['created'] + totals['updated']} holidays "
                f"({totals['created']} new, {totals['updated']} updated)."
            )
        )
        if estimated:
            self.stdout.write(
                self.style.WARNING(
                    f"{estimated} lunar dates are still estimates. Confirm them against "
                    "the Ministry of Habous announcements before anyone books a flight."
                )
            )

    def _seed_year(self, data: dict[str, Any], year: int) -> SeedResult:
        result: SeedResult = {"created": 0, "updated": 0}

        for entry in data.get("fixed", []):
            if year < entry.get("since", 0):
                continue  # e.g. Amazigh New Year did not exist before 2024
            self._upsert(
                slug=entry["slug"],
                date=dt.date(year, entry["month"], entry["day"]),
                kind=HolidayKind.FIXED,
                entry=entry,
                is_confirmed=True,
                uncertainty_days=0,
                result=result,
            )

        hijri_for_year = data.get("hijri", {}).get(year)
        if hijri_for_year is None:
            raise CommandError(
                f"No Hijri dates for {year} in {DATA_FILE.name}. Add them before seeding: "
                "a year without Eid would silently produce a wrong plan."
            )

        for entry in hijri_for_year:
            self._upsert(
                slug=entry["slug"],
                date=entry["date"],
                kind=HolidayKind.HIJRI,
                entry=entry,
                is_confirmed=entry.get("is_confirmed", False),
                uncertainty_days=entry.get("uncertainty_days", 1),
                result=result,
            )

        return result

    def _upsert(
        self,
        *,
        slug: str,
        date: dt.date,
        kind: HolidayKind,
        entry: dict[str, Any],
        is_confirmed: bool,
        uncertainty_days: int,
        result: SeedResult,
    ) -> None:
        _, created = Holiday.objects.update_or_create(
            year=date.year,
            slug=slug,
            defaults={
                "date": date,
                "name": entry["name"],
                "name_fr": entry.get("name_fr", ""),
                "name_ar": entry.get("name_ar", ""),
                "kind": kind,
                "is_confirmed": is_confirmed,
                "uncertainty_days": uncertainty_days,
            },
        )
        result["created" if created else "updated"] += 1

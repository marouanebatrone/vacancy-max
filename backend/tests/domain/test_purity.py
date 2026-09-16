"""Architectural guard: the domain layer stays framework-free.

If this test fails, someone imported Django into the optimizer core and the
whole testing strategy is at risk. Fix the import, don't relax the test.
"""

from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[2] / "apps" / "optimizer" / "domain"


def test_domain_has_no_django_imports() -> None:
    offenders = [
        path.name
        for path in DOMAIN.rglob("*.py")
        if "django" in path.read_text() or "from apps" in path.read_text()
    ]
    assert offenders == [], f"Django/app imports leaked into the pure domain: {offenders}"

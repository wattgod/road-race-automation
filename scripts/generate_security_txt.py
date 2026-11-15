#!/usr/bin/env python3
"""Write web/.well-known/security.txt (RFC 9116).

Expires is set one year from the generation date. push_wordpress.py
--sync-llms-txt regenerates it at deploy time, so each deploy moves the date
forward instead of letting the tracked copy run out.

Usage:
    python3 scripts/generate_security_txt.py
"""

from datetime import date, datetime, time, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "web" / ".well-known" / "security.txt"

CONTACT = "mailto:gravelgodcoaching@gmail.com"
CANONICAL = "https://roadielabs.com/.well-known/security.txt"


def one_year_after(today: date) -> date:
    try:
        return today.replace(year=today.year + 1)
    except ValueError:  # Feb 29
        return today.replace(year=today.year + 1, day=28)


def build_security_txt(today: date) -> str:
    expires = datetime.combine(one_year_after(today), time(0, 0), tzinfo=timezone.utc)
    return (
        f"Contact: {CONTACT}\n"
        f"Expires: {expires.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        "Preferred-Languages: en\n"
        f"Canonical: {CANONICAL}\n"
    )


def write_security_txt(today: date = None, path: Path = OUTPUT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_security_txt(today or date.today()), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(f"  wrote {write_security_txt().relative_to(PROJECT_ROOT)}")

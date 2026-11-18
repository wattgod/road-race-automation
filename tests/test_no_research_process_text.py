"""Public race-page text must state finished judgments, not the research process.

CLAUDE.md: "Write the finished judgment, never the research process." Race
pages render these fields straight from race-data/*.json, so phrases that
narrate how this database built or corrected a profile ("this profile
previously described...", "as of research", "previously on file") leak onto
roadielabs.com. This guard walks the publicly rendered sections and fails on
those phrases.

Skipped: youtube_data (real rider words and transcripts), the citations
section except each label (labels render in the source list), and any key
starting with "_" (internal).
"""

import json
import re
from pathlib import Path

import pytest

RACE_DATA_DIR = Path(__file__).parent.parent / "race-data"

PUBLIC_SECTIONS = (
    "biased_opinion",
    "course_description",
    "final_verdict",
    "history",
    "vitals",
    "climate",
)

SKIP_KEYS = {"youtube_data", "citations"}

PROCESS_PATTERNS = [
    r"this profile",
    r"on file\b",
    r"as of (this )?(research|review|wave)",
    r"research dump",
    r"audit pass",
    r"batch brief",
    r"editorial pass",
    r"this database",
    r"this listing's prior",
    r"previously (described|said|carried|conflated|listed)",
    r"do not promote",
    r"do not assert",
    # Same leak, other wording: references to the profile's own earlier state,
    # internal field names, and the database's own record.
    r"\b(our|the) prior (profile|file|entry|version|course description)",
    r"prior file\b",
    r"prior profile's",
    r"\b(our|the database's)( own)? prior",
    r"prior listing",
    r"previously logged",
    r"catalog_flags",
    r"eligibility\.notes",
    r"youtube_data",
    r"this entry exists",
    r"the research (found|does not|did not)",
    r"we could verify",
    # Correction narratives that slipped past the first pass.
    r"\bwe(\'ve| have)? (corrected|updated|revised|fixed|moved|renamed)",
    r"\bour (old|earlier|previous|original) (data|vitals|profile|listing|figures)",
    r"on-file\b",
    r"as of this write-up",
    r"correcting a [\w-]+ (discrepancy|on-file|figure|distance|date)",
]
PROCESS_RE = re.compile("|".join(f"(?:{p})" for p in PROCESS_PATTERNS), re.IGNORECASE)

# Vitals render verbatim in the hero date/location line, the vitals table, RSS
# items and the search index, so they also may not carry dated research
# checks, source-by-source bookkeeping or instructions to the researcher. Keep
# the finished status ("2027 date not yet announced") and move the working
# note to vitals._notes, which no generator reads.
VITALS_PROCESS_PATTERNS = [
    r"\bas of 20\d\d",
    r"as of (this|verification)",
    r"do not assume",
    r"should not be treated",
    r"aggregator",
    r"in (the )?(available|current|accessible|reviewed)( official)? sources",
    r"not independently verified",
    r"current research",
    r"(verified|confirmed) via",
    r"when verified",
    r"sources (conflict|disagree)",
    r"source figures",
    r"see eligibility notes",
    r"per the \w[\w ]* (page|rules|road book)",
    r"corrects? stale",
    r"was incorrect",
    r"\(check [\w.-]+\.(com|org|net)",
    r"registration (page )?header",
    r"still (incorrectly )?(lists?|shows?)\b",
]
VITALS_PROCESS_RE = re.compile(
    "|".join(f"(?:{p})" for p in VITALS_PROCESS_PATTERNS), re.IGNORECASE
)

# Every public section (prose included): research-check timestamps, source
# bookkeeping and instructions to the researcher. A plain time anchor
# ("six editions deep as of 2026") and a rider-facing warning about the
# organizer ("the official page still lists TBD") are finished judgments and
# stay allowed.
SECTION_PROCESS_PATTERNS = [
    r"as of (this|verification)",
    r"as of \d{1,2} \w+ 20\d\d",
    r"as of 20\d\d-\d\d",
    r"in (the )?(available|reviewed|accessible)( official)? sources",
    r"not independently (verified|confirmed)",
    r"(verified|confirmed) via",
    r"should not be treated",
    r"do not assume",
    r"aggregator",
    r"source figures",
    r"secondary sources",
    r"not securely verified",
    r"sources disagree on the exact",
    r"per the official [\w ]*page",
]
SECTION_PROCESS_RE = re.compile(
    "|".join(f"(?:{p})" for p in SECTION_PROCESS_PATTERNS), re.IGNORECASE
)


def _walk(node, path):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in SKIP_KEYS or str(key).startswith("_"):
                continue
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def _violations():
    found = []
    for f in sorted(RACE_DATA_DIR.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            race = json.load(fh).get("race", {})
        for section in PUBLIC_SECTIONS:
            if section not in race:
                continue
            for path, text in _walk(race[section], f".race.{section}"):
                for m in [*PROCESS_RE.finditer(text), *SECTION_PROCESS_RE.finditer(text)]:
                    start = max(0, m.start() - 60)
                    snippet = text[start : m.end() + 60].replace("\n", " ")
                    found.append(f"{f.stem} | {path} | {m.group(0)!r} | ...{snippet}...")
        for path, text in _walk(race.get("vitals") or {}, ".race.vitals"):
            for m in VITALS_PROCESS_RE.finditer(text):
                start = max(0, m.start() - 60)
                snippet = text[start : m.end() + 60].replace("\n", " ")
                found.append(f"{f.stem} | {path} | {m.group(0)!r} | ...{snippet}...")
        # Citation labels render in the page's source list, so they are public
        # too; they may quote a source ("Listing Marked Unconfirmed"), which none
        # of these patterns match.
        for i, cite in enumerate(race.get("citations") or []):
            label = cite.get("label", "") if isinstance(cite, dict) else ""
            for m in PROCESS_RE.finditer(label):
                found.append(f"{f.stem} | .race.citations[{i}].label | {m.group(0)!r} | ...{label[:160]}...")
    return found


def test_patterns_compile_and_match_examples():
    assert PROCESS_RE.search("not the sportive this profile previously described")
    assert PROCESS_RE.search("As of research, no GPX")
    assert PROCESS_RE.search("a figure previously on file")
    assert not PROCESS_RE.search("Unconfirmed for 2026")
    assert not PROCESS_RE.search("2026 field unconfirmed")
    assert VITALS_PROCESS_RE.search(
        "2027 dates not yet announced by NEABA as of 2026-08-03: official site "
        "and UCI GFWS calendar still list only May 16-17, 2026"
    )
    assert VITALS_PROCESS_RE.search("Not specified in available sources")
    assert not VITALS_PROCESS_RE.search("2026: May 16-17 (completed). 2027 dates not yet announced.")
    assert not VITALS_PROCESS_RE.search("intermediate cutoffs apply per the regulations")
    assert SECTION_PROCESS_RE.search("No 2027 date published yet as of this writing")
    assert SECTION_PROCESS_RE.search("isn't specified in available sources")
    assert SECTION_PROCESS_RE.search("A third-party aggregator lists a May 2026 date")
    assert not SECTION_PROCESS_RE.search("Six editions deep as of 2026 (founded 2021)")
    assert not SECTION_PROCESS_RE.search("the official page still lists the date as TBD")


def test_no_research_process_text_in_public_fields():
    violations = _violations()
    if violations:
        pytest.fail(
            f"{len(violations)} public string(s) narrate the research process "
            "instead of stating the finished judgment:\n" + "\n".join(violations)
        )

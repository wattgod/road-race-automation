#!/usr/bin/env python3
"""
Roadie Labs — Immune System, Layer 1: deterministic verifier + lane classifier.

This is the "immune system's" senses. It does three things and NOTHING else:

  1. DETECT   — reuse validate_profile.py's schema/scoring checks (the actual
                per-profile source of truth `preflight.py` itself calls
                indirectly via pytest), plus a search-index freshness check,
                near-duplicate detection, money-path wiring, a fabricated-claims
                pass (offline, reuses research-dumps/), and optionally the live
                404 / money-path checker. Every problem becomes one Finding.
  2. CLASSIFY — sort each Finding into exactly one lane:
        GREEN  (auto-heal)  safe & mechanical — a regenerate fixes it
        YELLOW (needs you)  judgment — a fix is proposed, but a human approves
        RED    (issue only) unsafe to auto-fix — money path / security / systemic
  3. REPORT   — write immune/report.json, append a run record to
                immune/ledger.jsonl, and print a human digest.

NOTE on this repo vs. the XC Ski Labs template this was cloned from:
`scripts/preflight.py` here is a step-RUNNER (it subprocess-calls pytest,
audit_colors.py, validate_citations.py, etc. in sequence and stops on the
first failure) — it has no importable check functions with an errors/warnings
list, unlike XC Ski's `preflight.PreflightResult`. The closest equivalent —
the actual schema/scoring source of truth — is `scripts/validate_profile.py`,
which already returns a clean `list[str]` of errors per profile. This script
imports THAT instead, so the criteria still "come for free" from the repo's
own code, not reinvented here.

IMPORTANT: this script never edits data, commits, or deploys. It is the
*verifier* a nightly repair loop would check candidate fixes against — the
Karpathy rule: a candidate fix only ships if it makes this script go green
WITHOUT turning anything new red. Anything else becomes a PR (YELLOW) or an
issue (RED).

Usage:
    python3 scripts/immune_check.py            # fast, offline: schema + index + duplicates + money-path wiring + claims
    python3 scripts/immune_check.py --regen     # regenerate index/pages first, then also check page parity
    python3 scripts/immune_check.py --live       # also run the live money-path / 404 check (network)
    python3 scripts/immune_check.py --json        # print machine JSON only (for the agent)

Exit code: 0 if no RED and no YELLOW findings, else 1 (so CI can gate on it).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RACE_DATA_DIR = PROJECT_ROOT / "race-data"
IMMUNE_DIR = PROJECT_ROOT / "immune"
REPORT_FILE = IMMUNE_DIR / "report.json"      # latest snapshot (gitignored — churns every run)
SCANS_FILE = IMMUNE_DIR / "scans.jsonl"       # scan telemetry / streak (gitignored)
LEDGER_FILE = IMMUNE_DIR / "ledger.jsonl"     # permanent FIX log (tracked — the memory)
BASELINE_FILE = IMMUNE_DIR / "baseline.json"  # known/accepted backlog fingerprints (tracked)

BRAND = "roadie-labs"
GREEN, YELLOW, RED = "green", "yellow", "red"

# Make the repo's own validators importable and reuse their logic (don't reinvent it).
sys.path.insert(0, str(SCRIPT_DIR))
import validate_profile  # noqa: E402


@dataclass
class Finding:
    code: str            # short stable slug, e.g. "index-drift"
    lane: str            # green | yellow | red
    severity: str        # critical | high | medium | low
    title: str           # one-line human summary
    detail: str           # the raw message / specifics
    remedy: str            # what a fix would do, in plain words
    auto_fix: str | None = None   # the exact safe command (GREEN only), else None
    source: str = "validate_profile"     # which detector raised it
    new: bool = True              # not in the accepted baseline (a new/worsening finding)


# ── Classification table ──────────────────────────────────────────────────────
# Each rule: (regex on the raw message, code, lane, severity, remedy, auto_fix cmd)
# Ordered — first match wins. Unmatched errors default to YELLOW/high (a human
# decides), which is the safe direction: never auto-touch something we can't
# confidently classify.
REGEN_INDEX = "python3 scripts/generate_index.py --with-jsonld"
REGEN_PAGES = "python3 wordpress/generate_neo_brutalist.py --all"

RULES: list[tuple[str, str, str, str, str, str | None]] = [
    # ── GREEN: safe, mechanical, deterministic regenerate ──
    (r"race-index\.json not found|Index has \d+ entries",
     "index-drift", GREEN, "high",
     "web/race-index.json is stale/missing/miscounted — regenerate it from the profiles.",
     REGEN_INDEX),
    (r"Output missing \d+ of \d+ race pages|wordpress/output/ directory not found",
     "pages-stale", GREEN, "high",
     "Generated race pages are stale/missing — regenerate wordpress/output/.", REGEN_PAGES),
    # ── YELLOW: judgment — propose a fix, human approves (includes ALL ratings) ──
    (r"overall_score=\d+ but dimensions sum to \d+",
     "score-math", YELLOW, "high",
     "A race's overall_score doesn't equal its fondo_rating dimensions sum. Proposed: "
     "recompute the score — but confirm the dimensions are what you intended (a score "
     "IS a rating).", None),
    (r"Invalid tier=",
     "tier-math", YELLOW, "high",
     "A race's tier doesn't match its score/prestige rule. Proposed: recompute the "
     "tier — confirm the inputs.", None),
    (r"\(must be 1-5\)|Missing fondo_rating\.",
     "rating-broken", YELLOW, "high",
     "A race's fondo_rating dimensions are missing or out of range — needs a human "
     "rating call.", None),
    (r"Invalid JSON",
     "json-invalid", YELLOW, "critical",
     "A profile file is malformed JSON — needs a careful human fix (auto-repair could "
     "silently change data).", None),
    (r"Missing race\.(name|slug|vitals|fondo_rating|final_verdict|citations)",
     "missing-content", YELLOW, "high",
     "A race is missing a required top-level section — a human fills it in.", None),
    (r"Missing vitals\.(distance_km|location|date)",
     "missing-content", YELLOW, "high",
     "A race is missing required vitals (distance/location/date) — a human fills it in.",
     None),
    (r"missing distance_mi \(dual units required\)|missing elevation_ft \(dual units required\)",
     "missing-dual-units", YELLOW, "medium",
     "A race has one unit of a pair (km/mi or m/ft) but not the other — a human "
     "back-fills the conversion.", None),
    (r"Unknown discipline",
     "bad-discipline", YELLOW, "medium",
     "A race has an invalid discipline value — a human sets gran_fondo/sportive/"
     "century/multi_stage/hillclimb.", None),
    (r"Only \d+ citations \(minimum 3\)|Citation \d+ missing URL",
     "citations-broken", YELLOW, "high",
     "A race doesn't meet the minimum-citation bar or has a citation without a URL — "
     "a human sources it (it's a trust claim).", None),
    (r"Missing final_verdict\.one_liner",
     "missing-verdict", YELLOW, "medium",
     "A race is missing its one-line verdict — a human writes it.", None),
    (r"climbing=\d+ but no climb_profile section",
     "climb-profile-missing", YELLOW, "low",
     "A hilly/mountainous race has no climb_profile section — likely one of the known "
     "`_needs_enrichment` placeholders; a human backfills the gradient data.", None),
    (r"unsupported claim|has_research.*false|NO RESEARCH DUMP",
     "fabricated-claim", YELLOW, "critical",
     "A prestige claim (championship/national/world/etc.) in the profile isn't backed "
     "by its research dump — anti-shill violation, a human verifies or removes it.",
     None),
    (r"Duplicate slugs|Duplicate names|Near-Duplicate Name",
     "duplicate-race", YELLOW, "high",
     "Two profiles look like the same event — a human picks the canonical one to keep.",
     None),
    # ── RED: unsafe to auto-fix, ever ──
    (r"\.env not in \.gitignore|hardcoded API key|Possible hardcoded API key",
     "security", RED, "critical",
     "Possible secret exposure — handle by hand, never auto-touch secrets.", None),
]


def classify(message: str, source: str = "validate_profile") -> Finding:
    for pattern, code, lane, severity, remedy, auto in RULES:
        if re.search(pattern, message):
            return Finding(code, lane, severity, code.replace("-", " ").title(),
                           message, remedy, auto, source)
    # Unknown error → safe default: a human looks at it.
    return Finding("unclassified", YELLOW, "high", "Unclassified issue",
                   message, "New kind of problem — a human should look and, once "
                   "understood, add a rule for it.", None, source)


# ── Detectors ─────────────────────────────────────────────────────────────────
def run_validate_profile() -> list[Finding]:
    """Run validate_profile.py's per-profile schema/scoring checks (the repo's own
    source of truth) and classify every error message."""
    findings: list[Finding] = []
    for path in sorted(RACE_DATA_DIR.glob("*.json")):
        for message in validate_profile.validate_profile(path):
            findings.append(classify(message))
    return findings


def check_security() -> list[Finding]:
    """Offline guard: .env must stay out of git, and no obvious hardcoded API keys
    in the scripts that ship. Never auto-touched — RED."""
    findings: list[Finding] = []
    gitignore = PROJECT_ROOT / ".gitignore"
    try:
        gi_text = gitignore.read_text(encoding="utf-8")
    except OSError:
        gi_text = ""
    if not re.search(r"^\.env$", gi_text, re.MULTILINE):
        findings.append(classify(".env not in .gitignore"))

    key_pattern = re.compile(
        r"sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|re_[a-zA-Z0-9]{20,}")
    for py_dir in ("scripts", "wordpress", "workers"):
        d = PROJECT_ROOT / py_dir
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if f.resolve() == Path(__file__).resolve():
                continue  # skip self (contains the detection pattern itself)
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if key_pattern.search(text):
                findings.append(classify(f"Possible hardcoded API key in {f.relative_to(PROJECT_ROOT)}"))
    return findings


def check_search_index() -> list[Finding]:
    """web/race-index.json must exist and have one entry per profile."""
    index_file = PROJECT_ROOT / "web" / "race-index.json"
    n_profiles = len(list(RACE_DATA_DIR.glob("*.json")))
    if not index_file.exists():
        return [classify("race-index.json not found")]
    try:
        index = json.loads(index_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [classify("race-index.json is invalid JSON")]
    n_index = len(index) if isinstance(index, list) else len(index.get("races", []))
    if n_index != n_profiles:
        return [classify(f"Index has {n_index} entries but race-data has {n_profiles} profiles")]
    return []


def check_output_pages() -> list[Finding]:
    """wordpress/output/ must have one {slug}.html per profile (only checked when
    --regen was requested or the dir already exists, same gating as XC Ski)."""
    output_dir = PROJECT_ROOT / "wordpress" / "output"
    if not output_dir.exists():
        return [classify("wordpress/output/ directory not found")]
    profiles = [f.stem for f in RACE_DATA_DIR.glob("*.json")]
    missing = [slug for slug in profiles if not (output_dir / f"{slug}.html").exists()]
    if missing:
        return [classify(f"Output missing {len(missing)} of {len(profiles)} race pages")]
    return []


def check_money_path_wiring() -> list[Finding]:
    """Offline guard: the race-page generator must still emit the questionnaire CTA.
    If a future edit drops it, that's a money-path regression — RED, never auto."""
    gen = PROJECT_ROOT / "wordpress" / "generate_neo_brutalist.py"
    try:
        src = gen.read_text(encoding="utf-8")
    except OSError:
        return [Finding("money-path-generator-missing", RED, "critical",
                        "Money Path Generator Missing", str(gen),
                        "The race-page generator is unreadable — the money path can't "
                        "be verified.", None, "immune")]
    if "/questionnaire/" not in src:
        return [Finding("money-path-cta-dropped", RED, "critical",
                        "Money Path CTA Dropped",
                        "generate_neo_brutalist.py no longer contains a /questionnaire/ CTA",
                        "The conversion CTA vanished from the page generator — restore it "
                        "before deploying. Money path, so never auto-fixed.",
                        None, "immune")]
    return []


def check_fuzzy_duplicates() -> list[Finding]:
    """Catch near-duplicate events hiding under different slugs (e.g. two profiles
    for the same climb under different names).

    Primary signal is a HIGH fuzzy-similarity between event names — precise enough
    to avoid flagging a whole race series that merely shares a citation domain.
    Sharing a citation domain only raises confidence; it never flags on its own."""
    from difflib import SequenceMatcher

    findings: list[Finding] = []
    profiles: list[tuple[str, dict]] = []
    for f in sorted(RACE_DATA_DIR.glob("*.json")):
        try:
            profiles.append((f.stem, json.loads(f.read_text(encoding="utf-8")).get("race", {})))
        except (OSError, json.JSONDecodeError):
            continue

    def canon(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    def first_citation_domain(race: dict) -> str:
        citations = race.get("citations") or []
        if citations and citations[0].get("url"):
            from urllib.parse import urlparse
            return urlparse(citations[0]["url"]).netloc.lower()
        return ""

    NAME_THRESHOLD = 0.88  # tuned in the XC Ski template: catches near-duplicates, skips series
    for i in range(len(profiles)):
        slug_a, race_a = profiles[i]
        name_a = canon(race_a.get("name") or slug_a)
        for j in range(i + 1, len(profiles)):
            slug_b, race_b = profiles[j]
            name_b = canon(race_b.get("name") or slug_b)
            ratio = SequenceMatcher(None, name_a, name_b).ratio()
            if ratio >= NAME_THRESHOLD:
                same_domain = (first_citation_domain(race_a)
                               and first_citation_domain(race_a) == first_citation_domain(race_b))
                conf = "same citation domain too" if same_domain else "distinct sources"
                findings.append(Finding(
                    "duplicate-race", YELLOW, "high", "Near-Duplicate Name",
                    f"'{slug_a}' and '{slug_b}' names ~{int(ratio * 100)}% similar "
                    f"({conf})",
                    "Likely the same event under two slugs — a human merges/removes one.",
                    None, "immune"))
    return findings


def run_fabricated_claims_check() -> list[Finding]:
    """Reuse the repo's own anti-shill detector (offline — checks race-data claims
    against research-dumps/, no network) and classify each finding."""
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "audit_fabricated_claims.py"), "--json"],
            capture_output=True, text=True, timeout=120, cwd=PROJECT_ROOT)
    except Exception as e:  # noqa: BLE001
        return [Finding("fabricated-claims-check-failed", YELLOW, "medium",
                        "Fabricated Claims Check Failed", str(e),
                        "audit_fabricated_claims.py couldn't run.", None,
                        "audit_fabricated_claims")]
    findings: list[Finding] = []
    try:
        # audit_fabricated_claims.py --json prints the JSON array followed by a
        # trailing "PASSED"/"FAILED" text line — json.loads() would choke on that
        # extra data, so decode only the first JSON value in the stream.
        claims, _ = json.JSONDecoder().raw_decode(proc.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return findings  # nothing parseable = nothing to report (script prints text on error too)
    for c in claims:
        research_note = "NO RESEARCH DUMP" if not c.get("has_research") else "not in research"
        findings.append(classify(
            f"{c.get('slug')}: unsupported claim [{c.get('claim_type')}] {c.get('field')} "
            f"({research_note})", source="audit_fabricated_claims"))
    return findings


def run_live_link_check() -> list[Finding]:
    """Run the existing live checker as a subprocess and parse its DEAD LINKS block.
    A dead link on the money path (/questionnaire/ or /coaching/) is a RED P0."""
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "check_links.py"), "--max-urls", "300"],
            capture_output=True, text=True, timeout=900)
    except Exception as e:  # noqa: BLE001
        return [Finding("live-check-failed", YELLOW, "medium", "Live Check Failed",
                        str(e), "The live link checker couldn't run — check network/site.",
                        None, "check_links")]
    findings: list[Finding] = []
    # Sectioned parse: an entry line only counts for the section whose header
    # was seen last, and any non-entry line closes the section.
    challenged: list[str] = []
    dead: list[tuple[str, str]] = []
    section = None
    for line in proc.stdout.splitlines():
        if line.startswith("WAF-CHALLENGED"):
            section = "waf"
            continue
        if line.startswith("DEAD LINKS"):
            section = "dead"
            continue
        m = re.match(r"\s+(\d+|ERR)\s+(\S+)$", line)
        if not m:
            section = None
            continue
        if section == "waf":
            challenged.append(m.group(2))
        elif section == "dead":
            dead.append((m.group(1), m.group(2)))
    if challenged:
        shown = sorted(set(challenged))
        findings.append(Finding(
            "live-check-challenged", YELLOW, "low", "Live Check Challenged by WAF",
            f"{len(shown)} URLs unverifiable behind SiteGround's bot challenge "
            f"(HTTP 202) after backoff retries: " + " ".join(shown[:12])
            + (f" (+{len(shown) - 12} more)" if len(shown) > 12 else ""),
            "The scanner tripped SiteGround's bot protection, so these URLs could not "
            "be verified this run — an inconclusive scan, not an outage (2026-07-22: "
            "18 false money-path-404/dead-link findings were exactly this). Re-run "
            "later; investigate only if it persists across days.",
            None, "check_links"))
    for status, url in dead:
        money = "/questionnaire/" in url or "/coaching/" in url
        findings.append(Finding(
            "money-path-404" if money else "dead-link",
            RED if money else YELLOW,
            "critical" if money else "medium",
            "Money-Path 404" if money else "Dead Link",
            f"{status}  {url}",
            ("A conversion link a visitor clicks is dead — likely the questionnaire/"
             "coaching dir isn't deployed or the cache wasn't purged. Money path, so "
             "a human confirms the re-deploy.") if money else
            "A same-site link is dead — a human confirms the fix.",
            None, "check_links"))
    # A crash or parse drift must be a finding, never a silent green:
    # rc 0 = clean, rc 1 = dead links (must have parsed some),
    # rc 2 = inconclusive (must have parsed a WAF block).
    rc = proc.returncode
    if rc not in (0, 1, 2) or (rc == 1 and not dead) or (rc == 2 and not challenged):
        findings.append(Finding(
            "live-check-failed", YELLOW, "medium", "Live Check Failed",
            f"check_links.py exited {rc} but its output parsed to "
            f"{len(dead)} dead / {len(challenged)} challenged URLs; "
            f"stderr tail: {proc.stderr[-400:].strip() or '(empty)'}",
            "The live link checker crashed or its output format drifted from what "
            "this parser expects — the site was NOT verified this run.",
            None, "check_links"))
    return findings


# ── Report + ledger ───────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint(f: Finding) -> str:
    """Stable identity for a finding, so the baseline can recognise a recurrence."""
    return f"{f.code}::{f.detail}"


def load_baseline() -> set[str]:
    """Fingerprints the user has accepted as known backlog (not alerted nightly)."""
    if not BASELINE_FILE.exists():
        return set()
    try:
        return set(json.loads(BASELINE_FILE.read_text(encoding="utf-8")).get("fingerprints", []))
    except (OSError, json.JSONDecodeError):
        return set()


def mark_new(findings: list[Finding], baseline: set[str]) -> None:
    """Flag each finding new/known vs the baseline. SAFETY: RED findings (money
    path / security / systemic) are ALWAYS treated as new — you can never
    accidentally baseline away an emergency."""
    for f in findings:
        f.new = f.lane == RED or fingerprint(f) not in baseline


def write_outputs(findings: list[Finding], mode: dict) -> dict:
    IMMUNE_DIR.mkdir(exist_ok=True)
    lanes = {GREEN: 0, YELLOW: 0, RED: 0}
    for f in findings:
        lanes[f.lane] += 1
    new_ct = sum(1 for f in findings if f.new)
    report = {
        "brand": BRAND,
        "generated_at": now_iso(),
        "mode": mode,
        "counts": {"total": len(findings), **lanes,
                   "new": new_ct, "backlog": len(findings) - new_ct},
        "findings": [asdict(f) for f in findings],
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # Append a compact run record to the scan telemetry (gitignored; feeds the streak).
    # The permanent ledger.jsonl is reserved for type:"fix" records (the memory) so it
    # only changes when something is actually healed — no git noise from routine scans.
    run_record = {
        "ts": report["generated_at"], "type": "scan", "brand": BRAND,
        "mode": mode, "counts": report["counts"],
        "codes": sorted({f.code for f in findings}),
    }
    with SCANS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(run_record) + "\n")
    return report


def print_digest(report: dict) -> None:
    findings = [Finding(**f) for f in report["findings"]]
    c = report["counts"]
    new = [f for f in findings if f.new]
    known = [f for f in findings if not f.new]
    print("=" * 60)
    print(f"🩺 {BRAND} — Immune scan  ({report['generated_at']})")
    print(f"   mode: {report['mode']}")
    print("=" * 60)

    def block(items, lane, emoji, label):
        items = [f for f in items if f.lane == lane]
        if not items:
            return
        print(f"\n{emoji} {label} ({len(items)})")
        # Group by code so a big class shows as a count + a few examples, not a wall.
        by_code: dict[str, list[Finding]] = {}
        for f in items:
            by_code.setdefault(f.code, []).append(f)
        for code, group in sorted(by_code.items(), key=lambda kv: -len(kv[1])):
            head = group[0]
            print(f"   • {code} ({len(group)}) — {head.remedy}")
            for f in group[:3]:
                print(f"       – {f.detail}")
            if len(group) > 3:
                print(f"       … +{len(group) - 3} more")

    if new:
        print(f"\n🆕 NEW SINCE LAST ACCEPTED BASELINE ({len(new)}) — this is what to look at")
        block(new, RED, "🔴", "ISSUE (money path / security / systemic — never auto-fixed)")
        block(new, YELLOW, "🟡", "NEEDS YOU (a fix is proposed → PR for your approval)")
        block(new, GREEN, "🟢", "AUTO-HEALABLE (the loop would fix these itself)")

    if known:
        by_code: dict[str, int] = {}
        for f in known:
            by_code[f.code] = by_code.get(f.code, 0) + 1
        print(f"\n📉 KNOWN BACKLOG ({len(known)}) — accepted, tracked, not alerted")
        for code, n in sorted(by_code.items(), key=lambda kv: -kv[1]):
            print(f"   · {n:>4}  {code}")

    print("\n" + "-" * 60)
    print(f"total {c['total']}  |  🆕 new {c.get('new', c['total'])}  📉 backlog {c.get('backlog', 0)}"
          f"  |  🟢 {c['green']}  🟡 {c['yellow']}  🔴 {c['red']}")
    if c["total"] == 0:
        print("🧬 All clear. Streak intact.")
    elif not new:
        print("🧬 Nothing new — all findings are accepted backlog.")
    print("-" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Roadie Labs immune system — Layer 1 verifier")
    parser.add_argument("--regen", action="store_true",
                        help="regenerate index/pages first (enables page-parity check)")
    parser.add_argument("--live", action="store_true",
                        help="also run the live money-path / 404 check (network)")
    parser.add_argument("--json", action="store_true", help="print machine JSON only")
    parser.add_argument("--fail-on", choices=["red", "any"], default="any",
                        help="exit non-zero on RED only, or on any NEW RED/YELLOW (default: any)")
    parser.add_argument("--accept-baseline", action="store_true",
                        help="catalogue ALL current findings as accepted backlog "
                             "(they stop alerting; only new/worsening issues alert after)")
    args = parser.parse_args()

    if args.regen:
        subprocess.run(REGEN_INDEX.split(), cwd=PROJECT_ROOT, check=False,
                       stdout=subprocess.DEVNULL)
        subprocess.run(REGEN_PAGES.split(), cwd=PROJECT_ROOT, check=False,
                       stdout=subprocess.DEVNULL)

    findings: list[Finding] = []
    findings += run_validate_profile()
    findings += check_security()
    findings += check_search_index()
    if args.regen or (PROJECT_ROOT / "wordpress" / "output").exists():
        findings += check_output_pages()
    findings += check_money_path_wiring()
    findings += check_fuzzy_duplicates()
    findings += run_fabricated_claims_check()
    if args.live:
        findings += run_live_link_check()

    if args.accept_baseline:
        # RED is never baselined (mark_new keeps it alerting); only accept non-RED.
        fps = sorted({fingerprint(f) for f in findings if f.lane != RED})
        IMMUNE_DIR.mkdir(exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(
            {"accepted_at": now_iso(), "brand": BRAND, "fingerprints": fps}, indent=2) + "\n",
            encoding="utf-8")
        reds = sum(1 for f in findings if f.lane == RED)
        print(f"✅ Accepted {len(fps)} findings as known backlog for {BRAND}.")
        if reds:
            print(f"⚠️  {reds} RED finding(s) were NOT baselined — they will keep alerting.")
        return 0

    mark_new(findings, load_baseline())
    mode = {"regen": args.regen, "live": args.live}
    report = write_outputs(findings, mode)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_digest(report)

    # Non-zero only on NEW attention-worthy findings, so CI / the agent gate on
    # what changed, not on accepted backlog.
    new = [f for f in findings if f.new]
    if args.fail_on == "red":
        return 1 if any(f.lane == RED for f in new) else 0
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())

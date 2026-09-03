#!/usr/bin/env python3
"""
Re-fetch the compliance corpus from authoritative sources and report what changed.

The /compliance/ folder is only trustworthy if somebody re-pulls it on a schedule. The FTC amended the
COPPA Rule in April 2025 with a compliance deadline of April 2026; a channel running on a stale local copy
would have been out of compliance without changing a line of its own process. This script is the thing that
stops that from happening quietly.

    python3 compliance/fetch_compliance.py --check      # stale? exit 1 if so. Cheap, offline, no network.
    python3 compliance/fetch_compliance.py --refresh    # re-download, diff against local, report
    python3 compliance/fetch_compliance.py --sources    # print the URLs a human must read manually

Stdlib only. No install step.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE_TEXT = HERE / "source_text"
RULES = HERE / "rules.json"
PROVENANCE = SOURCE_TEXT / "PROVENANCE.json"
LAST_FETCHED = HERE / "LAST_FETCHED.json"

TIMEOUT = 60
UA = "compliance-refresh/1.0 (nursery-rhyme agency; contact: channel owner)"

# ---------------------------------------------------------------------------
# Machine-fetchable primary law. These are U.S. Government works.
# ---------------------------------------------------------------------------
FETCHABLE = {
    "coppa-rule-16-cfr-part-312.txt": {
        "citation": "16 C.F.R. Part 312",
        "url": "https://www.ecfr.gov/api/versioner/v1/full/{today}/title-16.xml?part=312",
        "format": "xml",
        "note": "eCFR versioner API. {today} is substituted with today's date.",
    },
    "coppa-statute-15-usc-6501-6506.txt": {
        "citation": "15 U.S.C. 6501-6506",
        "url": "https://uscode.house.gov/view.xhtml?req=granuleid%3AUSC-prelim-title15-chapter91&edition=prelim",
        "format": "html",
        "note": "Office of the Law Revision Counsel. Confirm the 'laws in effect' date on the page.",
    },
    "copyright-17-usc-102-106-302-305.txt": {
        "citation": "17 U.S.C. 102, 106, 302-305",
        "url": "https://uscode.house.gov/view.xhtml?path=/prelim@title17&edition=prelim",
        "format": "html",
        "note": "Sections 114/115 excluded from the local copy: the build-time mirror predated the 2018 MMA.",
    },
}

# ---------------------------------------------------------------------------
# Pages a human must read. Copyrighted by their owners: linked, never mirrored.
# ---------------------------------------------------------------------------
READ_AT_SOURCE = [
    ("YouTube: set channel/video audience", "https://support.google.com/youtube/answer/9527654"),
    ("YouTube: watching made-for-kids content", "https://support.google.com/youtube/answer/9632097"),
    ("YouTube: ads on MFK content", "https://support.google.com/youtube/answer/9713557"),
    ("YouTube: child safety policy", "https://support.google.com/youtube/answer/2801999"),
    ("YouTube: quality principles for kids content", "https://support.google.com/youtube/answer/10774223"),
    ("YouTube: altered or synthetic content disclosure", "https://support.google.com/youtube/answer/14328491"),
    ("FTC: Children's Privacy hub", "https://www.ftc.gov/business-guidance/privacy-security/childrens-privacy"),
    ("FTC: Six-Step COPPA Compliance Plan", "https://www.ftc.gov/business-guidance/resources/childrens-online-privacy-protection-rule-six-step-compliance-plan-your-business"),
    ("FTC: COPPA FAQs", "https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions"),
    ("Copyright Office: Circular 15a, duration", "https://www.copyright.gov/circs/circ15a.pdf"),
    ("Copyright Office: public records / registration search", "https://www.copyright.gov/public-records/"),
]

GREEN, YELLOW, RED, DIM, BOLD, OFF = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{OFF}" if sys.stdout.isatty() else text


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rules() -> dict:
    if not RULES.exists():
        sys.exit(_c(f"FATAL: {RULES} is missing. The agency cannot operate without it.", RED))
    return json.loads(RULES.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------
def cmd_check(args) -> int:
    rules = load_rules()
    today = dt.date.today()
    due = dt.date.fromisoformat(rules["next_review_due"])
    days = (due - today).days

    print(f"{BOLD}Compliance freshness check{OFF}" if sys.stdout.isatty() else "Compliance freshness check")
    print(f"  last reviewed : {rules['last_reviewed']}")
    print(f"  next due      : {rules['next_review_due']}")
    print(f"  today         : {today.isoformat()}")

    missing = [n for n in FETCHABLE if not (SOURCE_TEXT / n).exists()]
    if missing:
        print(_c(f"\n  MISSING source text: {', '.join(missing)}", RED))
        print("  Run --refresh, or restore from version control. The pipeline is blocked.")
        return 1

    # Verify recorded hashes still match what is on disk.
    if PROVENANCE.exists():
        prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        drifted = []
        for doc in prov.get("documents", []):
            p = ROOT / doc["file"]
            if p.exists() and sha256_file(p) != doc["sha256"]:
                drifted.append(doc["file"])
        if drifted:
            print(_c(f"\n  TAMPER/DRIFT: on-disk text no longer matches PROVENANCE.json:", RED))
            for d in drifted:
                print(f"    - {d}")
            print("  Reference law must not be hand-edited. Restore it or re-run --refresh.")
            return 1

    if days < 0:
        overdue = -days
        if overdue > 30:
            print(_c(f"\n  BLOCKED: review is {overdue} days overdue (>30).", RED))
            print("  scripts/compliance_gate.py will refuse to run until this is resolved.")
            return 1
        print(_c(f"\n  OVERDUE by {overdue} day(s). Refresh now.", YELLOW))
        return 1

    colour = GREEN if days > 14 else YELLOW
    print(_c(f"\n  OK — {days} day(s) until the next required review.", colour))
    return 0


# ---------------------------------------------------------------------------
# --refresh
# ---------------------------------------------------------------------------
def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def cmd_refresh(args) -> int:
    today = dt.date.today().isoformat()
    outdir = HERE / "_fetched" / today
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Re-fetching primary law -> {outdir}\n")
    results, failures = [], 0

    for name, meta in FETCHABLE.items():
        url = meta["url"].format(today=today)
        local = SOURCE_TEXT / name
        local_hash = sha256_file(local) if local.exists() else None
        print(f"  {meta['citation']}\n    {url}")
        try:
            body = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print(_c(f"    FAILED: {e}", RED))
            print(_c("    -> Fetch manually and diff by hand. Do NOT mark this cycle complete.", YELLOW))
            failures += 1
            results.append({"file": name, "url": url, "status": "FETCH_FAILED", "error": str(e)})
            continue

        raw = outdir / f"{name}.{meta['format']}"
        raw.write_bytes(body)
        new_hash = hashlib.sha256(body).hexdigest()
        print(_c(f"    OK {len(body):,} bytes  sha256:{new_hash[:16]}", GREEN))
        results.append({
            "file": name, "url": url, "status": "FETCHED", "bytes": len(body),
            "raw_sha256": new_hash, "raw_path": str(raw.relative_to(ROOT)),
            "local_text_sha256": local_hash,
        })

    LAST_FETCHED.write_text(json.dumps({
        "fetched_on": today,
        "results": results,
        "read_at_source": [{"topic": t, "url": u} for t, u in READ_AT_SOURCE],
        "human_followup_required": True,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"\nWrote {LAST_FETCHED.relative_to(ROOT)}")
    print(_c(f"\n{'='*78}", DIM))
    print(f"{BOLD}A HUMAN MUST NOW DO THIS{OFF}" if sys.stdout.isatty() else "A HUMAN MUST NOW DO THIS")
    print("  1. Diff the newly fetched raw files against compliance/source_text/.")
    print("  2. Read every URL under 'read at source' below — platform policy is not machine-diffable.")
    print("  3. If anything changed: update the affected restatement docs and compliance/rules.json.")
    print("  4. Log the review in audit/CHANGELOG.md and audit/policy_update_tracker.csv.")
    print("  5. Set last_reviewed and next_review_due (+90 days) in compliance/rules.json.")
    print(_c(f"{'='*78}\n", DIM))
    cmd_sources(args)

    if failures:
        print(_c(f"{failures} source(s) failed to download. The cycle is NOT complete.", RED))
        return 1
    return 0


def cmd_sources(args) -> int:
    print("Read at source (copyrighted — linked, never mirrored):")
    for topic, url in READ_AT_SOURCE:
        print(f"  - {topic}\n      {url}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="offline staleness + integrity check")
    g.add_argument("--refresh", action="store_true", help="re-download primary law and report")
    g.add_argument("--sources", action="store_true", help="print URLs a human must read")
    args = ap.parse_args()
    if args.check:
        return cmd_check(args)
    if args.refresh:
        return cmd_refresh(args)
    return cmd_sources(args)


if __name__ == "__main__":
    sys.exit(main())

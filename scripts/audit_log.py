#!/usr/bin/env python3
"""
Append-only decision log. Operating rule #4: "Log every decision in /audit/ with date and reason."

Every generator and every gate calls log_decision(). The log is the thing that answers, six months later,
"why did we ship that?" - to a lawyer, to YouTube, or to yourself.

    python3 scripts/audit_log.py --stage review --decision FLAG \
        --reason "Frame 44 hand geometry unclear" --actor "Sam Ortiz" --ref VID-2026-001
    python3 scripts/audit_log.py --tail 20
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "audit" / "decision_log.csv"
FIELDS = ["timestamp", "date", "ref", "stage", "actor", "decision", "reason", "evidence"]

VALID_STAGES = ["ideation", "script", "music", "video_prompt", "generation",
                "review", "duplicate_check", "publish", "policy", "incident"]
VALID_DECISIONS = ["PASS", "FLAG", "BLOCK", "APPROVED", "REJECTED", "REVISED", "ESCALATED", "NOTE"]


def ensure_log():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        with LOG.open("w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=FIELDS).writeheader()


def log_decision(stage, decision, reason, actor="agent", ref="", evidence=""):
    """Append one decision. Returns the row written."""
    if stage not in VALID_STAGES:
        raise ValueError(f"unknown stage {stage!r}; expected one of {VALID_STAGES}")
    if decision not in VALID_DECISIONS:
        raise ValueError(f"unknown decision {decision!r}; expected one of {VALID_DECISIONS}")
    if not reason or not reason.strip():
        raise ValueError("a reason is required - an unexplained decision is not a logged decision")

    ensure_log()
    now = dt.datetime.now(dt.timezone.utc)
    row = {
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "ref": ref,
        "stage": stage,
        "actor": actor,
        "decision": decision,
        "reason": reason.replace("\n", " ").strip(),
        "evidence": evidence.replace("\n", " ").strip(),
    }
    with LOG.open("a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=FIELDS).writerow(row)
    return row


def log_result(stage, result, ref="", actor="agent"):
    """Log a compliance_gate.Result: one row per finding, or a PASS row if clean."""
    if not result.findings:
        return [log_decision(stage, "PASS", "No compliance findings.", actor=actor, ref=ref)]
    return [log_decision(stage, f.verdict, f"{f.rule_id}: {f.message}", actor=actor,
                         ref=ref, evidence=f.evidence) for f in result.findings]


def tail(n=20):
    if not LOG.exists():
        return []
    with LOG.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))[-n:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=VALID_STAGES)
    ap.add_argument("--decision", choices=VALID_DECISIONS)
    ap.add_argument("--reason")
    ap.add_argument("--actor", default="human")
    ap.add_argument("--ref", default="")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--tail", type=int, metavar="N", help="show the last N entries")
    args = ap.parse_args()

    if args.tail:
        rows = tail(args.tail)
        if not rows:
            print("Decision log is empty.")
            return 0
        for r in rows:
            print(f"{r['date']}  {r['ref'] or '-':<14} {r['stage']:<15} {r['decision']:<9} "
                  f"{r['actor']:<14} {r['reason']}")
        return 0

    if not (args.stage and args.decision and args.reason):
        ap.error("--stage, --decision and --reason are required (or use --tail N)")
    row = log_decision(args.stage, args.decision, args.reason,
                       actor=args.actor, ref=args.ref, evidence=args.evidence)
    print(f"logged: {row['timestamp']}  {row['stage']}  {row['decision']}  {row['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

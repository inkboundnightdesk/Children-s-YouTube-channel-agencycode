#!/usr/bin/env python3
"""
Today's two ship waves — timestamps for YouTube Studio Scheduled.

Does NOT upload. Does NOT call the YouTube API. Prints the clock and the
Studio fields for slots that already have a human sign-off.

    python3 scripts/today_ship.py
    python3 scripts/today_ship.py --date 2026-09-28
    python3 scripts/today_ship.py --all-pending   # show even unsigned slots (still not approved)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from compliance_gate import load_rules

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:
    ET = None


def et_label(utc_hhmm: str, day: dt.date) -> str:
    h, m = map(int, utc_hhmm.split(":"))
    utc = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=dt.timezone.utc)
    if ET is None:
        return utc.strftime("%Y-%m-%d %H:%M UTC")
    local = utc.astimezone(ET)
    return local.strftime("%Y-%m-%d %I:%M %p %Z")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--all-pending", action="store_true")
    args = ap.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    rules = load_rules()
    cad = rules["cadence"]
    times = cad["publish_times_utc"]
    formats = cad["slot_formats"]
    waves = cad.get("wave_names") or ["wave1", "wave2"]

    print(f"SHIP BOARD  {day.isoformat()}  timezone={cad.get('timezone', 'UTC')}")
    print("Visibility in Studio: Scheduled. Made for Kids: Yes. You click upload.")
    print("No YouTube API. Unsigned slots do not ship.\n")

    for i, (hhmm, fmt) in enumerate(zip(times, formats)):
        wave = waves[0] if i < 2 else waves[-1]
        ref_long = f"{'VID' if fmt != 'short' else 'SHT'}-{day.strftime('%Y%m%d')}-{i+1}"
        signoff = ROOT / "build" / ref_long / "signoff.json"
        packaged = ROOT / "build" / ref_long / "publish_package.json"
        if packaged.exists():
            state = "PACKAGED — schedule in Studio"
        elif signoff.exists():
            state = "SIGNED — run --package, then schedule in Studio"
        else:
            state = "NOT SIGNED — do not schedule"
        if not args.all_pending and not signoff.exists() and not packaged.exists():
            print(f"  {wave:<8}  {fmt:<5}  {hhmm} UTC  |  {et_label(hhmm, day)}")
            print(f"            {ref_long}  {state}")
            print(f"            {('python3 scripts/pipeline.py --ref ' + ref_long + ' --rhyme <id> --format ' + fmt)}")
            print()
            continue
        print(f"  {wave:<8}  {fmt:<5}  {hhmm} UTC  |  {et_label(hhmm, day)}")
        print(f"            {ref_long}  {state}")
        print(f"            Studio schedule: {day.isoformat()} {hhmm} UTC")
        print()

    print("Studio steps for a PACKAGED slot:")
    print("  1. Upload the file from build/<REF>/")
    print("  2. Audience: Yes, it's made for kids. Confirm on the review screen.")
    print("  3. Visibility: Scheduled. Enter the UTC time above (Studio shows your local clock).")
    print("  4. After it goes live: comments off, notifications off, flag actually stuck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

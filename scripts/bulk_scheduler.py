#!/usr/bin/env python3
"""
Bulk scheduler. Stacks a production calendar of 2 long videos + 2 Shorts per day, indefinitely.

What it DOES:
  - lays out 4 slots a day at the configured publish times
  - assigns a title and a distinct treatment to every slot, enforcing the title cooldown
  - rotates setting, palette and companion so no two nearby slots look alike
  - writes a schedule CSV you can work from, plus a per-slot brief
  - computes the human review load the plan implies, and says so plainly

What it does NOT do, ever:
  - approve anything
  - mark anything ready to publish
  - front-run the review gate

Every slot lands as PENDING. It becomes publishable only after running through the pipeline and a
named human passing review/safety_checklist.md. The calendar is a plan, not a queue of approvals.

    python3 scripts/bulk_scheduler.py --days 30
    python3 scripts/bulk_scheduler.py --days 90 --start 2026-09-04 --out build/q4-calendar.json
    python3 scripts/bulk_scheduler.py --capacity          # what can this library actually sustain?
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "review"))

import audit_log
from compliance_gate import ComplianceError, load_rules, preflight
from rhyme_generator import COMPANIONS, PALETTES, SETTINGS, load_library, short_shape


def lru_pick(pool, seen, k):
    """Least-recently-used option, so each dimension gets the widest possible spacing."""
    choice = min(pool, key=lambda x: seen.get(x, -10**9))
    seen[choice] = k
    return choice


def validate(slots, window_days=30):
    """Score the calendar against its own duplicate gate before anyone works from it.

    A calendar that fails at the gate is worse than no calendar: the work is done before the
    refusal arrives. So the scheduler checks its own output the way the pipeline will.
    """
    import itertools
    sys.path.insert(0, str(ROOT / "review"))
    from duplicate_detection import compare

    items = [dict(s, scenes=[{"kind": k} for k in s["planned_scenes"]],
                  runtime_s=s["planned_runtime_s"],
                  _d=dt.date.fromisoformat(s["publish_date"])) for s in slots]

    th = load_rules()["thresholds"]
    block_at = th["duplicate_similarity_block"]
    flag_at = th["duplicate_similarity_flag"]
    blocks, flags, worst = [], 0, (0.0, None, None)
    for a, b in itertools.combinations(items, 2):
        gap = abs((a["_d"] - b["_d"]).days)
        if gap > window_days:
            continue
        _, score = compare(a, b)
        if score > worst[0]:
            worst = (score, a["ref"], b["ref"])
        if score >= block_at:
            blocks.append({"a": a["ref"], "b": b["ref"], "days_apart": gap,
                           "score": round(score, 3)})
        elif score >= flag_at:
            flags += 1
    return {"window_days": window_days, "thresholds": {"flag": flag_at, "block": block_at},
            "would_block": len(blocks), "would_flag": flags,
            "worst_score": round(worst[0], 3), "worst_pair": [worst[1], worst[2]],
            "examples": blocks[:5]}


def usable(lib, fmt):
    return [r for r in lib["rhymes"] if r["pd_verified"] and fmt in r.get("formats", [])]


def capacity_report(rules, lib):
    """Can the library actually sustain the cadence under the cooldown? Arithmetic, not opinion."""
    th = rules["thresholds"]
    cooldown = th["title_cooldown_days"]
    per_day = {"long": th["daily_long_videos"], "short": th["daily_shorts"]}
    out = {"cooldown_days": cooldown, "formats": {}, "sustainable": True, "warnings": []}

    for fmt, n_day in per_day.items():
        pool = len(usable(lib, fmt))
        need = n_day * cooldown          # distinct titles required to never breach the cooldown
        headroom = pool - need
        ok = pool >= need
        out["formats"][fmt] = {
            "pool": pool, "per_day": n_day, "required_titles": need,
            "headroom": headroom, "sustainable": ok,
            "max_per_day_at_this_pool": round(pool / cooldown, 2),
        }
        if not ok:
            out["sustainable"] = False
            out["warnings"].append(
                f"{fmt}: {pool} titles cannot sustain {n_day}/day on a {cooldown}-day cooldown "
                f"(needs {need}). Max sustainable is {pool/cooldown:.1f}/day. "
                f"Verify {need - pool} more titles, or widen content types.")
        elif headroom <= 6:
            out["warnings"].append(
                f"{fmt}: only {headroom} titles of headroom. One flagged clearance and the "
                f"schedule breaks. Keep verifying new titles.")
    return out


def review_load(rules, days):
    th = rules["thresholds"]
    per_day_min = (th["daily_long_videos"] * th["review_minutes_per_long"]
                   + th["daily_shorts"] * th["review_minutes_per_short"])
    weekly_h = per_day_min * 7 / 60
    avail = th.get("reviewer_hours_available_per_week", 0)
    return {
        "minutes_per_day": per_day_min,
        "hours_per_day": round(per_day_min / 60, 2),
        "hours_per_week": round(weekly_h, 1),
        "hours_for_this_plan": round(per_day_min * days / 60, 1),
        "reviewer_hours_available_per_week": avail,
        "shortfall_hours_per_week": round(max(0.0, weekly_h - avail), 1),
        "reviewers_needed": max(1, -(-round(weekly_h) // max(1, avail))) if avail else None,
    }


def plan(days, start, seed):
    rules = load_rules()
    th = rules["thresholds"]
    cad = rules["cadence"]
    lib = load_library()
    rnd = random.Random(seed)

    cap = capacity_report(rules, lib)
    pools = {f: usable(lib, f) for f in ("long", "short")}
    for f in pools:
        rnd.shuffle(pools[f])

    cooldown = th["title_cooldown_days"]
    last_used = {}          # (rhyme_id, fmt) -> date last scheduled
    cursors = {"long": 0, "short": 0}
    seen = {"setting": {}, "palette": {}, "companion": {}}
    slots, skipped = [], []

    times = cad["publish_times_utc"]
    formats = cad["slot_formats"]

    for day_i in range(days):
        day = start + dt.timedelta(days=day_i)
        for slot_i, (hhmm, fmt) in enumerate(zip(times, formats)):
            pool = pools[fmt]
            chosen = None
            # walk the pool for the first title outside its cooldown
            for _ in range(len(pool)):
                cand = pool[cursors[fmt] % len(pool)]
                cursors[fmt] += 1
                prev = last_used.get((cand["id"], fmt))
                if prev is None or (day - prev).days >= cooldown:
                    chosen = cand
                    break
            if chosen is None:
                skipped.append({"date": day.isoformat(), "slot": slot_i + 1, "format": fmt,
                                "reason": f"every {fmt} title is inside its {cooldown}-day cooldown"})
                continue
            last_used[(chosen["id"], fmt)] = day

            # Treatment is assigned least-recently-used per dimension, not by modular
            # stepping. Fixed steps made the three dimensions cycle in lockstep, so the whole
            # triple recurred on a short period and unrelated rhymes landed in identical
            # worlds - a reskin, which is precisely what NN-3 blocks. LRU maximises the gap on
            # each dimension, and the pool sizes (24/17/19) are pairwise coprime so the triple
            # cannot realign for 7,752 slots (~5.3 years).
            k = len(slots)
            setting = lru_pick(SETTINGS, seen["setting"], k)
            palette = lru_pick(PALETTES, seen["palette"], k)
            companion = lru_pick(COMPANIONS, seen["companion"], k)

            # Plan the shape here so the calendar is authoritative and self-validation is exact.
            shape_seed = (k * 37 + chosen["verses"] * 11) % 97
            if fmt == "short":
                kinds, durs = short_shape(chosen["verses"], shape_seed)
            else:
                extra = 1 if shape_seed % 3 == 0 else 0          # some get a story beat
                kinds = (["open"] + ["verse"] * chosen["verses"]
                         + (["story"] if extra else []) + ["learn", "reprise", "close"])
                base = 10 + chosen["verses"] * 22 + 18 + 22 + 8
                durs = [base + (45 if extra else 0) + (shape_seed % 11) - 5]
            runtime = sum(durs) if fmt == "short" else durs[0]

            ref = f"{'VID' if fmt != 'short' else 'SHT'}-{day.strftime('%Y%m%d')}-{slot_i+1}"
            slots.append({
                "ref": ref,
                "publish_date": day.isoformat(),
                "publish_time_utc": hhmm,
                "publish_at_utc": f"{day.isoformat()}T{hhmm}:00Z",
                "slot": slot_i + 1,
                "format": fmt,
                "rhyme_id": chosen["id"],
                "rhyme_title": chosen["title"],
                "content_type": chosen["content_type"],
                "learning_hook": chosen["learning_hook"],
                "setting": setting,
                "palette": palette,
                "companion": companion,
                "visual_style": "cartoon",
                "planned_scenes": kinds,
                "planned_runtime_s": runtime,
                "status": "PENDING",
                "review_state": "NOT_STARTED",
                "approved_by": "",
                "pipeline_cmd": (f"python3 scripts/pipeline.py --ref {ref} "
                                 f"--rhyme {chosen['id']} --format {fmt}"),
            })

    validation = validate(slots)

    return {
        "validation": validation,
        "generated_on": dt.date.today().isoformat(),
        "start": start.isoformat(),
        "days": days,
        "end": (start + dt.timedelta(days=days - 1)).isoformat(),
        "cadence": cad,
        "seed": seed,
        "capacity": cap,
        "review_load": review_load(rules, days),
        "slots": slots,
        "skipped": skipped,
        "status": "PLAN_ONLY",
        "_warning": "Every slot is PENDING. Nothing here is approved and nothing may be uploaded "
                    "from this file. Each slot runs the full pipeline and its own human review gate.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--start", default="", help="YYYY-MM-DD, defaults to today")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="")
    ap.add_argument("--capacity", action="store_true", help="report sustainable cadence and exit")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    rules, lib = load_rules(), load_library()

    if args.capacity:
        cap = capacity_report(rules, lib)
        rl = review_load(rules, 7)
        print("CONTENT CAPACITY\n" + "-" * 74)
        for fmt, c in cap["formats"].items():
            mark = "OK " if c["sustainable"] else "NO "
            print(f"  {mark} {fmt:<6} pool={c['pool']:<4} need={c['required_titles']:<4} "
                  f"headroom={c['headroom']:<4} max sustainable={c['max_per_day_at_this_pool']}/day")
        for w in cap["warnings"]:
            print(f"  ! {w}")
        print(f"\nHUMAN REVIEW LOAD (NN-4 = 100% of frames)\n" + "-" * 74)
        print(f"  {rl['hours_per_day']} h/day = {rl['hours_per_week']} h/week")
        print(f"  reviewer hours available : {rl['reviewer_hours_available_per_week']} h/week")
        if rl["shortfall_hours_per_week"] > 0:
            print(f"  SHORTFALL: {rl['shortfall_hours_per_week']} h/week. "
                  f"~{rl['reviewers_needed']} reviewer(s) needed at the configured availability.")
        else:
            print("  within configured reviewer availability")
        return 0 if cap["sustainable"] else 1

    start = dt.date.fromisoformat(args.start) if args.start else dt.date.today()
    batch = plan(args.days, start, args.seed)

    out = pathlib.Path(args.out) if args.out else ROOT / "build" / f"calendar-{batch['start']}-{batch['days']}d.json"
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")

    csv_path = out.with_suffix(".csv")
    cols = ["publish_date", "publish_time_utc", "ref", "format", "rhyme_title", "content_type",
            "setting", "palette", "companion", "status", "review_state", "approved_by", "pipeline_cmd"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(batch["slots"])

    cap, rl = batch["capacity"], batch["review_load"]
    print(f"Calendar: {batch['start']} -> {batch['end']}  ({batch['days']} days)")
    print(f"  slots scheduled : {len(batch['slots'])}"
          f"  ({sum(1 for s in batch['slots'] if s['format']=='long')} long, "
          f"{sum(1 for s in batch['slots'] if s['format']=='short')} shorts)")
    if batch["skipped"]:
        print(f"  slots UNFILLED  : {len(batch['skipped'])}  (cooldown exhausted the pool)")
    print(f"  distinct titles : {len({s['rhyme_id'] for s in batch['slots']})}")

    print(f"\nCAPACITY")
    for fmt, c in cap["formats"].items():
        print(f"  {fmt:<6} pool={c['pool']:<4} needed={c['required_titles']:<4} headroom={c['headroom']}")
    for w in cap["warnings"]:
        print(f"  ! {w}")

    v = batch["validation"]
    print(f"\nSELF-VALIDATION  (every pair within {v['window_days']} days, scored by the real gate; "
          f"flag>={v['thresholds']['flag']} block>={v['thresholds']['block']})")
    print(f"  would BLOCK : {v['would_block']}")
    print(f"  would FLAG  : {v['would_flag']}")
    print(f"  worst pair  : {v['worst_score']}  {' vs '.join(x for x in v['worst_pair'] if x)}")
    if v["would_block"]:
        print("  ! This calendar contains slots the duplicate gate will refuse. Fix before working it.")
        for e in v["examples"]:
            print(f"      {e['score']}  {e['a']} vs {e['b']}  ({e['days_apart']}d apart)")

    print(f"\nHUMAN REVIEW LOAD - this is the real constraint")
    print(f"  {rl['hours_per_day']} h/day  =  {rl['hours_per_week']} h/week"
          f"  =  {rl['hours_for_this_plan']} h for this {batch['days']}-day plan")
    if rl["shortfall_hours_per_week"] > 0:
        print(f"  SHORTFALL {rl['shortfall_hours_per_week']} h/week against "
              f"{rl['reviewer_hours_available_per_week']} h available "
              f"-> ~{rl['reviewers_needed']} reviewer(s) needed.")

    print(f"\nWritten:\n  {out.relative_to(ROOT)}\n  {csv_path.relative_to(ROOT)}")
    print(f"\nEvery slot is PENDING. Nothing here is approved. Run each through:")
    print(f"  {batch['slots'][0]['pipeline_cmd'] if batch['slots'] else 'python3 scripts/pipeline.py ...'}")

    audit_log.log_decision("ideation", "PASS" if cap["sustainable"] else "FLAG",
                           f"Bulk calendar {batch['start']}..{batch['end']}: {len(batch['slots'])} slots, "
                           f"{len(batch['skipped'])} unfilled; review load {rl['hours_per_week']} h/week.",
                           actor="bulk_scheduler", evidence=str(out.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

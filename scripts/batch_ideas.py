#!/usr/bin/env python3
"""
Batch idea planning - with the anti-mass-production rule (NN-3) applied at the planning stage, where it is
cheap, instead of at the review gate, where it is expensive.

The failure mode this exists to prevent: sit down, generate thirty ideas, notice on video nineteen that
they are all the same video. So the planner refuses to emit two ideas that share a rhyme, refuses to reuse
a setting or companion already in the batch, checks each idea against everything already published, and
caps the batch at what the weekly schedule can actually absorb.

A batch is a PLAN, not an approval. Every idea still goes through the full pipeline individually.

    python3 scripts/batch_ideas.py --count 4
    python3 scripts/batch_ideas.py --count 4 --weeks 2 --out build/batch-2026-09.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_log
from compliance_gate import ComplianceError, load_rules, preflight, scan_text
from rhyme_generator import COMPANIONS, PALETTES, SETTINGS, load_library

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "review"))
from duplicate_detection import check as dup_check

ROOT = pathlib.Path(__file__).resolve().parent.parent


def plan(count, weeks, seed):
    rules = load_rules()
    th = rules["thresholds"]
    cap = th["max_videos_per_week"] * weeks
    if count > cap:
        raise SystemExit(
            f"Refusing to plan {count} videos for {weeks} week(s).\n"
            f"The cap is {th['max_videos_per_week']}/week = {cap}. Volume is the mass-production signal "
            f"(NN-3).\nPlan more weeks, or plan fewer videos.")

    lib = load_library()
    usable = [r for r in lib["rhymes"] if r["pd_verified"]]
    if count > len(usable):
        raise SystemExit(
            f"Refusing: {count} ideas requested but only {len(usable)} verified public-domain rhymes are "
            f"available.\nTwo videos of the same rhyme in one batch is exactly the pattern NN-3 forbids.\n"
            f"Verify more rhymes into scripts/rhyme_library.json first - properly, with a citable source.")

    rnd = random.Random(seed)
    rhymes = rnd.sample(usable, count)
    settings = rnd.sample(SETTINGS, count)
    palettes = rnd.sample(PALETTES, min(count, len(PALETTES)))
    companions = rnd.sample(COMPANIONS, min(count, len(COMPANIONS)))

    start = dt.date.today()
    gap_days = max(2, round(th["min_hours_between_uploads"] / 24) + 1)

    ideas = []
    for i, r in enumerate(rhymes):
        release = start + dt.timedelta(days=gap_days * (i + 1))
        idea = {
            "slot": i + 1,
            "ref": f"VID-{release.year}-{release.strftime('%m%d')}-{r['id'][:6]}",
            "rhyme_id": r["id"],
            "rhyme_title": r["title"],
            "pd_basis": r["pd_basis"],
            "setting": settings[i],
            "palette": palettes[i % len(palettes)],
            "companion": companions[i % len(companions)],
            "visual_style": "cartoon",
            "mood": r["mood"],
            "learning_hook": r["learning_hook"],
            "target_release": release.isoformat(),
            "runtime_estimate_s": 60 + (r["verses"] * 22),
            "scenes": [{"kind": "open"}] + [{"kind": "verse"}] * r["verses"] +
                      [{"kind": "learn"}, {"kind": "reprise"}, {"kind": "close"}],
        }
        idea["runtime_s"] = idea["runtime_estimate_s"]
        dup = dup_check(idea)
        idea["duplicate_check"] = {"verdict": dup["verdict"], "max_similarity": dup["max_similarity"]}
        copy_res = scan_text(r["title"], context=f"idea{i+1}.title")
        idea["copy_scan"] = copy_res.verdict
        ideas.append(idea)

    # Intra-batch collision check: the planner must not hand you two versions of the same video.
    collisions = []
    for a in range(len(ideas)):
        for b in range(a + 1, len(ideas)):
            for key in ("rhyme_id", "setting", "companion"):
                if ideas[a][key] == ideas[b][key]:
                    collisions.append(f"slots {a+1} and {b+1} share {key}: {ideas[a][key]!r}")

    return {
        "generated_on": start.isoformat(),
        "weeks": weeks,
        "count": count,
        "weekly_cap": th["max_videos_per_week"],
        "min_gap_days": gap_days,
        "seed": seed,
        "ideas": ideas,
        "intra_batch_collisions": collisions,
        "status": "PLAN_ONLY",
        "_note": "A plan is not an approval. Each idea runs the full pipeline and its own human review gate.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--weeks", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    seed = args.seed if args.seed is not None else random.randrange(100000)
    batch = plan(args.count, args.weeks, seed)

    print(f"Batch plan - {batch['count']} idea(s) across {batch['weeks']} week(s) "
          f"(cap {batch['weekly_cap']}/week, min {batch['min_gap_days']} days apart)\n")
    for idea in batch["ideas"]:
        dc = idea["duplicate_check"]
        mark = {"PASS": "ok", "FLAG": "FLAG", "BLOCK": "BLOCK"}[dc["verdict"]]
        print(f"  {idea['slot']}. {idea['rhyme_title']}")
        print(f"     ref      : {idea['ref']}   release {idea['target_release']}")
        print(f"     setting  : {idea['setting']}")
        print(f"     look     : {idea['palette']}  |  {idea['companion']}")
        print(f"     teaches  : {idea['learning_hook']}")
        print(f"     dup check: {mark} (similarity {dc['max_similarity']:.3f})")
        print()

    if batch["intra_batch_collisions"]:
        print("INTRA-BATCH COLLISIONS - fix before proceeding:")
        for c in batch["intra_batch_collisions"]:
            print(f"  - {c}")
        print()

    blocked = [i for i in batch["ideas"] if i["duplicate_check"]["verdict"] == "BLOCK"]
    if blocked:
        print(f"{len(blocked)} idea(s) BLOCKED as too close to published work. "
              f"Replace them before building anything.\n")

    out = pathlib.Path(args.out) if args.out else ROOT / "build" / f"batch-{batch['generated_on']}.json"
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    print(f"Plan written: {out.relative_to(ROOT)}")

    audit_log.log_decision("ideation", "FLAG" if (blocked or batch["intra_batch_collisions"]) else "PASS",
                           f"Planned {batch['count']} idea(s) over {batch['weeks']} week(s); "
                           f"{len(blocked)} blocked, {len(batch['intra_batch_collisions'])} collisions.",
                           actor="batch_ideas", evidence=str(out.relative_to(ROOT)))
    print("\nA plan is not an approval. Each idea runs the full pipeline and its own human review gate.")
    return 2 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())

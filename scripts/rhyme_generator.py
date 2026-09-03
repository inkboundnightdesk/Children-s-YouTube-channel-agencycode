#!/usr/bin/env python3
"""
Generate a full video script from a verified public-domain rhyme.

Every script is built from scripts/rhyme_library.json and nothing else. A rhyme without pd_verified=true
is refused outright - "it feels traditional" is not a clearance (see compliance/music-licensing-basics.md).

The output is run through the compliance gate before it is written, and the decision is logged. That is
operating rule #3: "When generating a script or video prompt, run it through the /review/ checklist first."

    python3 scripts/rhyme_generator.py --list
    python3 scripts/rhyme_generator.py --rhyme twinkle --ref VID-2026-001
    python3 scripts/rhyme_generator.py --rhyme twinkle --setting "a quiet hilltop meadow" --out build/
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_log
from compliance_gate import BLOCK, ComplianceError, preflight, scan_text

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "scripts" / "rhyme_library.json"

# Settings are varied deliberately: the anti-duplication rule (NN-3) is satisfied by real difference in
# the work, not by a reshuffled title.
SETTINGS = [
    "a quiet hilltop meadow under a wide evening sky",
    "a cosy wooden treehouse with round windows",
    "a small harbour where painted boats bob at their moorings",
    "a sunlit kitchen garden with tall sunflowers",
    "a snowy village square with warm lantern light",
    "a riverbank where willows dip into slow water",
    "a friendly red barn at the edge of a green field",
    "a bright attic room full of soft toys and books",
]
PALETTES = [
    "deep indigo, soft gold, cream",
    "sage green, warm terracotta, oat",
    "dusty blue, buttermilk, pale coral",
    "plum, mustard, soft grey",
    "forest green, cream, honey",
    "lavender, mint, warm white",
]
COMPANIONS = [
    "a small round owl with speckled feathers",
    "a patient grey donkey with long ears",
    "a curious hedgehog in a knitted scarf",
    "a slow, cheerful tortoise",
    "a fluffy duckling who hums along",
    "a gentle brown bear cub",
]


def load_library():
    return json.loads(LIBRARY.read_text(encoding="utf-8"))


def find_rhyme(lib, rid):
    for r in lib["rhymes"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"No rhyme with id {rid!r}. Run --list to see what is available.")


def build_script(rhyme, setting, palette, companion, seed):
    """Build the script structure. Deliberately contains NO call to action of any kind."""
    rnd = random.Random(seed)
    title_word = rhyme["title"]

    scenes = []
    scenes.append({
        "n": 1, "kind": "open", "duration_s": 10,
        "visual": f"Slow establishing view of {setting}. {companion.capitalize()} enters from the left and settles.",
        "narration": f"Here we are, in {setting.split(' with ')[0].split(' where ')[0]}.",
        "on_screen_text": title_word,
    })
    for v in range(1, rhyme["verses"] + 1):
        scenes.append({
            "n": len(scenes) + 1, "kind": "verse", "duration_s": 22,
            "visual": f"Verse {v}: the action of the rhyme plays out gently in {setting.split(' with ')[0]}. "
                      f"{companion.capitalize()} joins in the motion. Camera moves slowly, no fast cuts.",
            "narration": f"[SUNG] Verse {v} of {title_word}.",
            "on_screen_text": f"Verse {v}",
        })
    scenes.append({
        "n": len(scenes) + 1, "kind": "learn", "duration_s": 18,
        "visual": f"A calm, uncluttered frame. The learning idea is shown plainly, one thing at a time.",
        "narration": f"Let's look again at {rhyme['learning_hook']}.",
        "on_screen_text": rhyme["learning_hook"].split(",")[0].strip().title(),
    })
    scenes.append({
        "n": len(scenes) + 1, "kind": "reprise", "duration_s": 22,
        "visual": "The full scene once more, a little softer and slower than before.",
        "narration": "[SUNG] Final time through, slower.",
        "on_screen_text": "",
    })
    scenes.append({
        "n": len(scenes) + 1, "kind": "close", "duration_s": 8,
        "visual": f"{companion.capitalize()} settles down to rest. Light dims gently. Hold, then fade.",
        "narration": "Goodnight." if rhyme["mood"] == "calm" else "See you next time.",
        "on_screen_text": "",
    })

    return {
        "rhyme_id": rhyme["id"],
        "rhyme_title": rhyme["title"],
        "pd_basis": rhyme["pd_basis"],
        "pd_source": rhyme["source"],
        "setting": setting,
        "palette": palette,
        "companion": companion,
        "mood": rhyme["mood"],
        "tempo": rhyme["tempo"],
        "learning_hook": rhyme["learning_hook"],
        "visual_style": "cartoon",
        "seed": seed,
        "runtime_s": sum(s["duration_s"] for s in scenes),
        "scenes": scenes,
        "no_call_to_action": True,
        "_note": "Made-for-Kids disables comments, notifications and playlists, and asking children for "
                 "engagement is inappropriate regardless. No CTA is generated, by design.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list rhymes and their clearance status")
    ap.add_argument("--rhyme", help="rhyme id from the library")
    ap.add_argument("--setting"); ap.add_argument("--palette"); ap.add_argument("--companion")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--ref", default="", help="project reference for the audit log, e.g. VID-2026-001")
    ap.add_argument("--out", default="build", help="output directory")
    args = ap.parse_args()

    lib = load_library()

    if args.list:
        print(f"{'id':<18}{'PD?':<6}{'verses':<8}{'mood':<10}title")
        print("-" * 78)
        for r in lib["rhymes"]:
            mark = "yes" if r["pd_verified"] else "NO"
            print(f"{r['id']:<18}{mark:<6}{r['verses']:<8}{r['mood']:<10}{r['title']}")
        print("\nOnly rhymes marked 'yes' may be used. See compliance/music-licensing-basics.md.")
        return 0

    if not args.rhyme:
        ap.error("--rhyme is required (or use --list)")

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    rhyme = find_rhyme(lib, args.rhyme)

    # NN-5: refuse anything not verified public domain.
    if not rhyme["pd_verified"]:
        reason = (f"Refused rhyme {rhyme['id']!r}: pd_verified is false. {rhyme['pd_basis']}")
        audit_log.log_decision("script", "BLOCK", reason, actor="rhyme_generator", ref=args.ref)
        print(f"BLOCKED - NN-5 (music/composition clearance)\n\n"
              f"  Rhyme  : {rhyme['title']}\n  Basis  : {rhyme['pd_basis']}\n  Note   : {rhyme['notes']}\n\n"
              f"This is not a bug. The rhyme is not verified public domain, so the agency will not build a "
              f"script from it.\nResolve the clearance with counsel and set pd_verified=true - or pick "
              f"another rhyme.", file=sys.stderr)
        return 2

    seed = args.seed if args.seed is not None else abs(hash(rhyme["id"] + (args.setting or ""))) % 100000
    rnd = random.Random(seed)
    setting = args.setting or rnd.choice(SETTINGS)
    palette = args.palette or rnd.choice(PALETTES)
    companion = args.companion or rnd.choice(COMPANIONS)

    script = build_script(rhyme, setting, palette, companion, seed)

    # Operating rule #3: gate it before it leaves the generator.
    result = scan_text(script["rhyme_title"], context="script.title")
    for sc in script["scenes"]:
        if sc["on_screen_text"]:
            result.merge(scan_text(sc["on_screen_text"], context=f"scene{sc['n']}.on_screen_text"))
        result.merge(scan_text(sc["narration"], context=f"scene{sc['n']}.narration"))

    audit_log.log_result("script", result, ref=args.ref, actor="rhyme_generator")
    script["compliance"] = result.as_dict()

    if result.verdict == BLOCK:
        print("BLOCKED - the generated script failed the compliance gate:\n", file=sys.stderr)
        print(result.report(), file=sys.stderr)
        return 2

    outdir = ROOT / args.out / (args.ref or rhyme["id"])
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "script.json"
    path.write_text(json.dumps(script, indent=2) + "\n", encoding="utf-8")

    audit_log.log_decision("script", "PASS",
                           f"Generated script for '{rhyme['title']}' (seed {seed}, setting: {setting}).",
                           actor="rhyme_generator", ref=args.ref, evidence=str(path.relative_to(ROOT)))

    print(f"Script written: {path.relative_to(ROOT)}")
    print(f"  rhyme    : {rhyme['title']}")
    print(f"  PD basis : {rhyme['pd_basis'][:70]}...")
    print(f"  setting  : {setting}")
    print(f"  palette  : {palette}")
    print(f"  companion: {companion}")
    print(f"  runtime  : {script['runtime_s']}s across {len(script['scenes'])} scenes")
    print(f"  gate     : {result.verdict}")
    print("\nNext: python3 scripts/title_thumbnail_copy.py --script "
          f"{path.relative_to(ROOT)} --ref {args.ref or rhyme['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

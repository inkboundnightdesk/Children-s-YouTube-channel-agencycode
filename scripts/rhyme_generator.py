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
    "a windmill on a low hill with long grass",
    "a duck pond ringed with smooth grey stones",
    "an orchard of short apple trees in soft afternoon light",
    "a lighthouse keeper's cottage above a calm bay",
    "a market square with striped awnings, early morning",
    "a mossy woodland clearing with dappled sunlight",
    "a sandy cove with gentle waves and rock pools",
    "a greenhouse full of seedlings and watering cans",
    "a bakery window with warm light and round loaves",
    "a wildflower field with a low stone wall",
    "a train platform in a tiny country station",
    "a hillside sheep pasture under drifting clouds",
    "a cobbled lane with window boxes and a blue door",
    "a frozen pond with soft snow on the reeds",
    "a rope bridge over a shallow, sunny stream",
    "a hay loft with warm light through the slats",
]

PALETTES = [
    "deep indigo, soft gold, cream",
    "sage green, warm terracotta, oat",
    "dusty blue, buttermilk, pale coral",
    "plum, mustard, soft grey",
    "forest green, cream, honey",
    "lavender, mint, warm white",
    "soft teal, apricot, ivory",
    "clay pink, olive, sand",
    "midnight blue, silver, pale rose",
    "moss green, butter yellow, chalk",
    "russet, cream, slate blue",
    "periwinkle, peach, warm grey",
    "deep plum, sage, oatmeal",
    "denim blue, wheat, soft white",
    "pine green, copper, bone",
    "mauve, straw, dove grey",
    "seafoam, coral, linen",
]

COMPANIONS = [
    "a small round owl with speckled feathers",
    "a patient grey donkey with long ears",
    "a curious hedgehog in a knitted scarf",
    "a slow, cheerful tortoise",
    "a fluffy duckling who hums along",
    "a gentle brown bear cub",
    "a shy grey rabbit with one folded ear",
    "a tidy badger with round spectacles",
    "a sleepy orange cat with a bell",
    "a small red fox with a white-tipped tail",
    "a woolly lamb with a crooked fringe",
    "a bright green frog in wellington boots",
    "a plump robin with a red waistcoat",
    "a spotted puppy with oversized paws",
    "a quiet grey mouse with a patchwork bag",
    "a friendly goose in a straw hat",
    "a small striped bumblebee with tired wings",
    "a soft grey seal pup with wide eyes",
    "a small brown wren with a bright eye",
]


def recent_treatments(limit=40):
    """Setting/palette/companion used by the most recent published items.

    At 4 uploads a day, picking a treatment at random collides with something recent almost
    immediately - and a different rhyme in an identical world is a reskin, which is exactly what
    NN-3 blocks. So the generator avoids what is already on the shelf rather than discovering
    the collision at the duplicate gate.
    """
    idx = ROOT / "audit" / "published_index.json"
    if not idx.exists():
        return {"setting": set(), "palette": set(), "companion": set()}
    try:
        pub = json.loads(idx.read_text(encoding="utf-8")).get("published", [])
    except (ValueError, OSError):
        return {"setting": set(), "palette": set(), "companion": set()}
    pub = pub[-limit:]
    return {k: {p.get(k) for p in pub if p.get(k)} for k in ("setting", "palette", "companion")}


def pick(pool, used, rnd):
    """Prefer something not recently used; fall back to the full pool if all are taken."""
    fresh = [x for x in pool if x not in used]
    return rnd.choice(fresh if fresh else pool)


def load_library():
    return json.loads(LIBRARY.read_text(encoding="utf-8"))


def find_rhyme(lib, rid):
    for r in lib["rhymes"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"No rhyme with id {rid!r}. Run --list to see what is available.")


FORMATS = {
    "long":    {"aspect": "16:9", "target_s": (90, 150), "label": "long-form video"},
    "short":   {"aspect": "9:16", "target_s": (20, 55),  "label": "YouTube Short (vertical)"},
    "cartoon": {"aspect": "16:9", "target_s": (150, 300), "label": "story cartoon"},
}


def short_shape(verses, seed):
    """Scene kinds and durations for a Short, varied deterministically.

    Every Short having the same 3-scene / 28-second shape makes structure similarity 1.00 for
    every pair, which eats 30% of the duplicate score as a constant and leaves almost no room
    for legitimate variation in look. Varying it is both better craft and what keeps the
    duplicate gate usable at four uploads a day.
    """
    n_verse = 1 if verses <= 2 else 2
    hook_d = 4 + (seed % 3)          # 4-6s
    verse_d = 15 + (seed % 8)        # 15-22s
    close_d = 5 + ((seed // 3) % 4)  # 5-8s
    kinds = ["hook"] + ["verse"] * n_verse + ["loop_close"]
    durs = [hook_d] + [verse_d, max(12, verse_d - 4)][:n_verse] + [close_d]
    return kinds, durs


def build_short(rhyme, setting, palette, companion, seed):
    """A Short is not a trimmed long video. Vertical, one idea, no wind-up, loopable."""
    kinds, durs = short_shape(rhyme["verses"], seed)
    text = [rhyme["title"]] + [""] * (len(kinds) - 1)
    visual = {
        "hook": f"Vertical 9:16. Straight into the action in {setting.split(' with ')[0]}. "
                f"{companion.capitalize()} already mid-motion, centred in the upper two thirds.",
        "verse": "Vertical 9:16. One continuous action, subject centred and large. "
                 "Nothing in the lower fifth - the UI covers it.",
        "loop_close": "Vertical 9:16. Return to the exact opening framing so the loop is seamless.",
    }
    narr = {"hook": "[SUNG] Opening line, no wind-up.",
            "verse": "[SUNG] The strongest verse.",
            "loop_close": "[SUNG] Final phrase, landing on the opening beat."}
    return [{"n": i + 1, "kind": k, "duration_s": d, "visual": visual[k],
             "narration": narr[k], "on_screen_text": text[i]}
            for i, (k, d) in enumerate(zip(kinds, durs))]


def build_script(rhyme, setting, palette, companion, seed, fmt="long"):
    """Build the script structure. Deliberately contains NO call to action of any kind."""
    rnd = random.Random(seed)
    title_word = rhyme["title"]

    if fmt == "short":
        scenes = build_short(rhyme, setting, palette, companion, seed)
        return {
            "rhyme_id": rhyme["id"], "rhyme_title": rhyme["title"], "format": "short",
            "aspect": "9:16", "pd_basis": rhyme["pd_basis"], "pd_source": rhyme["source"],
            "setting": setting, "palette": palette, "companion": companion,
            "mood": rhyme["mood"], "tempo": rhyme["tempo"],
            "learning_hook": rhyme["learning_hook"], "visual_style": "cartoon", "seed": seed,
            "runtime_s": sum(s["duration_s"] for s in scenes), "scenes": scenes,
            "no_call_to_action": True,
            "_note": "Vertical Short. Keep the lower fifth of frame clear - YouTube's UI covers it. "
                     "Built to loop: the close returns to the opening framing.",
        }

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
    if fmt == "cartoon":
        scenes.append({
            "n": len(scenes) + 1, "kind": "story", "duration_s": 45,
            "visual": f"A short original story beat in {setting.split(' with ')[0]}: "
                      f"{companion} meets a small, gentle problem and solves it kindly. "
                      f"No peril, no antagonist, no distress.",
            "narration": "[SPOKEN] Original narration - not part of the rhyme.",
            "on_screen_text": "",
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
        "format": fmt,
        "aspect": FORMATS[fmt]["aspect"],
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
    ap.add_argument("--format", choices=["long", "short", "cartoon"], default="long",
                    help="long-form video, vertical Short, or story cartoon")
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
    used = recent_treatments()
    setting = args.setting or pick(SETTINGS, used["setting"], rnd)
    palette = args.palette or pick(PALETTES, used["palette"], rnd)
    companion = args.companion or pick(COMPANIONS, used["companion"], rnd)

    if args.format not in rhyme.get("formats", ["long", "short"]):
        print(f"BLOCKED - {rhyme['title']!r} is not approved for format {args.format!r} "
              f"(allowed: {rhyme.get('formats')}).\n"
              f"Lullabies in particular are long-form only: a 20-second lullaby is not a lullaby.",
              file=sys.stderr)
        audit_log.log_decision("script", "BLOCK",
                               f"Format {args.format!r} not allowed for {rhyme['id']!r}.",
                               actor="rhyme_generator", ref=args.ref)
        return 2

    script = build_script(rhyme, setting, palette, companion, seed, fmt=args.format)

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
    print(f"  format   : {script['format']} ({script['aspect']})")
    print(f"  runtime  : {script['runtime_s']}s across {len(script['scenes'])} scenes")
    print(f"  gate     : {result.verdict}")
    print("\nNext: python3 scripts/title_thumbnail_copy.py --script "
          f"{path.relative_to(ROOT)} --ref {args.ref or rhyme['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Title, description and thumbnail copy - written for a Made-for-Kids video, where none of the usual
growth levers exist.

There is no bell, no comment section, no end screen and no playlist to save to. So the title and the
thumbnail are doing effectively all of the discovery work, and they have to do it without a single
manipulative technique: no curiosity gaps, no all-caps, no "you won't believe", no engagement bait.
See compliance/youtube-made-for-kids-policy.md.

Every candidate is scanned by the compliance gate and anything that BLOCKs is dropped before you see it.

    python3 scripts/title_thumbnail_copy.py --script build/VID-2026-001/script.json --ref VID-2026-001
    python3 scripts/title_thumbnail_copy.py --check "Twinkle Twinkle - SUBSCRIBE NOW!"
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_log
from compliance_gate import BLOCK, FLAG, ComplianceError, preflight, scan_text

ROOT = pathlib.Path(__file__).resolve().parent.parent

TITLE_MAX = 100          # YouTube hard limit
TITLE_COMFORT = 60       # beyond this it truncates in most surfaces
THUMB_WORD_MAX = 4       # a preschooler is not reading a sentence off a thumbnail


def title_candidates(script):
    t = script["rhyme_title"]
    setting_short = script["setting"].split(" with ")[0].split(" where ")[0].replace("a ", "", 1)
    hook = script["learning_hook"].split(",")[0].strip()
    companion_short = script["companion"].split(" with ")[0].replace("a ", "", 1)
    mood_word = {"calm": "Gentle", "playful": "Playful", "cheerful": "Happy", "warm": "Cosy"}.get(
        script["mood"], "Gentle")
    return [
        f"{t} | {mood_word} Nursery Rhyme for Little Ones",
        f"{t} - A Song About {hook.title()}",
        f"{t} | Sing Along at {setting_short.title()}",
        f"{mood_word} {t} with {companion_short.title()}",
        f"{t} | Nursery Rhymes for Toddlers",
    ]


def thumbnail_candidates(script):
    t = script["rhyme_title"]
    first = t.split(",")[0].split(" ")[0]
    hook = script["learning_hook"].split(",")[0].strip().title()
    return [
        first.upper() if len(first) <= 8 else first.title(),
        " ".join(t.replace(",", "").split()[:3]).title(),
        hook if len(hook.split()) <= THUMB_WORD_MAX else hook.split()[0],
        "Sing Along",
    ]


def build_description(script):
    """Description with no CTA, no links, no contact route. Credits the PD source, which is both good
    practice and useful evidence if a Content ID claim ever lands."""
    return "\n".join([
        f"{script['rhyme_title']} - a gentle sing-along for little ones.",
        "",
        f"Join {script['companion']} in {script['setting']} for a calm version of this "
        f"classic nursery rhyme, with a look at {script['learning_hook']}.",
        "",
        f"Runtime: about {script['runtime_s'] // 60} minute(s).",
        "",
        "About this song:",
        f"  {script['rhyme_title']} is a traditional nursery rhyme in the public domain.",
        f"  {script['pd_basis']}",
        f"  Source: {script['pd_source']}",
        "  This arrangement and recording were created originally for this channel.",
        "",
        "This video is made for kids. Comments and notifications are turned off, and no personalised "
        "advertising is shown.",
    ])


def evaluate(text, context):
    res = scan_text(text, context=context)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--script", help="path to script.json from rhyme_generator.py")
    g.add_argument("--check", help="lint a single title or line of copy")
    ap.add_argument("--ref", default="")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    if args.check:
        res = evaluate(args.check, "input")
        print(res.report())
        if len(args.check) > TITLE_MAX:
            print(f"\n[BLOCK] LENGTH: {len(args.check)} chars exceeds YouTube's {TITLE_MAX}-char limit.")
            return 2
        return {"PASS": 0, "FLAG": 1, "BLOCK": 2}[res.verdict]

    script = json.loads((ROOT / args.script).read_text(encoding="utf-8")) \
        if not pathlib.Path(args.script).is_absolute() else \
        json.loads(pathlib.Path(args.script).read_text(encoding="utf-8"))

    accepted_titles, rejected = [], []
    for cand in title_candidates(script):
        res = evaluate(cand, "title")
        entry = {"text": cand, "chars": len(cand), "verdict": res.verdict,
                 "findings": [f.as_dict() for f in res.findings]}
        if res.verdict == BLOCK or len(cand) > TITLE_MAX:
            rejected.append(entry)
        else:
            entry["truncates_in_feed"] = len(cand) > TITLE_COMFORT
            accepted_titles.append(entry)

    accepted_thumbs = []
    for cand in thumbnail_candidates(script):
        res = evaluate(cand, "thumbnail_text")
        if res.verdict != BLOCK and len(cand.split()) <= THUMB_WORD_MAX:
            accepted_thumbs.append({"text": cand, "words": len(cand.split()), "verdict": res.verdict})

    description = build_description(script)
    desc_res = evaluate(description, "description")

    out = {
        "ref": args.ref,
        "rhyme_title": script["rhyme_title"],
        "titles": accepted_titles,
        "titles_rejected": rejected,
        "thumbnail_text": accepted_thumbs,
        "description": description,
        "description_verdict": desc_res.as_dict(),
        "_rules": {
            "no_call_to_action": True,
            "no_links": True,
            "no_contact_routes": True,
            "reason": "Made-for-Kids disables the features a CTA would point at, and engagement bait "
                      "aimed at children is a child-safety problem, not just a style problem.",
        },
    }

    dest = (ROOT / args.script).parent if not pathlib.Path(args.script).is_absolute() \
        else pathlib.Path(args.script).parent
    path = dest / "copy.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    audit_log.log_decision(
        "script", "PASS" if desc_res.verdict != BLOCK else "BLOCK",
        f"Generated {len(accepted_titles)} title candidates and description for "
        f"'{script['rhyme_title']}'; {len(rejected)} rejected by the gate.",
        actor="title_thumbnail_copy", ref=args.ref, evidence=str(path.relative_to(ROOT)))

    print(f"Copy written: {path.relative_to(ROOT)}\n")
    print("TITLE CANDIDATES (a human picks one):")
    for i, t in enumerate(accepted_titles, 1):
        warn = "  <- truncates in feed" if t.get("truncates_in_feed") else ""
        print(f"  {i}. [{t['verdict']}] ({t['chars']:>3} ch) {t['text']}{warn}")
    if rejected:
        print(f"\n  {len(rejected)} candidate(s) rejected by the gate.")
    print("\nTHUMBNAIL TEXT (short - they cannot read a sentence):")
    for t in accepted_thumbs:
        print(f"  - \"{t['text']}\" ({t['words']} word(s))")
    print(f"\nDESCRIPTION: {desc_res.verdict}")

    # A BLOCK has to stop the run. Logging a refusal and then returning success is worse than
    # having no gate: the pipeline proceeds and the audit trail claims it was checked.
    if desc_res.verdict == BLOCK:
        print("\nBLOCKED - the description failed the compliance gate:\n", file=sys.stderr)
        print(desc_res.report(), file=sys.stderr)
        return 2
    if not accepted_titles:
        print("\nBLOCKED - every title candidate was rejected by the gate.", file=sys.stderr)
        return 2

    print("\nNext: python3 scripts/pipeline.py --ref " + (args.ref or "<ref>") + " --stage video")
    return {"PASS": 0, "FLAG": 0, "BLOCK": 2}[desc_res.verdict]


if __name__ == "__main__":
    sys.exit(main())

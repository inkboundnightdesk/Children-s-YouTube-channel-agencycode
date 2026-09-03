#!/usr/bin/env python3
"""
Duplicate detection - the numeric half of NN-3, "no mass-production patterns".

Near-duplicate output at volume is the exact profile YouTube demotes, and it is the thing a nursery-rhyme
channel drifts into without noticing: same template, same palette, swap the animal, ship it. This compares
a candidate against everything already published and refuses anything too close.

It scores four dimensions and takes the worst, because a video can be a duplicate along any one of them:

    title       character 4-gram Jaccard  - catches "Twinkle Star Song 1 / 2 / 3"
    rhyme       same source rhyme?        - the strongest single signal
    structure   scene shape + runtime     - catches the template farm
    look        setting/palette/companion - catches the reskin

Thresholds live in compliance/rules.json:  >= 0.55 BLOCK,  >= 0.40 FLAG.

    python3 review/duplicate_detection.py --package build/VID-2026-001/script.json
    python3 review/duplicate_detection.py --package build/VID-2026-001/script.json --write
    python3 review/duplicate_detection.py --index
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import audit_log
from compliance_gate import load_rules

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "audit" / "published_index.json"


def shingles(text, n=4):
    t = "".join(ch.lower() if ch.isalnum() else " " for ch in str(text))
    t = " ".join(t.split())
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))} or {t}


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_index():
    if not INDEX.exists():
        return {"published": []}
    return json.loads(INDEX.read_text(encoding="utf-8"))


def structure_signature(item):
    kinds = [s.get("kind", "?") for s in item.get("scenes", [])]
    return {"kinds": kinds, "n": len(kinds), "runtime": item.get("runtime_s", 0)}


def days_between(a, b):
    """Whole days between two ISO dates; None if either is missing/unparseable."""
    try:
        return abs((dt.date.fromisoformat(str(a)) - dt.date.fromisoformat(str(b))).days)
    except (ValueError, TypeError):
        return None


def compare(candidate, prior):
    """Per-dimension similarity between a candidate and one published item.

    The scoring question is NOT "is this the same rhyme?" - at 4 uploads a day, revisiting a
    rhyme is inevitable and legitimate; that is what the cooldown window governs. The question
    is "is this the same VIDEO?" So when the source rhyme matches, the title dimension is pure
    redundancy and is excluded from the score: what must differ is the treatment - structure
    and look. Title only scores across DIFFERENT rhymes, where it catches serial near-titles
    ("Star Song 1 / 2 / 3").
    """
    scores = {}
    same_rhyme = bool(candidate.get("rhyme_id")) and candidate.get("rhyme_id") == prior.get("rhyme_id")
    same_format = candidate.get("format", "long") == prior.get("format", "long")

    scores["title"] = jaccard(shingles(candidate.get("rhyme_title", "")),
                              shingles(prior.get("rhyme_title", "")))
    scores["rhyme"] = 1.0 if same_rhyme else 0.0

    cs, ps = structure_signature(candidate), structure_signature(prior)
    if cs["kinds"] and ps["kinds"]:
        same = sum(1 for a, b in zip(cs["kinds"], ps["kinds"]) if a == b)
        shape = same / max(len(cs["kinds"]), len(ps["kinds"]))
        longest = max(cs["runtime"], ps["runtime"]) or 1
        runtime_sim = 1 - abs(cs["runtime"] - ps["runtime"]) / longest
        scores["structure"] = round((shape * 0.7) + (runtime_sim * 0.3), 4)
    else:
        scores["structure"] = 0.0

    # visual_style is deliberately excluded: it is "cartoon" for every video on the channel,
    # so including it only adds a constant 0.25 floor to every comparison and drags unrelated
    # videos over the flag line. A dimension that never varies carries no information.
    look_parts = []
    for key in ("setting", "palette", "companion"):
        if candidate.get(key) and prior.get(key):
            look_parts.append(jaccard(shingles(candidate[key]), shingles(prior[key])))
    scores["look"] = round(sum(look_parts) / len(look_parts), 4) if look_parts else 0.0

    # A Short and a long video are different products even from one rhyme.
    if not same_format:
        scores["structure"] = round(scores["structure"] * 0.4, 4)
        scores["look"] = round(scores["look"] * 0.6, 4)

    # Weighting, and why it is not a plain max().
    #
    # A channel legitimately has ONE house format. Every video sharing the scene template scores
    # high on structure by design, so letting structure drive the verdict would flag essentially
    # every upload - 1,460 alarms a year, which trains everyone to click through them. NN-3 targets
    # near-duplicate VIDEOS, not a consistent format.
    #
    # So identity (what the video actually is - its look, and its title across different rhymes)
    # carries the verdict at 70%, and structure contributes 30%. Structure alone cannot block;
    # structure on top of a shared look absolutely can.
    # Calibration, stated as the behaviour it produces against the 0.55 block line:
    #   0 of 3 treatment dimensions shared           -> ~0.15  PASS
    #   1 of 3 shared (e.g. same setting)            -> ~0.43  FLAG - a human looks
    #   2 of 3 shared (same setting + companion)     -> ~0.72  BLOCK - that is a reskin
    #   3 of 3 shared                                -> ~1.00  BLOCK
    # Structure sits at 15% because the channel has one house format by design: nearly every
    # pair scores high on it, so any heavier weight turns it into a constant offset that
    # squeezes the legitimate variation budget and blocks unrelated videos.
    identity = ["look"] if same_rhyme else ["title", "look"]
    identity_score = max(scores[k] for k in identity)
    composite = identity_score * 0.85 + scores["structure"] * 0.15

    scores = {k: round(v, 4) for k, v in scores.items()}
    scores["_scored_on"] = f"{'+'.join(identity)} (85%) + structure (15%)"
    return scores, round(composite, 4)


def check(candidate, today=None):
    rules = load_rules()
    th = rules["thresholds"]
    idx = load_index()
    published = idx.get("published", [])
    today = today or dt.date.today().isoformat()
    cooldown = th.get("title_cooldown_days", 21)

    # Hard cooldown: the same title in the same format may not recur inside the window,
    # however different the treatment. This is what replaced the old weekly volume cap.
    cooldown_hit = None
    for prior in published:
        if (prior.get("rhyme_id") == candidate.get("rhyme_id")
                and prior.get("format", "long") == candidate.get("format", "long")):
            gap = days_between(today, prior.get("published_on"))
            if gap is not None and gap < cooldown:
                if cooldown_hit is None or gap < cooldown_hit["days_ago"]:
                    cooldown_hit = {
                        "ref": prior.get("ref"), "days_ago": gap,
                        "cooldown_days": cooldown, "format": prior.get("format", "long"),
                        "published_on": prior.get("published_on"),
                    }

    comparisons = []
    for prior in published:
        per_dim, worst = compare(candidate, prior)
        comparisons.append({
            "against": prior.get("ref") or prior.get("rhyme_id"),
            "title": prior.get("rhyme_title"),
            "published_on": prior.get("published_on"),
            "scores": per_dim,
            "max_similarity": round(worst, 4),
        })
    comparisons.sort(key=lambda c: c["max_similarity"], reverse=True)

    max_sim = comparisons[0]["max_similarity"] if comparisons else 0.0
    if cooldown_hit or max_sim >= th["duplicate_similarity_block"]:
        verdict = "BLOCK"
    elif max_sim >= th["duplicate_similarity_flag"]:
        verdict = "FLAG"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "max_similarity": round(max_sim, 4),
        "compared_against": len(published),
        "block_threshold": th["duplicate_similarity_block"],
        "flag_threshold": th["duplicate_similarity_flag"],
        "cooldown_days": cooldown,
        "cooldown_violation": cooldown_hit,
        "closest": comparisons[:3],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--package", help="script.json (or publish package) to check")
    g.add_argument("--index", action="store_true", help="show the published index")
    ap.add_argument("--write", action="store_true", help="write duplicate_check.json beside the package")
    ap.add_argument("--ref", default="")
    args = ap.parse_args()

    if args.index:
        idx = load_index()
        pub = idx.get("published", [])
        if not pub:
            print("Published index is empty. Nothing has shipped yet.")
            return 0
        print(f"{'ref':<16}{'rhyme':<18}{'published':<13}title")
        print("-" * 78)
        for p in pub:
            print(f"{p.get('ref',''):<16}{p.get('rhyme_id',''):<18}"
                  f"{p.get('published_on',''):<13}{p.get('rhyme_title','')}")
        return 0

    path = pathlib.Path(args.package)
    if not path.is_absolute():
        path = ROOT / path
    candidate = json.loads(path.read_text(encoding="utf-8"))
    ref = args.ref or candidate.get("ref") or path.parent.name

    result = check(candidate)

    print(f"Duplicate check: {result['verdict']}")
    print(f"  max similarity : {result['max_similarity']:.3f}")
    print(f"  compared with  : {result['compared_against']} published video(s)")
    print(f"  thresholds     : flag >= {result['flag_threshold']}, block >= {result['block_threshold']}")
    if result["closest"]:
        print("\n  Closest matches:")
        for c in result["closest"]:
            dims = "  ".join(f"{k}={v:.2f}" for k, v in c["scores"].items()
                             if isinstance(v, (int, float)))
            dims += f"   [scored on {c['scores'].get('_scored_on', 'n/a')}]"
            print(f"    {c['max_similarity']:.3f}  {c['against']:<14} {c['title']}")
            print(f"          {dims}")
    if result.get("cooldown_violation"):
        cv = result["cooldown_violation"]
        print(f"\n  COOLDOWN VIOLATION: this exact title was published as a "
              f"{cv['format']} {cv['days_ago']} day(s) ago ({cv['ref']}, {cv['published_on']}).")
        print(f"  The cooldown is {cv['cooldown_days']} days. Pick a different title, or a "
              f"different format.")
    if result["verdict"] == "BLOCK":
        print("\n  BLOCKED. This is too close to something already published.")
        print("  Change the rhyme, the setting, the characters AND the structure - not just the title.")
    elif result["verdict"] == "FLAG":
        print("\n  FLAGGED. A human confirms this is a genuinely distinct video before it proceeds.")

    if args.write:
        out = path.parent / "duplicate_check.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"\n  written: {out.relative_to(ROOT)}")

    audit_log.log_decision("duplicate_check", result["verdict"],
                           f"Max similarity {result['max_similarity']:.3f} against "
                           f"{result['compared_against']} published video(s).",
                           actor="duplicate_detection", ref=ref)
    return {"PASS": 0, "FLAG": 1, "BLOCK": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
The pipeline. Runs a video from idea to a publish package that is READY FOR A HUMAN - and stops there.

    idea -> script -> copy -> music clearance -> video prompts -> [HUMAN REVIEW GATE] -> publish package
                                                                          ^
                                                        the pipeline cannot cross this by itself

There is no --force, no --yes, no --auto-publish flag, and adding one would be a policy change requiring a
CHANGELOG entry and a conversation. "Never auto-publish without a human passing the /review/ gate" is a
maintenance rule, and the only way to honour it in software is to make the software unable to do it.

    python3 scripts/pipeline.py --ref VID-2026-001 --rhyme hickory_dickory
    python3 scripts/pipeline.py --ref VID-2026-001 --status
    python3 scripts/pipeline.py --ref VID-2026-001 --package
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "review"))

import audit_log
from compliance_gate import BLOCK, ComplianceError, check_publish_package, preflight
from duplicate_detection import check as dup_check

MUSIC_TRACKER = ROOT / "music" / "licensing_tracker.csv"
SIGNOFF_NAME = "signoff.json"

STAGES = ["script", "copy", "music", "video", "duplicate", "review", "package"]


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def workdir(ref):
    return ROOT / "build" / ref


def music_row(rhyme_id):
    """Look up the clearance row. No row means no render (NN-5)."""
    import csv
    if not MUSIC_TRACKER.exists():
        return None
    with MUSIC_TRACKER.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("rhyme_id") == rhyme_id:
                return row
    return None


def stage_status(ref):
    d = workdir(ref)
    return {
        "script": (d / "script.json").exists(),
        "copy": (d / "copy.json").exists(),
        "video_prompts": (d / "video_prompts.json").exists(),
        "duplicate_check": (d / "duplicate_check.json").exists(),
        "human_signoff": (d / SIGNOFF_NAME).exists(),
        "publish_package": (d / "publish_package.json").exists(),
    }


def cmd_status(ref):
    d = workdir(ref)
    if not d.exists():
        print(f"No work directory for {ref}. Start with:\n"
              f"  python3 scripts/pipeline.py --ref {ref} --rhyme <rhyme_id>")
        return 1
    st = stage_status(ref)
    print(f"Pipeline status for {ref}   ({d.relative_to(ROOT)})\n")
    for k, v in st.items():
        print(f"  [{'x' if v else ' '}] {k}")
    if not st["human_signoff"]:
        print(f"\n  BLOCKED AT THE HUMAN REVIEW GATE.")
        print(f"  A named person completes review/safety_checklist.md and writes "
              f"{(d / SIGNOFF_NAME).relative_to(ROOT)}.")
        print(f"  Template: review/gate_signoff.template.json")
    return 0


def build_video_prompts(script):
    """Turn the script into per-scene generation prompts, with the negative prompt attached to every one."""
    negative = ("extra limbs, extra fingers, six fingers, malformed hands, warped face, melting features, "
                "asymmetric eyes, distorted anatomy, garbled text, misspelled words, gibberish letters, "
                "watermark, signature, logo, brand marks, photorealistic child, uncanny valley, "
                "horror, gore, blood, weapons, darkness, menacing shadows, scary expression, "
                "sexualised, adult themes, crowds, fast strobing, flashing lights")
    style = (f"{script['visual_style']} style, soft rounded shapes, gentle lighting, "
             f"palette of {script['palette']}, flat storybook illustration, friendly and calm, "
             f"generous negative space, slow camera")
    if script.get("format") == "short":
        style += (", vertical 9:16 composition, subject centred in the upper two thirds, "
                  "generous clear space in the lower fifth of frame")
    prompts = []
    for sc in script["scenes"]:
        prompts.append({
            "scene": sc["n"],
            "kind": sc["kind"],
            "duration_s": sc["duration_s"],
            "prompt": f"{sc['visual']} {style}. Setting: {script['setting']}. "
                      f"Featuring {script['companion']}.",
            "negative_prompt": negative,
            "camera": "slow push in" if sc["kind"] == "open" else
                      "locked off" if sc["kind"] == "learn" else "very slow drift",
            "on_screen_text": sc["on_screen_text"],
            "text_warning": ("AI models garble text. If this scene carries on-screen words, render them "
                             "as a separate overlay in your editor, never inside the generated frame."
                             if sc["on_screen_text"] else ""),
            "review_required": True,
        })
    return {
        "ref": script.get("ref", ""),
        "visual_style": script["visual_style"],
        "global_negative_prompt": negative,
        "style_prompt": style,
        "scenes": prompts,
        "_note": "Every generated frame is reviewed by a human against video/frame_review_checklist.md "
                 "before it enters an edit. NN-4 has no sampling clause: 100% of frames.",
    }


def cmd_run(ref, rhyme, seed, fmt="long"):
    d = workdir(ref)
    d.mkdir(parents=True, exist_ok=True)

    print(f"{'='*78}\nPIPELINE {ref}\n{'='*78}")

    # 1. script
    if run([sys.executable, "scripts/rhyme_generator.py", "--rhyme", rhyme, "--ref", ref,
            "--format", fmt,
            *(["--seed", str(seed)] if seed is not None else [])]) != 0:
        print("\nStopped at the script stage.", file=sys.stderr)
        return 2
    script = json.loads((d / "script.json").read_text(encoding="utf-8"))
    script["ref"] = ref

    # 2. copy
    if run([sys.executable, "scripts/title_thumbnail_copy.py",
            "--script", f"build/{ref}/script.json", "--ref", ref]) != 0:
        print("\nStopped at the copy stage.", file=sys.stderr)
        return 2

    # 3. music clearance (NN-5)
    print(f"\n$ music clearance lookup: {rhyme}")
    row = music_row(rhyme)
    if row is None:
        audit_log.log_decision("music", "BLOCK",
                               f"No clearance row in music/licensing_tracker.csv for {rhyme!r}.",
                               actor="pipeline", ref=ref)
        print(f"BLOCKED - NN-5: no row in music/licensing_tracker.csv for rhyme {rhyme!r}.\n"
              f"No row, no render. Add the clearance row with evidence first.", file=sys.stderr)
        return 2
    if row.get("clearance_status") != "CLEARED":
        audit_log.log_decision("music", "BLOCK",
                               f"Music for {rhyme!r} is {row.get('clearance_status')!r}, not CLEARED.",
                               actor="pipeline", ref=ref)
        print(f"BLOCKED - NN-5: music clearance is {row.get('clearance_status')!r}.\n"
              f"  {row.get('notes','')}", file=sys.stderr)
        return 2
    print(f"  CLEARED - {row.get('composition_pd_basis','')[:60]}")
    print(f"  evidence: {row.get('evidence_url','')}")
    audit_log.log_decision("music", "PASS", f"Music cleared for {rhyme!r}.", actor="pipeline",
                           ref=ref, evidence=row.get("evidence_url", ""))

    # 4. video prompts
    print(f"\n$ building video prompts")
    prompts = build_video_prompts(script)
    (d / "video_prompts.json").write_text(json.dumps(prompts, indent=2) + "\n", encoding="utf-8")
    print(f"  {len(prompts['scenes'])} scene prompt(s) -> build/{ref}/video_prompts.json")
    audit_log.log_decision("video_prompt", "PASS",
                           f"Generated {len(prompts['scenes'])} scene prompts with safety negatives.",
                           actor="pipeline", ref=ref)

    # 5. duplicate detection (NN-3)
    dup = dup_check(script)
    (d / "duplicate_check.json").write_text(json.dumps(dup, indent=2) + "\n", encoding="utf-8")
    print(f"\n$ duplicate check: {dup['verdict']} (max similarity {dup['max_similarity']:.3f})")
    audit_log.log_decision("duplicate_check", dup["verdict"],
                           f"Max similarity {dup['max_similarity']:.3f}.", actor="pipeline", ref=ref)
    if dup["verdict"] == "BLOCK":
        print(f"BLOCKED - NN-3: too similar to published work. Change the rhyme, setting, characters "
              f"and structure.", file=sys.stderr)
        return 2

    # 6. THE HUMAN GATE
    print(f"\n{'='*78}")
    print("HUMAN REVIEW GATE - the pipeline stops here and cannot continue on its own.")
    print(f"{'='*78}")
    print(f"""
A named person must now:

  1. Generate the frames from build/{ref}/video_prompts.json using your AI video tool.
  2. Review 100% of them against video/frame_review_checklist.md
       - warped faces, extra limbs, garbled text, anything unsafe or creepy
  3. Work through review/safety_checklist.md and review/quality_bar.md
  4. Copy review/gate_signoff.template.json to build/{ref}/signoff.json, fill it in and sign it
  5. Re-run:  python3 scripts/pipeline.py --ref {ref} --package

There is no flag that skips this. That is deliberate.""")
    audit_log.log_decision("review", "FLAG", "Reached the human review gate; awaiting named sign-off.",
                           actor="pipeline", ref=ref)
    return 0


def cmd_package(ref):
    d = workdir(ref)
    signoff_path = d / SIGNOFF_NAME
    if not signoff_path.exists():
        print(f"BLOCKED - no human sign-off at {signoff_path.relative_to(ROOT)}.\n\n"
              f"The review gate has not been passed. Copy review/gate_signoff.template.json there, "
              f"complete it, and sign it.\nThe pipeline will not build a publish package without a named "
              f"human behind it.", file=sys.stderr)
        audit_log.log_decision("publish", "BLOCK", "Package requested without a human sign-off.",
                               actor="pipeline", ref=ref)
        return 2

    script = json.loads((d / "script.json").read_text(encoding="utf-8"))
    copy = json.loads((d / "copy.json").read_text(encoding="utf-8"))
    dup = json.loads((d / "duplicate_check.json").read_text(encoding="utf-8"))
    signoff = json.loads(signoff_path.read_text(encoding="utf-8"))
    row = music_row(script["rhyme_id"]) or {}

    if not signoff.get("human_reviewer_name"):
        print("BLOCKED - the sign-off has no reviewer name. An unsigned sign-off is not a sign-off.",
              file=sys.stderr)
        return 2

    title = signoff.get("chosen_title") or (copy["titles"][0]["text"] if copy["titles"] else "")
    thumb = signoff.get("chosen_thumbnail_text") or (
        copy["thumbnail_text"][0]["text"] if copy["thumbnail_text"] else "")

    pkg = {
        "ref": ref,
        "built_on": dt.date.today().isoformat(),
        "rhyme_id": script["rhyme_id"],
        "format": script.get("format", "long"),
        "aspect": script.get("aspect", "16:9"),
        "visual_style": script["visual_style"],
        "runtime_s": script["runtime_s"],
        "no_offplatform_collection": True,
        "metadata": {
            "title": title,
            "description": copy["description"],
            "thumbnail_text": thumb,
            "made_for_kids": True,
            "comments_disabled": True,
            "personalized_ads": False,
            "live_chat": False,
            "notifications": False,
            "altered_content_disclosed": script["visual_style"] == "photorealistic",
            "category": "Education",
            "language": "en",
            "tags": ["nursery rhyme", "kids songs", script["rhyme_title"].lower()],
        },
        "music": {
            "rhyme_id": script["rhyme_id"],
            "clearance_status": row.get("clearance_status"),
            "evidence_url": row.get("evidence_url"),
            "composition_pd_basis": row.get("composition_pd_basis"),
            "recording_owner": row.get("recording_owner"),
        },
        "review": {
            "human_reviewer_name": signoff.get("human_reviewer_name"),
            "reviewed_on": signoff.get("reviewed_on"),
            "frames_reviewed_pct": signoff.get("frames_reviewed_pct"),
            "safety_checklist_passed": signoff.get("safety_checklist_passed"),
            "quality_bar_passed": signoff.get("quality_bar_passed"),
            "notes": signoff.get("notes", ""),
        },
        "duplicate_check": {"max_similarity": dup["max_similarity"], "verdict": dup["verdict"]},
        "scheduling": signoff.get("scheduling", {"videos_this_week": 1, "hours_since_last_upload": 72}),
        "on_screen_text": [s["on_screen_text"] for s in script["scenes"] if s["on_screen_text"]],
    }

    result = check_publish_package(pkg)
    pkg["compliance"] = result.as_dict()
    out = d / "publish_package.json"
    out.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    audit_log.log_result("publish", result, ref=ref, actor="pipeline")

    print(f"Publish package: {out.relative_to(ROOT)}\n")
    print(result.report())
    if result.verdict == BLOCK:
        print("\nBLOCKED. Fix the findings above and rebuild the package.", file=sys.stderr)
        return 2
    print(f"\n{'='*78}")
    print(f"READY FOR UPLOAD - by a human, following publishing/youtube_upload_checklist.md")
    print(f"{'='*78}")
    print(f"  title    : {title}")
    print(f"  reviewer : {pkg['review']['human_reviewer_name']}")
    print(f"  verdict  : {result.verdict}")
    if result.verdict == "FLAG":
        print("\n  FLAGGED items above need a human decision, logged in audit/decision_log.csv, "
              "before upload.")
    print(f"\n  After upload, append the row to audit/published_index.json so future duplicate "
          f"detection can see it.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--rhyme")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--format", choices=["long", "short", "cartoon"], default="long")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--package", action="store_true")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    if args.status:
        return cmd_status(args.ref)
    if args.package:
        return cmd_package(args.ref)
    if not args.rhyme:
        ap.error("--rhyme is required to start a pipeline (or use --status / --package)")
    return cmd_run(args.ref, args.rhyme, args.seed, fmt=args.format)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
The compliance gate. Every other script in this agency imports it, and nothing reaches a human reviewer
without passing through it.

It does three jobs:

  1. Refuses to run at all when /compliance/ is missing, drifted, or more than 30 days past its 90-day
     review. ("Read every file in /compliance/ before generating any content.")
  2. Scans generated copy for banned language: off-platform data collection, engagement bait aimed at
     children, unsafe or sensational themes, and protected brands.
  3. Validates a finished publish package against the seven non-negotiables in compliance/rules.json.

Three verdicts, and the difference between them is the whole point:

    PASS   nothing found; proceed to the next gate
    FLAG   uncertain -> a human decides, and the decision is logged. NEVER auto-resolved.
    BLOCK  a non-negotiable is violated -> refused outright, no human override in software

Usage:
    python3 scripts/compliance_gate.py --text "Twinkle Twinkle Little Star | Subscribe below!"
    python3 scripts/compliance_gate.py --package build/my_video/publish_package.json
    python3 scripts/compliance_gate.py --preflight
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPLIANCE = ROOT / "compliance"
RULES_PATH = COMPLIANCE / "rules.json"

PASS, FLAG, BLOCK = "PASS", "FLAG", "BLOCK"
_SEVERITY = {PASS: 0, FLAG: 1, BLOCK: 2}

REQUIRED_COMPLIANCE_FILES = [
    "rules.json",
    "README.md",
    "ftc-kids-privacy-compliance-plan.md",
    "youtube-made-for-kids-policy.md",
    "music-licensing-basics.md",
    "ai-disclosure-labeling.md",
    "source_text/coppa-statute-15-usc-6501-6506.txt",
    "source_text/coppa-rule-16-cfr-part-312.txt",
    "source_text/copyright-17-usc-102-106-302-305.txt",
]


class ComplianceError(RuntimeError):
    """Raised when the agency is not in a state where it is allowed to generate anything."""


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------
class Finding:
    __slots__ = ("verdict", "rule_id", "message", "evidence", "remedy")

    def __init__(self, verdict, rule_id, message, evidence="", remedy=""):
        self.verdict, self.rule_id = verdict, rule_id
        self.message, self.evidence, self.remedy = message, evidence, remedy

    def as_dict(self):
        return {"verdict": self.verdict, "rule_id": self.rule_id, "message": self.message,
                "evidence": self.evidence, "remedy": self.remedy}

    def __str__(self):
        s = f"[{self.verdict}] {self.rule_id}: {self.message}"
        if self.evidence:
            s += f"\n         evidence: {self.evidence}"
        if self.remedy:
            s += f"\n         remedy:   {self.remedy}"
        return s


class Result:
    def __init__(self, findings=None):
        self.findings = list(findings or [])

    @property
    def verdict(self):
        if not self.findings:
            return PASS
        return max((f.verdict for f in self.findings), key=lambda v: _SEVERITY[v])

    @property
    def ok(self):
        return self.verdict == PASS

    @property
    def blocked(self):
        return self.verdict == BLOCK

    def add(self, *f):
        self.findings.extend(f)
        return self

    def merge(self, other):
        self.findings.extend(other.findings)
        return self

    def as_dict(self):
        return {"verdict": self.verdict, "findings": [f.as_dict() for f in self.findings]}

    def report(self):
        if not self.findings:
            return "PASS - no compliance findings."
        return "\n".join(str(f) for f in self.findings) + f"\n\nOVERALL: {self.verdict}"


# ---------------------------------------------------------------------------
# Preflight: are we even allowed to generate?
# ---------------------------------------------------------------------------
_rules_cache = None


def load_rules(force=False):
    global _rules_cache
    if _rules_cache is None or force:
        if not RULES_PATH.exists():
            raise ComplianceError(f"compliance/rules.json is missing at {RULES_PATH}. Refusing to run.")
        _rules_cache = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return _rules_cache


def preflight(today=None):
    """Operating rule #1. Raises ComplianceError if the agency may not generate content."""
    today = today or dt.date.today()
    missing = [f for f in REQUIRED_COMPLIANCE_FILES if not (COMPLIANCE / f).exists()]
    if missing:
        raise ComplianceError(
            "Cannot generate: required compliance documents are missing:\n  - "
            + "\n  - ".join(missing)
            + "\nRestore them, or run: python3 compliance/fetch_compliance.py --refresh"
        )

    rules = load_rules()
    due = dt.date.fromisoformat(rules["next_review_due"])
    overdue = (today - due).days
    if overdue > 30:
        raise ComplianceError(
            f"Cannot generate: the 90-day compliance review is {overdue} days overdue "
            f"(due {due.isoformat()}).\nRun: python3 compliance/fetch_compliance.py --refresh, then update "
            f"last_reviewed / next_review_due in compliance/rules.json."
        )
    warning = None
    if overdue > 0:
        warning = f"Compliance review is {overdue} day(s) overdue (due {due.isoformat()}). Refresh now."
    return warning


# ---------------------------------------------------------------------------
# Copy scanning
# ---------------------------------------------------------------------------
def _matches(text, phrase):
    """Word-boundary match so 'die' does not fire on 'diet' and 'gun' not on 'begun'."""
    return re.search(r"\b" + re.escape(phrase) + r"\b", text, flags=re.IGNORECASE) is not None


def scan_text(text, context="copy"):
    """Scan any human-facing string: title, description, thumbnail text, on-screen text, script line."""
    rules = load_rules()
    banned = rules["banned_in_copy"]
    res = Result()

    for phrase in banned["data_collection"]:
        if _matches(text, phrase):
            res.add(Finding(
                BLOCK, "NN-6", f"{context} solicits contact or off-platform data from children.",
                f'matched: "{phrase}"',
                "Remove it. We never collect anything from children off-platform, in any form.",
            ))
    for phrase in banned["manipulative_or_unsafe"]:
        if _matches(text, phrase):
            res.add(Finding(
                BLOCK, "NN-4", f"{context} contains unsafe or sensational language for a preschool audience.",
                f'matched: "{phrase}"',
                "Rewrite. Kids' copy is calm, plain and warm; nothing shocking, scary or clickbait.",
            ))
    for phrase in banned["engagement_bait"]:
        if _matches(text, phrase):
            res.add(Finding(
                BLOCK, "NN-2", f"{context} contains engagement bait.",
                f'matched: "{phrase}"',
                "Remove it. On Made-for-Kids videos these features are disabled anyway, and asking "
                "children for engagement is exactly what the child-safety policies target.",
            ))
    brands = rules["protected_brands_and_characters"]
    for brand in brands.get("exact", []):
        if _matches(text, brand):
            res.add(Finding(
                BLOCK, "NN-5", f"{context} names a protected brand or character.",
                f'matched: "{brand}"',
                "Use only original characters. Never imitate or name another channel's IP.",
            ))
    # Ordinary English words that are also brand titles. Matched only in capitalised form and
    # only flagged: "a frozen pond" and "toy cars" are legitimate nursery content, and a gate
    # that blocks those is a gate people learn to route around.
    for brand in brands.get("ambiguous", []):
        if re.search(r"\b" + re.escape(brand) + r"\b", text):
            res.add(Finding(
                FLAG, "NN-5", f"{context} contains {brand!r}, which is also a protected title.",
                f'matched: "{brand}" (capitalised)',
                "Fine as an ordinary word. Confirm it is not referring to the film or franchise, "
                "and that no artwork imitates it.",
            ))

    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", text):
        res.add(Finding(BLOCK, "NN-6", f"{context} contains an email address.",
                        "email pattern matched", "Remove. No contact routes are offered to children."))
    if re.search(r"https?://", text, flags=re.IGNORECASE):
        res.add(Finding(FLAG, "NN-6", f"{context} contains a URL.",
                        "http(s):// found",
                        "Off-platform links from kids' content need a named human to approve the "
                        "destination and confirm it collects nothing from children."))
    if text.count("!") > 2:
        res.add(Finding(FLAG, "NN-4", f"{context} is shouty ({text.count('!')} exclamation marks).",
                        text[:80], "Calm the tone down. Overexcited copy reads as bait."))
    # Caps are legitimate in thumbnail artwork; in a title or narration they read as shouting.
    if "thumbnail" not in context.lower() and re.search(r"\b[A-Z]{5,}\b", text):
        res.add(Finding(FLAG, "NN-4", f"{context} contains ALL-CAPS shouting.",
                        re.search(r"\b[A-Z]{5,}\b", text).group(0), "Use sentence case."))
    return res


# ---------------------------------------------------------------------------
# Publish package validation: the seven non-negotiables
# ---------------------------------------------------------------------------
def check_publish_package(pkg):
    """Validate a finished publish package dict against all seven non-negotiables."""
    rules = load_rules()
    th = rules["thresholds"]
    res = Result()
    meta = pkg.get("metadata", {})
    review = pkg.get("review", {})
    music = pkg.get("music", {})

    # NN-1 Made for Kids
    if meta.get("made_for_kids") is not True:
        res.add(Finding(BLOCK, "NN-1", "Video is not set Made for Kids.",
                        f"made_for_kids={meta.get('made_for_kids')!r}",
                        "Set made_for_kids: true. There is no exception to this rule."))

    # NN-2 no personalised ads / comments / notifications / live chat
    for key, want, label in [("comments_disabled", True, "comments"),
                             ("personalized_ads", False, "personalized ads"),
                             ("live_chat", False, "live chat"),
                             ("notifications", False, "notifications")]:
        if meta.get(key) is not want:
            res.add(Finding(BLOCK, "NN-2", f"Publish settings do not disable {label}.",
                            f"{key}={meta.get(key)!r} (expected {want!r})",
                            "Made-for-Kids disables these at the platform level; the package must "
                            "declare them off so the upload checklist can be verified against it."))

    # NN-3 no mass production
    sim = pkg.get("duplicate_check", {}).get("max_similarity")
    if sim is None:
        res.add(Finding(FLAG, "NN-3", "No duplicate-detection result attached.",
                        "duplicate_check.max_similarity missing",
                        "Run: python3 review/duplicate_detection.py --package <pkg>"))
    elif sim >= th["duplicate_similarity_block"]:
        res.add(Finding(BLOCK, "NN-3", "Too similar to something already published.",
                        f"similarity {sim:.3f} >= block threshold {th['duplicate_similarity_block']}",
                        "Change the rhyme, setting, characters and structure - not just the title."))
    elif sim >= th["duplicate_similarity_flag"]:
        res.add(Finding(FLAG, "NN-3", "Close to previously published work.",
                        f"similarity {sim:.3f} >= flag threshold {th['duplicate_similarity_flag']}",
                        "A human confirms this is a genuinely distinct video."))

    # NN-4 human review of every AI frame
    if not review.get("human_reviewer_name"):
        res.add(Finding(BLOCK, "NN-4", "No named human reviewer.",
                        "review.human_reviewer_name is empty",
                        "A named person signs off. 'The pipeline checked it' is not a reviewer."))
    pct = review.get("frames_reviewed_pct")
    if pct != 100:
        res.add(Finding(BLOCK, "NN-4", "Not every AI frame was reviewed.",
                        f"frames_reviewed_pct={pct!r}",
                        "Review 100% of generated frames against video/frame_review_checklist.md."))
    if review.get("safety_checklist_passed") is not True:
        res.add(Finding(BLOCK, "NN-4", "The safety checklist has not been passed.",
                        f"safety_checklist_passed={review.get('safety_checklist_passed')!r}",
                        "Complete review/safety_checklist.md and record the result."))

    # NN-5 music cleared
    if music.get("clearance_status") != "CLEARED":
        res.add(Finding(BLOCK, "NN-5", "Music is not cleared.",
                        f"clearance_status={music.get('clearance_status')!r}",
                        "Every track needs a CLEARED row in music/licensing_tracker.csv. No row, no render."))
    if not music.get("evidence_url"):
        res.add(Finding(BLOCK, "NN-5", "No clearance evidence recorded for the music.",
                        "music.evidence_url is empty",
                        "Attach the work-for-hire agreement / PD verification you could hand a lawyer."))

    # NN-6 no off-platform collection
    if pkg.get("no_offplatform_collection") is not True:
        res.add(Finding(BLOCK, "NN-6", "The package does not assert zero off-platform data collection.",
                        f"no_offplatform_collection={pkg.get('no_offplatform_collection')!r}",
                        "Set it true only if nothing in this video or its description invites contact."))

    # NN-7 AI disclosure for photorealistic output
    style = (pkg.get("visual_style") or "").lower()
    if style == "photorealistic":
        if meta.get("altered_content_disclosed") is not True:
            res.add(Finding(BLOCK, "NN-7", "Photorealistic AI content without the altered-content disclosure.",
                            f"visual_style={style!r}, altered_content_disclosed="
                            f"{meta.get('altered_content_disclosed')!r}",
                            "Toggle 'Altered content' in YouTube Studio and record it here - or switch "
                            "to a stylised look, which removes the question entirely."))
        res.add(Finding(FLAG, "NN-7", "Photorealistic style is FLAG-by-default in this agency.",
                        "visual_style=photorealistic",
                        "Photorealistic depiction of children is where AI artefacts stop being funny. "
                        "Needs a named human's written reason in audit/decision_log.csv."))
    elif style not in {"cartoon", "storybook", "claymation", "puppet", "2d-animation", "3d-animation"}:
        res.add(Finding(FLAG, "NN-7", f"Unrecognised visual style {style!r}.",
                        "cannot decide AI-disclosure need",
                        "Classify it. If it could be mistaken for reality, disclose. Do not guess."))

    # Copy scan over everything a viewer can read
    for field in ("title", "description", "thumbnail_text"):
        if meta.get(field):
            res.merge(scan_text(str(meta[field]), context=f"metadata.{field}"))
    for i, line in enumerate(pkg.get("on_screen_text", [])):
        res.merge(scan_text(str(line), context=f"on_screen_text[{i}]"))

    # Scheduling / volume
    sched = pkg.get("scheduling", {})
    if sched.get("videos_this_week", 0) > th["max_videos_per_week"]:
        res.add(Finding(BLOCK, "NN-3", "Weekly upload cap exceeded.",
                        f"{sched['videos_this_week']} > {th['max_videos_per_week']}",
                        "Volume is the mass-production signal. Slow down."))
    if sched.get("hours_since_last_upload") is not None and \
            sched["hours_since_last_upload"] < th["min_hours_between_uploads"]:
        res.add(Finding(FLAG, "NN-3", "Uploads are close together.",
                        f"{sched['hours_since_last_upload']}h < {th['min_hours_between_uploads']}h",
                        "Space releases out."))
    return res


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="scan a single string of copy")
    g.add_argument("--package", help="validate a publish package JSON file")
    g.add_argument("--preflight", action="store_true", help="check the agency may generate at all")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    if args.preflight:
        print("Preflight OK - compliance corpus present and current. Generation permitted.")
        return 0

    if args.text:
        res = scan_text(args.text, context="input")
    else:
        pkg = json.loads(pathlib.Path(args.package).read_text(encoding="utf-8"))
        res = check_publish_package(pkg)

    print(json.dumps(res.as_dict(), indent=2) if args.json else res.report())
    return {PASS: 0, FLAG: 1, BLOCK: 2}[res.verdict]


if __name__ == "__main__":
    sys.exit(main())

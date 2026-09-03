#!/usr/bin/env python3
"""
Thumbnail generator. Produces a real, openable SVG thumbnail per video plus a composition brief.

On a Made-for-Kids channel the thumbnail is doing almost all of the discovery work: there is no
notification bell, no end screen, no playlist, no comment section. It is also the single most common
place a kids channel drifts into bait. So every thumbnail here is generated from the approved copy,
run through the compliance gate, and built to the same rules as the video.

What it makes:
  - <ref>-thumb.svg   1280x720 (long) or 1080x1920 (short), openable in any browser or editor
  - <ref>-thumb.json  the composition brief: hero frame to drop in, text, palette, safe zones

The hero image is a labelled placeholder rect. Export the frame you approved during review and drop
it in - the thumbnail must show something that is actually in the video.

    python3 scripts/thumbnail_generator.py --script build/VID-2026-001/script.json
    python3 scripts/thumbnail_generator.py --script build/X/script.json --text "Counting Stars"
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_log
from compliance_gate import BLOCK, ComplianceError, preflight, scan_text

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_WORDS = 4

# Readable, high-contrast pairings. Kids' thumbnails are viewed small on a phone.
PALETTE_MAP = {
    "deep indigo, soft gold, cream":      ("#1b2a5e", "#3d5299", "#ffd166", "#fffaf0"),
    "sage green, warm terracotta, oat":   ("#4a6350", "#6d8a72", "#e07a5f", "#fdf6ec"),
    "dusty blue, buttermilk, pale coral": ("#3d5a80", "#5b7fa6", "#ee9b8f", "#fdf3e7"),
    "plum, mustard, soft grey":           ("#4a2545", "#6d3d66", "#e3b23c", "#f4f1ee"),
    "forest green, cream, honey":         ("#2d4a34", "#456b4f", "#e8b04b", "#fdf8ed"),
    "lavender, mint, warm white":         ("#5d4e8c", "#7d6db3", "#88d4ab", "#fffdf7"),
}
DEFAULT_PALETTE = ("#2d4a34", "#456b4f", "#e8b04b", "#fdf8ed")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def wrap(text, per_line=11):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= per_line or not cur:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines[:3]


def build_svg(text, palette, fmt, title_for_alt):
    dark, mid, accent, light = PALETTE_MAP.get(palette, DEFAULT_PALETTE)
    if fmt == "short":
        W, H = 1080, 1920
        hero = (60, 300, W - 120, 900)
        font, base_y = 130, 1500
        safe_note = "Lower fifth kept clear - YouTube Shorts UI covers it"
        ui_guard = f'<rect x="0" y="{int(H*0.8)}" width="{W}" height="{int(H*0.2)}" fill="none" stroke="{accent}" stroke-width="3" stroke-dasharray="14 10" opacity="0.55"/>'
    else:
        W, H = 1280, 720
        hero = (56, 56, 660, 608)
        font, base_y = 104, 300
        safe_note = "Right panel holds the text; hero frame sits left"
        ui_guard = ""

    lines = wrap(text, per_line=9 if fmt == "short" else 11)
    if fmt == "short":
        tx, anchor = W // 2, "middle"
    else:
        tx, anchor = 770, "start"

    spans = "".join(
        f'<text x="{tx}" y="{base_y + i * int(font * 1.12)}" text-anchor="{anchor}" '
        f'font-family="Verdana,DejaVu Sans,sans-serif" font-size="{font}" font-weight="bold" '
        f'fill="{light}" stroke="{dark}" stroke-width="{max(6, font // 14)}" '
        f'paint-order="stroke fill">{esc(l)}</text>'
        for i, l in enumerate(lines))

    hx, hy, hw, hh = hero
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title_for_alt)}">
  <title>{esc(title_for_alt)}</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.6" y2="1">
      <stop offset="0%" stop-color="{mid}"/><stop offset="100%" stop-color="{dark}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="{int(W*0.86)}" cy="{int(H*0.12)}" r="{int(W*0.09)}" fill="{accent}" opacity="0.32"/>
  <circle cx="{int(W*0.10)}" cy="{int(H*0.92)}" r="{int(W*0.12)}" fill="{accent}" opacity="0.18"/>

  <!-- HERO FRAME: replace with an approved still exported from the finished video -->
  <rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="28" fill="{light}" opacity="0.14"
        stroke="{light}" stroke-width="5" stroke-dasharray="18 12"/>
  <text x="{hx + hw // 2}" y="{hy + hh // 2}" text-anchor="middle"
        font-family="Verdana,DejaVu Sans,sans-serif" font-size="34" fill="{light}" opacity="0.85">
    drop approved hero frame here
  </text>

  {spans}
  {ui_guard}
  <!-- {esc(safe_note)} -->
</svg>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", required=True)
    ap.add_argument("--text", help="thumbnail text; defaults to a short form of the rhyme title")
    ap.add_argument("--ref", default="")
    args = ap.parse_args()

    try:
        warning = preflight()
    except ComplianceError as e:
        print(f"BLOCKED\n{e}", file=sys.stderr)
        return 2
    if warning:
        print(f"WARNING: {warning}\n", file=sys.stderr)

    path = pathlib.Path(args.script)
    if not path.is_absolute():
        path = ROOT / path
    script = json.loads(path.read_text(encoding="utf-8"))
    ref = args.ref or script.get("ref") or path.parent.name
    fmt = script.get("format", "long")

    text = args.text or " ".join(script["rhyme_title"].replace(",", "").split()[:3])

    res = scan_text(text, context="thumbnail_text")
    if res.verdict == BLOCK:
        print("BLOCKED - thumbnail copy failed the compliance gate:\n", file=sys.stderr)
        print(res.report(), file=sys.stderr)
        audit_log.log_decision("publish", "BLOCK", f"Thumbnail copy rejected: {text!r}",
                               actor="thumbnail_generator", ref=ref)
        return 2

    words = len(text.split())
    if words > MAX_WORDS:
        print(f"BLOCKED - thumbnail text is {words} words (max {MAX_WORDS}). "
              f"A preschooler cannot read a sentence off a thumbnail.", file=sys.stderr)
        return 2

    svg = build_svg(text, script.get("palette", ""), fmt, script["rhyme_title"])
    out_svg = path.parent / f"{ref}-thumb.svg"
    out_svg.write_text(svg, encoding="utf-8")

    brief = {
        "ref": ref,
        "format": fmt,
        "dimensions": "1080x1920" if fmt == "short" else "1280x720",
        "text": text,
        "words": words,
        "palette": script.get("palette", ""),
        "hero_frame": "REQUIRED - export an approved still from the finished video and replace the "
                      "dashed placeholder. The thumbnail must show something actually in the video.",
        "rules_applied": [
            "<=4 words, legible at phone size",
            "no third-party brands, characters or trade dress",
            "no clickbait, no curiosity gap, no shock imagery",
            "honest about the content - it is not a lure",
            "high contrast: text carries a dark stroke over a mid-tone ground",
        ],
        "compliance": res.as_dict(),
        "human_check": "Shrink it to 210px wide and look again. If the text is not instantly "
                       "readable there, it fails - that is the size most people see.",
    }
    out_json = path.parent / f"{ref}-thumb.json"
    out_json.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")

    audit_log.log_decision("publish", res.verdict if res.findings else "PASS",
                           f"Thumbnail generated for {ref} ({fmt}): {text!r}",
                           actor="thumbnail_generator", ref=ref,
                           evidence=str(out_svg.relative_to(ROOT)))

    print(f"Thumbnail : {out_svg.relative_to(ROOT)}  ({brief['dimensions']})")
    print(f"Brief     : {out_json.relative_to(ROOT)}")
    print(f"Text      : \"{text}\" ({words} word(s))  gate: {res.verdict}")
    print(f"\nNext: replace the dashed placeholder with an approved hero frame, then shrink to "
          f"210px and confirm the text still reads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

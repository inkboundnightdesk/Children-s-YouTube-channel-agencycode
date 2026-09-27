#!/usr/bin/env bash
# Run Gates 0–2 for the first test video, then stop for human review.
# Never publishes. Never writes signoff.json.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REF="${1:-VID-2026-001}"
RHYME="${2:-hickory_dickory}"
FORMAT="${3:-long}"

echo "== Gate 0: preflight =="
python3 scripts/compliance_gate.py --preflight

echo
echo "== Gate 1: cleared rhymes =="
python3 scripts/rhyme_generator.py --list

echo
echo "== Gate 2: pipeline ${REF} / ${RHYME} / ${FORMAT} =="
python3 scripts/pipeline.py --ref "$REF" --rhyme "$RHYME" --format "$FORMAT" --seed 3

echo
echo "Stopped at the human review gate, as designed."
echo "Next: generate frames from build/${REF}/video_prompts.json"
echo "Then: video/frame_review_checklist.md → review/safety_checklist.md → signoff.json"
echo "See FIRST_VIDEO.md"

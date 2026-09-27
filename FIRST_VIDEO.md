# First video — exact commands

Run these from the repo root. Python 3.8+. No pip. Gate numbers match `QUICKSTART.md`.

Default test: `hickory_dickory` → `VID-2026-001` (long).
Or: `bash scripts/first_video.sh`

---

## Once, on a machine with internet

```bash
python3 compliance/fetch_compliance.py --refresh
```

## Gate 0 — may we generate?

```bash
python3 scripts/compliance_gate.py --preflight
```

Need: `Preflight OK`. If BLOCKED, run `--refresh` and `--check`.

## Gate 1 — pick a cleared rhyme

```bash
python3 scripts/rhyme_generator.py --list
```

Need: `PD?  yes` and a `CLEARED` row in `music/licensing_tracker.csv`.

Deliberate refusal (this is the system working):

```bash
python3 scripts/rhyme_generator.py --rhyme wheels_bus --ref TEST-001
```

## Gate 2 — pipeline (stops at human review)

```bash
python3 scripts/pipeline.py --ref VID-2026-001 --rhyme hickory_dickory --format long --seed 3
```

Short instead:

```bash
python3 scripts/pipeline.py --ref SHT-2026-001 --rhyme humpty --format short
```

Read before moving on:

- `build/VID-2026-001/script.json`
- `build/VID-2026-001/copy.json` — **you pick the title**
- `build/VID-2026-001/video_prompts.json`

## Gate 3 — generate frames

Take `video_prompts.json` into Higgsfield (or your current tool). One prompt per scene. No text inside frames — overlay words in the editor.

## Gate 4–5 — human only

- `video/frame_review_checklist.md` — **100% of frames**
- `review/safety_checklist.md`
- `review/quality_bar.md`

Parent test and loop test must both be an easy yes.

## Gate 6 — sign off

```bash
cp review/gate_signoff.template.json build/VID-2026-001/signoff.json
```

Fill a **real name**. `frames_reviewed_pct` must be `100`. Claude/Grok is not the reviewer.

Prove the gate:

```bash
python3 scripts/pipeline.py --ref VID-2026-001 --package
```

Without `signoff.json` this BLOCKs. That is correct.

## Gate 7 — package

```bash
python3 scripts/pipeline.py --ref VID-2026-001 --package
python3 scripts/thumbnail_generator.py --script build/VID-2026-001/script.json
```

## Gate 8 — you upload

Follow `publishing/youtube_upload_checklist.md`.

After publish: confirm Made for Kids took, and comments/notifications are actually off.

## Gate 9 — close the loop

```bash
python3 scripts/audit_log.py --stage publish --decision APPROVED \
  --reason "Published Hickory Dickory Dock" --actor "YOUR NAME" --ref VID-2026-001
```

Append the real row + YouTube URL to `audit/published_index.json`.

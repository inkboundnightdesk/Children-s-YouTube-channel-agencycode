# /review/ — The Human Gate

**This folder is the point of the whole system.** Everything upstream generates; everything downstream
publishes. This is where a person decides.

| File | Purpose |
|---|---|
| [`safety_checklist.md`](safety_checklist.md) | The gate. All seven non-negotiables plus content, sensory, copy and music safety. |
| [`quality_bar.md`](quality_bar.md) | Is it worth shipping? YouTube demotes low-effort kids content, so this is compliance too. |
| [`duplicate_detection.py`](duplicate_detection.py) | Numeric enforcement of NN-3 against everything published |
| [`gate_signoff.template.json`](gate_signoff.template.json) | The artifact the pipeline demands before it will build a publish package |

## How the gate is enforced in software

`scripts/pipeline.py` stops after the video prompts and prints the human-gate banner. To continue, a person
must write `build/<ref>/signoff.json` with:

- a real `human_reviewer_name`
- `frames_reviewed_pct: 100`
- `safety_checklist_passed: true`

`compliance_gate.check_publish_package()` re-checks all three at the publish gate, so editing an
intermediate file does not get you past it. **There is no `--force`, no `--yes`, and no `--auto-publish`.**
Adding one would be a policy change requiring a CHANGELOG entry and a conversation.

## Order of operations

```
1. video/frame_review_checklist.md   100% of frames. Three passes: anatomy, text, tone.
2. review/safety_checklist.md        The seven non-negotiables + safety + copy + music.
3. review/quality_bar.md             Does it deserve to exist?
4. review/gate_signoff.template.json -> build/<ref>/signoff.json, signed.
5. python3 scripts/pipeline.py --ref <REF> --package
```

## Duplicate detection

```bash
python3 review/duplicate_detection.py --package build/<ref>/script.json --write
python3 review/duplicate_detection.py --index          # what has already shipped
```

Scores four dimensions — title, rhyme, structure, look — and takes the worst. `>= 0.55` BLOCKs, `>= 0.40`
FLAGs. A moderate **structure** score is expected when videos share the house template; that is the signal
working, not a bug. Vary scene count, runtime and arc between videos (see `../video/scene_template.md`).

## What a human is actually for

The scripts catch banned phrases, missing clearances, and numeric similarity. **They cannot see a
six-fingered hand, an unsettling smile, or a video that is technically compliant and quietly awful.**
That is the job. If the checklist ever feels like a formality, the system has failed — because at that
point nothing is actually looking.

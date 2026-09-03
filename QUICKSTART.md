# Quick Start — Your First Compliant Video

Exact steps, end to end, with **what to check at each gate before moving to the next.** Every command
below has been run; the outputs shown are real.

**Requirements:** Python 3.8+. Nothing else — standard library only, no `pip install`, no network.

> **Do this once first, from a machine with open internet:**
> ```bash
> python3 compliance/fetch_compliance.py --refresh
> ```
> The verbatim law in `compliance/source_text/` came through provenance-tracked mirrors because the
> government sites were blocked when this was built. Verify it against the official sources before you
> rely on it in production. See `audit/CHANGELOG.md` for the full list of known limitations.

---

## Gate 0 — May we generate at all?

```bash
python3 scripts/compliance_gate.py --preflight
```

```
Preflight OK - compliance corpus present and current. Generation permitted.
```

**Check before moving on:**
- [ ] It says `Preflight OK`.
- [ ] If it says **BLOCKED**, the compliance corpus is missing, hand-edited, or >30 days past its 90-day
      review. Fix that first — `python3 compliance/fetch_compliance.py --check` will tell you which.

> This is operating rule #1 in software: nothing generates until `/compliance/` is present and current.

---

## Gate 1 — Pick a cleared rhyme

```bash
python3 scripts/rhyme_generator.py --list
```

```
id                PD?   verses  mood      title
------------------------------------------------------------------------------
twinkle           yes   2       calm      Twinkle, Twinkle, Little Star
itsy_bitsy        yes   1       playful   The Itsy Bitsy Spider
hickory_dickory   yes   3       playful   Hickory Dickory Dock
...
wheels_bus        NO    5       cheerful  The Wheels on the Bus
```

**See the refusal work — run this deliberately:**

```bash
python3 scripts/rhyme_generator.py --rhyme wheels_bus --ref TEST-001
```

```
BLOCKED - NN-5 (music/composition clearance)
  Rhyme  : The Wheels on the Bus
  Basis  : UNVERIFIED. Commonly attributed to Verna Hills, 1939 - which would still be in copyright.
```

**That is not a bug.** It feels traditional, everybody treats it as free, and the common attribution is
1939 — still in copyright. Meet that lesson here, where it is free.

**Check before moving on:**
- [ ] Your rhyme shows `PD?  yes`.
- [ ] It has a `CLEARED` row in `music/licensing_tracker.csv` with a real `evidence_url`.
- [ ] It is not the same rhyme as a recent upload (`python3 review/duplicate_detection.py --index`).

---

## Gate 2 — Run the pipeline

```bash
python3 scripts/pipeline.py --ref VID-2026-001 --rhyme hickory_dickory --seed 3
```

This runs five stages and then **stops**:

1. **Script** — built from the verified rhyme, gated, written to `build/VID-2026-001/script.json`
2. **Copy** — titles, description, thumbnail text; anything that BLOCKs never reaches you
3. **Music clearance** — looks up the tracker row; **stops here if it is not `CLEARED`**
4. **Video prompts** — per-scene prompts with the safety negative prompt attached to every one
5. **Duplicate check** — scored against everything in `audit/published_index.json`

```
$ music clearance lookup: hickory_dickory
  CLEARED - Tommy Thumb's Pretty Song Book (c. 1744). Term long expired.
  evidence: evidence/hickory-wfh-2026-08-03.pdf

$ building video prompts
  7 scene prompt(s) -> build/VID-2026-001/video_prompts.json

$ duplicate check: FLAG (max similarity 0.547)

==============================================================================
HUMAN REVIEW GATE - the pipeline stops here and cannot continue on its own.
==============================================================================
```

**Check before moving on:**
- [ ] Music clearance says **CLEARED**, and you can open the evidence document.
- [ ] Duplicate check is **PASS**, or **FLAG** you have consciously accepted. If **BLOCK**, change the
      rhyme, setting, characters **and** structure — not just the title.
- [ ] Read the title candidates in `build/VID-2026-001/copy.json`. **You pick one; the script does not.**
- [ ] Read `video_prompts.json` and confirm the negative prompt is attached to every scene.

> A `FLAG` on structure similarity is common and correct — it means your video shares the house template.
> Vary scene count, runtime and arc between videos (see `video/scene_template.md`).

---

## Gate 3 — Generate frames

Take `build/VID-2026-001/video_prompts.json` into your AI video tool. One prompt per scene, with its
negative prompt and camera note.

**Check before moving on:**
- [ ] Every scene rendered.
- [ ] **No text was generated inside any frame.** Words go on as an overlay in your editor — every model
      garbles text.
- [ ] Record which tool, which model version, and its commercial-use terms **as of today**. Save that into
      the project folder. These terms change.

---

## Gate 4 — Frame review · **THE ONE THAT MATTERS**

Work through **[`video/frame_review_checklist.md`](video/frame_review_checklist.md)** — **100% of frames.
Not a sample. Not keyframes.** Artefacts appear and vanish within a few frames.

Three passes, because you cannot hold all three failure modes at once:

1. **Anatomy** — count fingers on every visible hand. Count limbs. Watch faces for drift and melt.
2. **Text** — read every visible word out loud. Check backgrounds for hallucinated signage and logos.
3. **Tone** — read it as a parent would. Anything creepy, frightening, or distressing?

**Check before moving on:**
- [ ] `frames_reviewed == frames_generated`. Exactly.
- [ ] Every failed frame regenerated **and re-reviewed from the top.** A re-review is a full review.
- [ ] No strobing above ~3 flashes/second anywhere in the timeline. *(Seizure risk.)*
- [ ] Frame checklist signed with your name and the date.

---

## Gate 5 — Safety and quality

Work through **[`review/safety_checklist.md`](review/safety_checklist.md)** and
**[`review/quality_bar.md`](review/quality_bar.md)**.

The safety checklist walks all seven non-negotiables plus content, sensory, copy and music safety. The
quality bar asks whether it deserves to exist — which is also compliance, since YouTube demotes low-effort
kids content.

**The two tests that override every checkbox:**

- [ ] **The parent test** — would you be glad if a parent watched this over their child's shoulder, all
      the way through? If that is not an easy yes, **it does not ship.**
- [ ] **The loop test** — watch it twice in a row. Does it become irritating? This audience *will* loop it.

---

## Gate 6 — Sign off

```bash
cp review/gate_signoff.template.json build/VID-2026-001/signoff.json
```

Fill it in. Required:

```json
{
  "human_reviewer_name": "Sam Ortiz",
  "frames_reviewed_pct": 100,
  "safety_checklist_passed": true,
  "quality_bar_passed": true,
  "chosen_title": "Hickory Dickory Dock - A Song About Telling The Hour",
  "chosen_thumbnail_text": "Telling The Hour"
}
```

**Verify the gate is real:**

```bash
rm build/VID-2026-001/signoff.json
python3 scripts/pipeline.py --ref VID-2026-001 --package
```
```
BLOCKED - no human sign-off at build/VID-2026-001/signoff.json.
The pipeline will not build a publish package without a named human behind it.
```

There is no flag that skips this. Put the file back.

**Check before moving on:**
- [ ] `human_reviewer_name` is a **real person**. "The pipeline checked it" is not a reviewer.
- [ ] `frames_reviewed_pct` is exactly `100`.
- [ ] Every flag raised has a resolution and a name against it.

---

## Gate 7 — Build the publish package

```bash
python3 scripts/pipeline.py --ref VID-2026-001 --package
```

```
Publish package: build/VID-2026-001/publish_package.json

[FLAG] NN-3: Close to previously published work.
         remedy: A human confirms this is a genuinely distinct video.

OVERALL: FLAG

==============================================================================
READY FOR UPLOAD - by a human, following publishing/youtube_upload_checklist.md
==============================================================================
  title    : Hickory Dickory Dock - A Song About Telling The Hour
  reviewer : Sam Ortiz
```

The gate re-validates all seven non-negotiables here, so editing an intermediate file does not get you
past it.

**Check before moving on:**
- [ ] Verdict is **PASS**, or **FLAG** with every flag resolved and logged.
- [ ] `metadata.made_for_kids` is `true`.
- [ ] `metadata.altered_content_disclosed` matches the visual style *(cartoon → false, photorealistic →
      true)*.
- [ ] The description contains **no links, no email, no call to action**.

---

## Gate 8 — Upload (a human, by hand)

Follow **[`publishing/youtube_upload_checklist.md`](publishing/youtube_upload_checklist.md)** step by step.

**The three that matter most:**

- [ ] **"Yes, it's made for kids"** selected — and **verified on the review screen after setting it.**
- [ ] **AI disclosure** correct: cartoon → Altered content **off**; photorealistic → **on**.
- [ ] **After publishing, look at whether comments and notifications are actually off.** If they are not,
      the audience setting did not take. This one look is worth more than every other check combined.

---

## Gate 9 — Close the loop

```bash
python3 scripts/audit_log.py --stage publish --decision APPROVED \
  --reason "Published Hickory Dickory Dock" --actor "Sam Ortiz" --ref VID-2026-001
```

Then append the row to `audit/published_index.json`:

```json
{
  "ref": "VID-2026-001",
  "rhyme_id": "hickory_dickory",
  "rhyme_title": "Hickory Dickory Dock",
  "published_on": "2026-09-03",
  "setting": "a sunlit kitchen garden with tall sunflowers",
  "palette": "forest green, cream, honey",
  "companion": "a fluffy duckling who hums along",
  "visual_style": "cartoon",
  "runtime_s": 124,
  "scenes": [{"kind":"open"},{"kind":"verse"},{"kind":"verse"},{"kind":"verse"},
             {"kind":"learn"},{"kind":"reprise"},{"kind":"close"}],
  "youtube_url": "https://youtube.com/watch?v=..."
}
```

**This step is not optional.** `duplicate_detection.py` reads this file. An unmaintained index means
duplicate detection silently stops working — and a silent failure is the dangerous kind.

**Check:**
- [ ] Row appended, with the real YouTube URL.
- [ ] Decision logged (`python3 scripts/audit_log.py --tail 10`).
- [ ] Check back within 24h for claims, strikes, or restrictions. Log whatever you find.

---

## Where things stop, and why

| Stop | Trigger | Fix |
|---|---|---|
| `BLOCKED` at preflight | Compliance corpus missing, drifted, or >30 days overdue | `python3 compliance/fetch_compliance.py --refresh` |
| `BLOCKED - NN-5` | Rhyme not verified PD, or no `CLEARED` tracker row | Verify properly, or pick another rhyme |
| `BLOCKED - NN-3` | Too similar to a published video | Change rhyme, setting, characters **and** structure |
| `BLOCKED` at `--package` | No `signoff.json`, or no reviewer name | Do the review. There is no override. |
| `BLOCK` on copy | Banned phrase — CTA, contact route, unsafe word, protected brand | Rewrite; the finding names the match and the remedy |

---

## Planning more than one

```bash
python3 scripts/batch_ideas.py --count 3 --weeks 1
```

Refuses to exceed 3/week, refuses two ideas sharing a rhyme, and duplicate-checks every idea against what
is already published — **at planning time, where it is cheap.**

A batch is a **plan, not an approval.** Every idea still runs the full pipeline and its own human review
gate.

---

## The rule underneath all of it

> **The human is the final approver at every gate.** The scripts catch banned phrases, missing clearances,
> and numeric similarity. They cannot see a six-fingered hand, an unsettling smile, or a video that is
> technically compliant and quietly awful.
>
> **That is your job. If the checklist ever feels like a formality, nothing is actually looking.**

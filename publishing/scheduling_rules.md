# Scheduling Rules

**Cadence: 2 long videos + 2 Shorts every day, indefinitely.** Set 2026-09-03 by the channel owner.

| Slot | Time (UTC) | Format |
|---|---|---|
| 1 | 09:00 | Long video |
| 2 | 13:00 | Short |
| 3 | 17:00 | Long video |
| 4 | 21:00 | Short |

Adjust `publish_times_utc` in [`../compliance/rules.json`](../compliance/rules.json) to your audience's
timezone. These are placeholders — pick real times from your own analytics once you have them.

---

## What changed, and what deliberately did not

The old cap was 3 videos/week. It is now 28/week. **The anti-duplication rule did not move an inch.**

The cap was never really about volume — it was a crude proxy for "don't become a template farm." At
4/day a crude proxy stops working, so it was replaced with something sharper:

| Mechanism | Rule |
|---|---|
| **Title cooldown** | The same title in the same format may not recur within **21 days**, however different the treatment. Hard BLOCK. |
| **Treatment scoring** | Same rhyme is judged on *structure* and *look*, not on the fact that it is the same rhyme. `>= 0.55` BLOCKs. |
| **Format separation** | A Short and a long video of one rhyme are different products, scored as such — but not if they share the same setting, palette and companion. That is a reskin, and it still blocks. |

High volume is permitted. **Near-duplication at any volume is not.**

---

## The arithmetic you have to respect

A daily cadence under a cooldown needs a minimum library:

```
titles required = videos per day per format × cooldown days
                = 2 × 21
                = 42 distinct titles, per format
```

Current position: **48 verified long titles, 46 for Shorts.** Six and four titles of headroom.

```bash
python3 scripts/bulk_scheduler.py --capacity
```

**That headroom is thin.** One clearance turning out to be unverifiable takes a title out of rotation and
the schedule starts leaving gaps. Treat verifying new public-domain titles as ongoing work, not a
one-time setup task — the scheduler warns whenever headroom drops to 6 or below.

To buy real headroom, widen `content_type` beyond `rhyme`: counting, alphabet, colours and shapes,
seasonal, and original `story_cartoon` pieces need no public-domain rhyme at all and expand the space
faster than verifying more rhymes does.

---

## Bulk stacking

```bash
python3 scripts/bulk_scheduler.py --days 90 --start 2026-09-04
```

Writes a calendar as both JSON and CSV:

- every slot dated, timed, and assigned a title plus a rotated treatment
- the cooldown enforced across the whole range
- capacity and review load computed up front
- **every slot marked `PENDING`**

### The one rule that makes bulk scheduling safe

> **A calendar slot is a plan. It is never an approval.**

The scheduler cannot mark anything ready to publish, and nothing may be uploaded from the calendar
file. Each slot runs the full pipeline and its own human review gate:

```bash
python3 scripts/pipeline.py --ref VID-20260904-1 --rhyme pop_weasel --format long
# ... generate frames, review 100% of them, sign off ...
python3 scripts/pipeline.py --ref VID-20260904-1 --package
```

Then, and only then, does it get scheduled in YouTube Studio.

## Pre-setting dates in YouTube Studio

Scheduling reviewed content in advance is fine and is the whole point of stacking. Upload the approved
video, set visibility to **Scheduled**, and enter the `publish_at_utc` from the calendar row.

**Confirm Made for Kids on the review screen before you schedule.** A scheduled video with the wrong
audience setting goes live unattended and stays live until somebody notices — which is exactly the
failure the review gate exists to prevent, arriving through the back door.

---

## The constraint that actually binds

Not Higgsfield capacity. Not the rhyme library. **Human review time.**

NN-4 requires 100% of AI frames reviewed by a person. At this cadence:

```
2 long  × ~38 min  = 76 min
2 short × ~14 min  = 28 min
                   = 104 min/day = 12.1 h/week
```

**Twelve hours a week of pure review, every week, forever.** That is a part-time job. The scheduler
prints it on every run and compares it against `reviewer_hours_available_per_week` in `rules.json`.

When review capacity runs short there are exactly three honest options:

1. **Add reviewers** — update `reviewer_hours_available_per_week` and staff it.
2. **Lower the cadence** — change `daily_long_videos` / `daily_shorts` in `rules.json`.
3. **Shorten runtimes** — less footage per video is less footage to review.

There is no fourth option. **Reviewing a sample is not an option** — NN-4 has no sampling clause, and
loosening it is the one change that would make this system worthless, because at that point nothing is
actually looking at what goes in front of children.

## When you cannot fill a slot

Publish nothing in it. A gap in the calendar costs a little momentum; a video pushed through a
half-finished review gate can cost the channel. **No schedule pressure in this system outranks the
review gate** — and at 4/day the pressure to skip it is exactly four times what it used to be.

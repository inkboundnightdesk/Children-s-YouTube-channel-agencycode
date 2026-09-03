# Scheduling Rules

Volume is the mass-production signal. **NN-3 is enforced as much by the calendar as by the diff.**

## Hard limits — enforced in software

From `../compliance/rules.json`:

| Rule | Value | Enforced by |
|---|---|---|
| Maximum uploads per week | **3** | `compliance_gate` BLOCKs above this |
| Minimum gap between uploads | **36 hours** | `compliance_gate` FLAGs below this |
| Duplicate similarity | **< 0.55** | `duplicate_detection.py` BLOCKs at or above |

`scripts/batch_ideas.py` refuses to plan a batch that exceeds the weekly cap at all — the limit applies at
planning time, where it is cheap, not at the review gate, where it is expensive.

## Why a cap on a channel that wants to grow

Because the thing that kills nursery-rhyme channels is not too little content. It is **too much
undifferentiated content**, which reads to YouTube's systems exactly like a template farm, because that is
what it is. Three genuinely distinct videos a week outperform ten reskins, and they do not put the channel
at risk.

**If you find the cap frustrating, that is the cap doing its job.** Raising it is a policy change: edit
`compliance/rules.json`, log it in `audit/CHANGELOG.md` with a reason, and own the decision.

## Cadence

- **Two per week is the sustainable default.** Three is the ceiling, not the target.
- Same days each week — parents build routines, and routine beats volume.
- Publish in the morning for the target region: this audience watches early.
- **Never publish two videos of the same rhyme family close together.** *Twinkle* and *Baa Baa Black Sheep*
  share a melody; back-to-back they sound like a duplicate even though they are not.

## Seasonal content

- Publish seasonal videos **2–3 weeks ahead** of the season.
- Do not rush a seasonal video through the review gate to hit a date. **The date is not a reason to skip a
  gate.** If it is not ready, it ships next year.

## What to do when you cannot fill the slot

Publish nothing.

An empty slot costs a little momentum. A video pushed through a half-finished review gate can cost the
channel. There is no schedule pressure in this system that outranks the review gate — and if anyone ever
tells you otherwise, that is the moment to point at this line.

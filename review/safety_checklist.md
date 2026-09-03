# Safety Checklist — The Gate

**This is the gate. Nothing published has not passed it, and a human passes it — never the pipeline.**

`scripts/pipeline.py` stops before this checklist and will not build a publish package until
`build/<ref>/signoff.json` exists with a real name in it. There is no `--force`.

**Ref:** ____________  **Reviewer:** ________________  **Date:** __________

> Complete [`../video/frame_review_checklist.md`](../video/frame_review_checklist.md) first. This checklist
> assumes every frame has already been looked at.

---

## 1. Compliance — the seven non-negotiables

- [ ] **NN-1** Video will be set **Made for Kids** in YouTube Studio. No exceptions.
- [ ] **NN-2** Comments, notifications, live chat and personalised ads are off *(automatic under MFK — verify, don't assume)*
- [ ] **NN-3** Duplicate check run and not BLOCK. Genuinely distinct from everything published.
- [ ] **NN-4** 100% of AI frames reviewed. Frame checklist signed.
- [ ] **NN-5** Music row is `CLEARED` in `../music/licensing_tracker.csv` with real evidence behind it.
- [ ] **NN-6** Nothing anywhere invites contact, data, or off-platform action from a child.
- [ ] **NN-7** AI disclosure decision made correctly: photorealistic → disclosed; stylised → not required.

## 2. Content safety

- [ ] Nothing frightening, violent, or distressing — including cartoon peril.
- [ ] No adult themes, innuendo, or anything sexualised in any form.
- [ ] No "Elsagate" pattern: a children's surface must not carry adult or disturbing content.
- [ ] No dangerous behaviour a child could imitate — climbing, hiding in appliances, eating non-food,
      approaching strangers or animals unsafely.
- [ ] No unsafe messaging about strangers, secrets, or keeping things from parents.
- [ ] Characters model kindness. No bullying, mocking, or exclusion played for laughs.
- [ ] Nothing that would distress a child watching alone at bedtime.

## 3. Sensory safety

- [ ] **No strobing or flashing above ~3 per second.** Seizure risk. Check the whole timeline.
- [ ] Audio levels are consistent — no sudden jumps, no startling sounds.
- [ ] No harsh, piercing, or grating frequencies.
- [ ] Pacing suits preschool: slow cuts, shots held, room to breathe.

## 4. Copy — title, description, thumbnail, on-screen text

- [ ] Compliance gate run and PASS: `python3 scripts/compliance_gate.py --text "<title>"`
- [ ] No call to action of any kind — no subscribe, no bell, no "comment below".
- [ ] No links, no email addresses, no contact routes anywhere in the description.
- [ ] Title describes the video honestly. **No curiosity gaps, no clickbait, no all-caps.**
- [ ] Thumbnail shows what is actually in the video. It is not a lure.
- [ ] Thumbnail text is ≤4 words and readable at phone size.
- [ ] No third-party brands, characters, or trade dress in copy or thumbnail.

## 5. Music

- [ ] Track matches the `CLEARED` tracker row for this rhyme.
- [ ] The recording is ours, and the work-for-hire agreement is signed and filed in `../music/evidence/`.
- [ ] No third-party recording, no library track, no "famous version" anywhere in the mix.
- [ ] Any AI music tool used has its commercial-use terms captured and dated.

## 6. Quality

- [ ] [`quality_bar.md`](quality_bar.md) worked through and passed.
- [ ] The video teaches, soothes, or delights. **It has a reason to exist beyond filling a slot.**

## 7. The parent test

> **Would you be glad if a parent watched this over their child's shoulder, all the way through?**

- [ ] Yes.

If that answer is anything other than an easy yes, **it does not ship.** No amount of checklist ticks
overrides it.

---

## Verdict

- [ ] **APPROVED** — write `build/<ref>/signoff.json` from `gate_signoff.template.json`, then run
      `python3 scripts/pipeline.py --ref <REF> --package`
- [ ] **REVISE** — note what must change; the pipeline re-runs from the affected stage
- [ ] **REJECTED** — does not ship; record why

**Notes:**

_______________________________________________________________________________

**Signature:** ________________  **Date:** __________

> ```
> python3 scripts/audit_log.py --stage review --decision APPROVED \
>   --reason "Safety checklist passed; all seven non-negotiables verified" \
>   --actor "<your name>" --ref <REF>
> ```

---

## If you are uncertain

**Flag it. Do not guess.** That is an operating rule, and it applies to humans exactly as much as to the
agent. An uncertain FLAG that turns out to be fine costs an hour. A guess that turns out to be wrong, on a
children's channel, costs the channel.

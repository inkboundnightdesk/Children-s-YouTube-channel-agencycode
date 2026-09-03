# YouTube Upload Checklist

**A human uploads. Always.** The pipeline produces `build/<ref>/publish_package.json` and stops. Nothing
in this repository touches the YouTube API, and that is deliberate — the last mile is where the
irreversible mistakes live.

**Ref:** ____________  **Uploader:** ________________  **Date:** __________

---

## Before you open YouTube Studio

- [ ] `build/<ref>/publish_package.json` exists and its compliance verdict is **PASS** (or FLAG with every
      flag resolved and logged).
- [ ] `build/<ref>/signoff.json` is signed by a named human.
- [ ] Any FLAG has a decision recorded in `../audit/decision_log.csv`.

```bash
python3 scripts/compliance_gate.py --package build/<ref>/publish_package.json
```

---

## 1. Audience — NN-1, the one that matters most

- [ ] **"Yes, it's made for kids"** selected.
- [ ] Verified on the review screen **after** setting it. Do not assume the channel default applied.
- [ ] Age restriction: **not** set *(an 18+ restriction on kids content is a contradiction — if you think
      you need it, the video should not ship)*.

> Set the channel-level default to Made for Kids as well, so a new upload is never one forgotten click
> away from a violation. **Then verify per video anyway.** Both. Every time.

## 2. AI disclosure — NN-7

- [ ] **Stylised / cartoon** → "Altered content" toggle **off**. No disclosure required.
- [ ] **Photorealistic people, animals or places** → "Altered content" **on**.
- [ ] Matches `metadata.altered_content_disclosed` in the publish package.

> If it is genuinely unclear, **disclose.** The label costs far less than a strike, and resolving ambiguity
> by staying silent is guessing.

## 3. Metadata

- [ ] Title copied exactly from the package. ≤100 characters.
- [ ] Description copied exactly. **No links, no email, no contact route, no CTA.**
- [ ] Thumbnail uploaded; text ≤4 words, legible at phone size, honest about the content.
- [ ] Category set (usually Education or Music).
- [ ] Language and captions set.
- [ ] Tags are descriptive, not stuffed, and name no third-party brand.
- [ ] **No end screens. No cards.** *(Unavailable on MFK anyway — do not fight it.)*

## 4. Confirm what MFK turned off — NN-2

These are disabled automatically. **Verify, do not assume:**

- [ ] Comments off
- [ ] Live chat off
- [ ] Notifications off
- [ ] Personalised ads off *(contextual only)*
- [ ] Save to playlist / Watch Later off
- [ ] Channel memberships, merch, Super Chat off

> **If any of these appear to be ON, stop and re-check the audience setting.** It almost certainly did not
> take. This is the single highest-value check on this page.

## 5. Monetisation

- [ ] Ad settings reviewed. Personalised advertising **not** enabled.
- [ ] No paid product placement or sponsorship.
- [ ] No affiliate links anywhere.

## 6. Scheduling

- [ ] Publish time follows `scheduling_rules.md`.
- [ ] ≥36 hours since the last upload.
- [ ] ≤3 uploads this week.

## 7. Final look — before you press publish

- [ ] Watch the uploaded version end to end **in the YouTube player**, not your editor. Encoding changes
      things.
- [ ] Thumbnail renders correctly at small size.
- [ ] Title is not truncated in a way that changes its meaning.
- [ ] Audio levels are right in the YouTube player.

---

## After publishing

- [ ] Append the row to `../audit/published_index.json` — **future duplicate detection is blind without
      it.**
- [ ] Log it:
      ```
      python3 scripts/audit_log.py --stage publish --decision APPROVED \
        --reason "Published <title>" --actor "<your name>" --ref <REF>
      ```
- [ ] Record the YouTube URL in the index row.
- [ ] Check back within 24h: any strike, claim, or restriction? Log whatever you find.

---

## If something goes wrong after publishing

1. **Unlist first, ask second.** Unlisting is instant and reversible; a strike is neither.
2. Log the incident: `--stage incident --decision ESCALATED`.
3. Work out the root cause before re-uploading. A re-upload of the same problem is two violations.
4. If it is a Content ID claim, go to `../music/evidence/` and follow
   `../compliance/music-licensing-basics.md`. **Do not dispute without documentation.**

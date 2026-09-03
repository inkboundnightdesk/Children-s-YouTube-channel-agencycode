# YouTube "Made for Kids" — What It Is and What It Costs

> **Document type: RESTATEMENT with official sources.**
> YouTube's Help Center and policy pages are copyrighted material owned by Google. This repository
> deliberately **does not mirror them** — reproducing them wholesale into a distributed zip would be its own
> licensing violation, and a stale local copy of a platform policy is actively dangerous. What follows is
> the agency's operational restatement, with the authoritative URLs to read at the source.
> **Reading the live pages is part of the 90-day cycle.** `compliance/fetch_compliance.py` opens them.
> Last reviewed: 2026-09-03 · Next review: 2026-12-02

## Authoritative sources — read these, not just this file

| Topic | URL |
|---|---|
| Set your channel or video's audience | <https://support.google.com/youtube/answer/9527654> |
| Watching "made for kids" content | <https://support.google.com/youtube/answer/9632097> |
| Ads on supervised accounts and MFK content | <https://support.google.com/youtube/answer/9713557> |
| Child safety policy | <https://support.google.com/youtube/answer/2801999> |
| Quality principles for kids content | <https://support.google.com/youtube/answer/10774223> |
| Altered or synthetic content disclosure | <https://support.google.com/youtube/answer/14328491> |
| Announcement of the kids policy change | <https://blog.youtube/news-and-events/better-protecting-kids-privacy-on-youtube/> |

---

## The setting is mandatory and it is a legal declaration

Every creator must set an audience — at the channel level (applies to all existing and future uploads) or
per video. There is no "unset" state you are allowed to leave behind.

**For this channel the answer is always the same: Made for Kids, every video, no exceptions.**
That is non-negotiable **NN-1**, and `scripts/compliance_gate.py` will not emit a publish package without
`made_for_kids: true`.

Setting it is not a formality. It is a declaration to YouTube — and through YouTube, effectively to the
FTC — about who your content is for. **Getting it wrong on purpose is the violation.** Setting it at the
channel level, once, and then verifying it per upload is the cheapest insurance in this entire pipeline.

---

## What the setting turns off

When content is Made for Kids, YouTube restricts data collection, and features that depend on that data —
or that create unsupervised social surface for children — stop working:

- Personalized advertising
- Comments
- Live chat, live chat donations, Super Chat, Super Stickers
- The notification bell / notifications
- Save to playlist and Save to Watch Later
- Channel memberships, merchandise and ticketing, the donate button
- Cards and end screens
- Video watermarks (including the subscribe watermark)
- Autoplay on the home feed
- Miniplayer playback
- Stories and community-style features

**Three of the seven non-negotiables are simply this list, restated.** NN-2 is not an extra burden the
agency invented — it is what the platform does automatically. Our job is to *design for it* rather than
fight it.

### The consequences you must actually plan around

This is where channels get hurt, so be blunt about it:

1. **Revenue per view drops.** Contextual ads only; no personalized targeting. Model the business on that
   number, not on a general-audience CPM.
2. **Every standard growth lever is gone.** No end screens, no cards, no notification bell, no playlists
   saved by viewers, no comment community. Discovery comes from search, suggested video, and the strength
   of the thumbnail and first ten seconds. Nothing else.
3. **You cannot call the audience to action.** No "subscribe," no "hit the bell," no "comment below" — the
   features do not exist, and addressing children with engagement bait is exactly the manipulation the
   child-safety policies target. `rules.json` bans these phrases in copy for this reason.
4. **Retention is the only real signal.** Which is a compliance advantage in disguise: it rewards making
   something genuinely good rather than something engineered to farm interaction.

---

## "Made for Kids" ≠ "in the YouTube Kids app"

A frequent and expensive misunderstanding. Setting MFK does **not** guarantee inclusion in the YouTube Kids
app. That app has a separate, stricter curation process, and YouTube may decline content that is perfectly
acceptable as MFK on the main platform. Plan for the main platform; treat YouTube Kids inclusion as upside,
never as the business model.

---

## Quality principles — the part with no checkbox

Beyond the legal minimum, YouTube publishes quality principles for kids content and **demotes content that
violates them even when nothing is technically against the rules.** Paraphrasing the substance:

**Favored:** content that teaches, sparks creativity or curiosity, encourages real-world interaction,
models good relationships, and is age-appropriate in pacing and complexity.

**Demoted or removed:** heavily commercial or purely acquisitive content; content that encourages negative
behaviors or attitudes; sensational, misleading, or shocking material; low-quality mass-produced content
with little effort or originality; and content that is deceptively made to look like it is for children
while containing adult themes ("Elsagate"-pattern material — YouTube removes this and it is a child-safety
violation, not a gray area).

**Non-negotiable NN-3 lives here.** "No mass-production patterns, no near-duplicate uploads, no template
farms" is not just our house preference — near-duplicate output at volume is the exact profile YouTube
demotes. `review/duplicate_detection.py` enforces it numerically before anything reaches the upload gate.

---

## The operational summary

| Question | Answer |
|---|---|
| Audience setting? | Made for Kids. Every video. Channel level **and** verified per upload. |
| Comments? | Off automatically. Do not attempt workarounds. |
| Personalized ads? | Off automatically. Model revenue accordingly. |
| Calls to action? | None. The features don't exist and the ask is inappropriate to the audience. |
| Publishing volume? | ≤ 3/week, ≥ 36 h apart, each meaningfully distinct (`rules.json` thresholds). |
| YouTube Kids app? | Separate curation. Not guaranteed. Not the plan. |

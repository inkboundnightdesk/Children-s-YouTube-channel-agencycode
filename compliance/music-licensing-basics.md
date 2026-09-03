# Music Licensing for Nursery Rhymes

> **Document type: RESTATEMENT.** Controlling text is verbatim in
> [`source_text/copyright-17-usc-102-106-302-305.txt`](source_text/copyright-17-usc-102-106-302-305.txt).
> Not legal advice. Last reviewed: 2026-09-03 · Next review: 2026-12-02

---

## The one mistake that sinks nursery-rhyme channels

**"The song is old, so it's free."**

That sentence is half true, and the half that is false is the expensive half. Every piece of music you can
hear is **two separate copyrights**:

| | The **composition** | The **sound recording** |
|---|---|---|
| What it covers | Melody and lyrics — the song as written | One specific fixed performance of it |
| Statutory basis | 17 U.S.C. § 102(a)(2), "musical works, including any accompanying words" | 17 U.S.C. § 102(a)(7), "sound recordings" |
| Nursery rhyme status | Usually **public domain** — genuinely centuries old | **Almost always protected.** Someone recorded it recently. |

"Twinkle, Twinkle, Little Star" as a composition is public domain and has been for well over a century.
**A 2019 recording of it is fully copyrighted for roughly the next century.** Using that recording is
ordinary infringement, and the song's age is no defense at all.

There is a third trap: **the arrangement.** A new arrangement of a public-domain melody — a particular
harmonization, a specific instrumental setting, an added bridge — is itself a protectable derivative work
in the *new* material it adds (§ 102, § 106(2)). "Baby Shark" is the canonical example: the chant is
traditional folklore, and Pinkfong's specific arrangement and recording are aggressively enforced property.
Public-domain source material does **not** make a specific modern version free.

---

## The channel's rule, and why it is simple on purpose

> **NN-5: Public-domain rhymes only, or properly licensed. No famous recorded versions.**

**We use a public-domain composition, and we create our own original recording of it.**

That single decision removes the entire recording-rights analysis:

- The **composition** is public domain → no license needed for the underlying song.
- The **recording** is ours, made for us, work-for-hire in writing → we own it outright.
- The **arrangement** is ours → we own that too, and it becomes an asset rather than a liability.
- Content ID disputes become answerable with evidence we actually hold: session files, stems, invoices,
  and a signed work-for-hire agreement.

Anything other than this path — licensing a third-party recording, using a library track, commissioning
from someone who will not sign work-for-hire — is a **FLAG**, not a decision the agent may make alone.

---

## Determining public domain: the arithmetic

From §§ 302–305, as of **2026**:

| Situation | Rule | Status in 2026 |
|---|---|---|
| Published in the U.S. in **1930 or earlier** | 95 years from publication | **Public domain** |
| Published 1931 | 95 years | Enters PD 2027-01-01 |
| Created 1978 or later | Life of author + 70 years (§ 302(a)) | Protected |
| Anonymous / pseudonymous / work for hire, 1978+ | 95 years from publication or 120 from creation, whichever expires first (§ 302(c)) | Protected |
| All terms | Run to **December 31** of the final year (§ 305) | — |

Traditional nursery rhymes — *Twinkle Twinkle*, *Row Row Row Your Boat*, *Old MacDonald*, *Mary Had a
Little Lamb*, *The Itsy Bitsy Spider*, *London Bridge*, *Hickory Dickory Dock* — predate 1930 by a wide
margin as compositions. **They are safe as compositions.** They are not safe as recordings.

### Two nuances that are genuinely tricky

**Sound recordings have their own schedule.** Pre-1972 recordings are governed by the Music Modernization
Act (Pub. L. 115-264, Title II), not the ordinary term rules — recordings published 1923–1946 get 100 years
from publication, on a rolling basis. **Do not attempt this analysis in-house.** Our own-recording rule
means we never have to; if someone proposes using a historical recording, that is a FLAG → counsel.

**"Traditional" is not a verified status.** Some songs that *feel* like folk songs have identifiable
20th-century authors and live copyrights. Verify each title against a real source before use — never
against intuition. `music/public_domain_sources.md` lists where to verify.

> § 114 and § 115 (sound-recording rights and the mechanical license) are **deliberately excluded** from
> `source_text/` — the mirror available at build time predates the 2018 Music Modernization Act that
> rewrote them. If a question turns on those sections, re-fetch them from `uscode.house.gov` first.

---

## What must be true before any track enters a video

Every track needs a row in [`../music/licensing_tracker.csv`](../music/licensing_tracker.csv) with
`clearance_status = CLEARED` and a working `evidence_url`. `scripts/compliance_gate.py` checks this and
**blocks the render** if the row is missing, `PENDING`, or `FLAGGED`.

Evidence means a document you could hand a lawyer:

1. **Composition** — the title, its PD basis, and the source that verified it.
2. **Recording** — the session date, performer, and the signed work-for-hire agreement.
3. **Arrangement** — who arranged it and under what agreement.
4. **Every stem and asset** — including any AI music tool used, with that tool's commercial-use terms
   captured at the date of use. AI music services change their terms; a screenshot dated to the session
   is worth more later than a remembered impression.

**No row, no render.** No exceptions, including for "obviously fine" traditional songs — the row is what
proves it was obviously fine, six months later, to someone who wasn't there.

---

## If a Content ID claim arrives

1. **Do not panic and do not blanket-dispute.** A claim on a PD composition is often an automated match
   against someone else's *recording* of it, which is a false positive on your original recording.
2. Pull the evidence from the tracker row.
3. If the evidence is complete and the claim is against material we created — dispute, citing the
   work-for-hire agreement and session files.
4. If the evidence is incomplete — **do not dispute.** Fix the underlying gap first. A dispute you cannot
   document is worse than the claim.
5. Log the claim, the decision, and the reason in `audit/decision_log.csv` either way.

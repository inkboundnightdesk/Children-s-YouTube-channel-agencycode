# Verifying Public Domain — Where to Actually Look

Read [`../compliance/music-licensing-basics.md`](../compliance/music-licensing-basics.md) first. This file
is the *how*: where you go to turn "I think this is traditional" into a citation you could hand a lawyer.

**A rhyme enters `../scripts/rhyme_library.json` with `pd_verified: true` only when you have a specific
printed source with a date.** Not a vibe. Not a Wikipedia sentence with no citation. Not "everyone uses it."

---

## The standard we hold

> **First publication in print before 1930, verified against a citable source, with the citation recorded.**

As of 2026, U.S. works published in 1930 or earlier are in the public domain (95-year term,
17 U.S.C. § 304). The line moves forward one year every January 1 — in 2027 it becomes 1931. Most genuine
nursery rhymes predate this by a century or more, so the verification is usually easy. **The point is doing
it at all, and writing down what you found.**

---

## Primary sources — the ones that settle it

| Source | What it gives you | URL |
|---|---|---|
| **HathiTrust** | Scanned pages of the actual 18th/19th-century collections. The strongest evidence there is: you can see the rhyme, in print, with the date. | <https://www.hathitrust.org> |
| **Internet Archive** | Full scans of *Mother Goose's Melody*, *Tommy Thumb's Pretty Song Book*, Victorian songbooks | <https://archive.org> |
| **Project Gutenberg** | Clean transcriptions of PD rhyme collections | <https://www.gutenberg.org> |
| **Library of Congress — Performing Arts** | American songbooks, sheet music, dated | <https://www.loc.gov/collections/> |
| **IMSLP / Petrucci Music Library** | Public-domain sheet music with per-item copyright review | <https://imslp.org> |
| **U.S. Copyright Office public records** | Search registrations and renewals — the way to check whether something is *still* protected | <https://www.copyright.gov/public-records/> |

## Secondary sources — useful for finding, never for proving

- **The Oxford Dictionary of Nursery Rhymes** (Iona and Peter Opie) — the scholarly reference on origins
  and first-printing dates. Excellent for *finding* the citation. Cite the underlying printing, not the
  dictionary.
- **Wikipedia** — fine as a starting point. **Follow the footnote to the actual source.** An uncited
  Wikipedia claim is not verification and must never be recorded as one.

---

## Recording it

Every verified rhyme needs both:

1. A row in [`licensing_tracker.csv`](licensing_tracker.csv) with `composition_pd_basis`,
   `composition_verified_by`, and `composition_verified_on`.
2. `pd_verified: true` plus `pd_basis` and `source` in `../scripts/rhyme_library.json`.

Then log it: `python3 scripts/audit_log.py --stage music --decision APPROVED --reason "..." --actor "<you>"`.

---

## The traps

**"Traditional" is a feeling, not a status.** `The Wheels on the Bus` is the worked example carried through
this repository: it feels ancient, everybody treats it as free, and the common attribution is **Verna
Hills, 1939** — which would still be in copyright. `scripts/rhyme_generator.py` refuses it, on purpose, so
you meet the lesson before it costs you anything.

**A public-domain composition does not make a specific version free.** Someone's 2019 recording and
arrangement of a 1744 rhyme is fully protected. This is why we record our own.

**Sound recordings run on their own clock.** Pre-1972 recordings are governed by the Music Modernization
Act's rolling schedule, not the ordinary term rules. **Do not attempt that analysis here** — our
own-recording rule means we never need to. Anyone proposing a historical recording gets a FLAG and a
conversation with counsel.

**AI music tools are a licensing question, not a creative one.** If you generate a backing track with an AI
service, capture that service's commercial-use terms *on the day you use it*, save the screenshot into
`evidence/`, and record it in the tracker's `ai_tool_used` / `ai_tool_terms_captured` columns. These terms
change. A screenshot dated to the session is worth far more later than a remembered impression.

**Fifteen seconds is not a safe harbour.** There is no duration below which using someone else's recording
becomes legal. That belief has cost a lot of channels a lot of money.

---

## The default path, restated

> **Public-domain composition + our own original recording + our own arrangement + a signed work-for-hire
> agreement.**

Every other path is a FLAG that a human resolves — with a lawyer where the money justifies it — before a
single frame is rendered.

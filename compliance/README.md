# /compliance/ — The Law Shelf

**Nothing in this agency generates a single word or frame until the files in this folder have been read.**
That is operating rule #1 in [`rules.json`](rules.json), and `scripts/compliance_gate.py` enforces it by
refusing to run when the documents here are missing or stale.

---

## What is in here

### `source_text/` — verbatim law, not summaries

These are the actual statutory and regulatory texts. They are U.S. Government works and are not subject to
copyright, so they are reproduced in full.

| File | What it is | Bytes |
|---|---|---|
| `coppa-statute-15-usc-6501-6506.txt` | The Children's Online Privacy Protection Act itself, §§ 6501–6506 complete | ~27 KB |
| `coppa-rule-16-cfr-part-312.txt` | The FTC's COPPA Rule, §§ 312.1–312.13 complete, **including the 2025 amendments** | ~46 KB |
| `copyright-17-usc-102-106-302-305.txt` | Copyright subject matter, exclusive rights, and the duration rules that decide public-domain status | ~110 KB |
| `PROVENANCE.json` | Source URL, retrieval date, and SHA-256 for each of the above |

Each file opens with a provenance header naming the authoritative URL, the retrieval date, and what to
verify before relying on it. The copyright file includes the official Historical and Revision Notes that
accompany each section — these are also government text and are useful for interpretation.

**Read `PROVENANCE.json` before trusting any of it.** The texts were obtained through provenance-tracked
third-party mirrors because `uscode.house.gov`, `ecfr.gov`, and `ftc.gov` are blocked from the network this
was built on. They were checked against known citations (the COPPA Rule carries the correct
`78 FR 4008 … as amended at 90 FR 16977, Apr. 22, 2025` source line, and § 312.2 contains the 2025
"mixed audience" definition), but *checked* is not *authoritative*. The first thing you should do with this
repository is run:

```bash
python3 compliance/fetch_compliance.py --refresh
```

from a machine with open internet access. It re-downloads all four documents straight from the government
sources and tells you, byte for byte, whether anything changed.

### Interpretation layer — how the law applies to *this* channel

| File | What it is |
|---|---|
| `ftc-kids-privacy-compliance-plan.md` | The FTC's six-step compliance plan, mapped onto a nursery-rhyme channel, with the 2025 amendments called out |
| `youtube-made-for-kids-policy.md` | What the "Made for Kids" setting does, what it disables, and what YouTube requires of you |
| `ai-disclosure-labeling.md` | When AI content must carry the altered/synthetic-content label and when it must not |
| `music-licensing-basics.md` | Composition vs. recording vs. arrangement, and the public-domain arithmetic |
| `rules.json` | The seven non-negotiables in machine-readable form, plus banned copy and thresholds |

These five are **restatements, clearly marked as such.** They are written by the agency, not by a
government or by YouTube, and every factual claim carries a citation back to `source_text/` or to an
official URL. Where YouTube's own policy text is concerned, this folder deliberately links and restates
rather than reproducing: YouTube's Help Center and policy pages are copyrighted material owned by Google,
and mirroring them into a distributed repository is itself a licensing problem. The URLs are all in
`fetch_compliance.py`, and reading them at the source is part of the 90-day cycle.

---

## The 90-day rule

> **Every document in this folder must be re-fetched and re-read every 90 days.**

Not because it is tidy. Because it has already happened once: the FTC amended the COPPA Rule in
April 2025 (90 FR 16977), with full compliance required by **April 22, 2026**. A channel running on
pre-2025 assumptions about what counts as "personal information," what data-retention policy it must
publish, and when a *separate* parental consent is needed for third-party disclosure would have been out
of compliance without ever changing a line of its own process.

| Field | Value |
|---|---|
| Last full review | **2026-09-03** |
| Next review due | **2026-12-02** |
| Interval | 90 days |
| Tracked in | [`../audit/policy_update_tracker.csv`](../audit/policy_update_tracker.csv) |

`scripts/compliance_gate.py` reads `next_review_due` from `rules.json` on every single run. Past due, it
prints a loud warning; more than 30 days past due, **it stops the pipeline entirely.** That is deliberate.
A compliance folder nobody refreshes is worse than none, because it manufactures confidence.

### Running the refresh

```bash
python3 compliance/fetch_compliance.py --check     # is anything stale? (exit 1 if so)
python3 compliance/fetch_compliance.py --refresh   # re-download, diff, report
```

`--refresh` writes `LAST_FETCHED.json`, updates the SHA-256 in `PROVENANCE.json`, and prints a diff summary.
**If a hash changed, a human reads the diff before anything else ships.** Then log it in
`audit/CHANGELOG.md` and reset `next_review_due` in `rules.json`.

---

## A necessary disclaimer

This folder is a working compliance system assembled by a production team. It is **not legal advice**, and
no one here is your lawyer. It is built to make the safe path the easy path and to make uncertainty
*visible* rather than silent — that is what the FLAG state throughout the pipeline is for. Where the stakes
are real (a licensing question you cannot answer from `music-licensing-basics.md`, an FTC inquiry, a
copyright claim, a question about whether your specific channel is "directed to children"), the correct
action is the one the agent rules already require: **flag it and escalate to qualified counsel. Do not
guess.**

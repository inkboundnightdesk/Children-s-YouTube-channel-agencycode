# /music/evidence/ — The Documents Themselves

The tracker's `evidence_url` column points here. **A tracker row without a real document behind it is a
claim, not evidence.**

What belongs here, per cleared track:

- **Work-for-hire agreement**, signed by the performer/arranger *before* the session. This is what makes
  the recording ours rather than theirs.
- **Public-domain verification** — the scan, screenshot, or citation showing the composition in print
  before 1930 (a HathiTrust page image is ideal).
- **Session records** — date, personnel, session files, stems.
- **AI tool terms** — if any AI music service was used, its commercial-use terms captured *on the day of
  use*, dated. These change; a remembered impression is worthless in a dispute.
- **Any third-party licence** — the full executed document, covering YouTube, worldwide, in perpetuity.

Naming: `<rhyme_id>-<doctype>-<YYYY-MM-DD>.pdf`, e.g. `twinkle-wfh-2026-08-01.pdf`.

## If a Content ID claim lands

This folder is the answer. A claim on a public-domain composition is usually an automated match against
someone else's *recording* — a false positive against our original one. Pull the work-for-hire agreement
and the session files and dispute with specifics.

**If the evidence is incomplete, do not dispute.** Fix the gap first. A dispute you cannot document is
worse than the claim. Log the decision either way in `audit/decision_log.csv`.

*(The filenames referenced in `licensing_tracker.csv` are illustrative — replace them with your real
executed documents. Keep them in version control or in a backed-up store; do not let them live only on
someone's laptop.)*

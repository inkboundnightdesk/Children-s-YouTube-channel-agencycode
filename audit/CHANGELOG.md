# Change Log

Every policy change, every rule change, every compliance review. **Append only — never rewrite history.**
This file and `decision_log.csv` are what answer "why did we ship that?" months later, to a lawyer, to
YouTube, or to yourself.

Format: `## YYYY-MM-DD — <what changed>` with **what**, **why**, and **who**.

---

## 2026-09-03 — Agency system created

**What:** Initial build of the complete agency system: compliance corpus, generation scripts, review gates,
publishing checklists, audit trail.

**Why:** Establish an automated nursery-rhyme production pipeline that cannot ship non-compliant content,
with a human as the final approver at every gate.

**Who:** system (initial build)

**Detail:**

- `/compliance/source_text/` populated with verbatim law:
  - 15 U.S.C. §§ 6501–6506 (COPPA statute), complete
  - 16 C.F.R. Part 312 §§ 312.1–312.13 (COPPA Rule), complete, **including the 2025 amendments**
    (78 FR 4008 as amended at 90 FR 16977, Apr. 22, 2025)
  - 17 U.S.C. §§ 102, 106, 302–305 (copyright subject matter, exclusive rights, duration)
- Seven non-negotiables encoded in `compliance/rules.json` with machine checks.
- `scripts/compliance_gate.py` enforces preflight, copy scanning, and publish-package validation.
- `review/duplicate_detection.py` enforces NN-3 numerically across four dimensions.
- `scripts/pipeline.py` built with **no** `--force` / `--auto-publish` path. The human gate is
  structurally uncrossable by software.
- 8 public-domain rhymes verified into `scripts/rhyme_library.json`; `wheels_bus` deliberately left
  unverified as a worked example of a refusal.

**Known limitations, recorded honestly:**

1. **Source text came through third-party mirrors.** `uscode.house.gov`, `ecfr.gov` and `ftc.gov` were
   blocked by the build environment's network policy. The texts were obtained from provenance-tracked
   mirrors (`bebetterest/content-rules-corpus` for COPPA, extracted from the eCFR XML API and
   uscode.house.gov with SHA-256 recorded; `publicdocs/uscode` for Title 17) and sanity-checked against
   known citations. **Verify them against the official sources on the first run with open network access:**
   `python3 compliance/fetch_compliance.py --refresh`.
2. **17 U.S.C. §§ 114 and 115 are excluded.** The available Title 17 mirror is a 2016 snapshot and predates
   the 2018 Music Modernization Act, which rewrote both. The duration sections we *did* include are
   unamended since 1998 and are reliable. Re-fetch before relying on §§ 114/115.
3. **YouTube policy text is not mirrored.** It is copyrighted by Google. `/compliance/` links and restates
   it; a human reads the live pages each 90-day cycle.
4. **Licensing tracker rows reference illustrative evidence filenames.** Replace them with your real
   executed work-for-hire agreements before shipping anything.

---

## Template for future entries

```markdown
## YYYY-MM-DD — <short description>

**What:** what changed
**Why:** what prompted it — a policy update, an incident, a lesson
**Who:** name
**Impact:** which files, which rules, which videos
**Follow-up:** anything still open
```

---

## Recording a 90-day review

Every cycle gets an entry, **even when nothing changed** — "we checked and it was unchanged" is itself the
record that the check happened.

```markdown
## YYYY-MM-DD — 90-day compliance review

**What:** Re-fetched COPPA statute, COPPA Rule, and copyright duration sections. Read YouTube MFK,
child safety, quality, and AI disclosure pages at source.
**Changes detected:** none / <describe>
**Who:** name
**Actions:** updated compliance/rules.json next_review_due to YYYY-MM-DD
```

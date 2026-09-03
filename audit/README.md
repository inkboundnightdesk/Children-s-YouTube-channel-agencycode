# /audit/ — The Record

Operating rule #4: **log every decision with a date and a reason.** This folder is what answers
"why did we ship that?" six months later — to a lawyer, to YouTube, or to yourself.

| File | Purpose |
|---|---|
| [`decision_log.csv`](decision_log.csv) | Every decision by every stage. Append-only. Written by `scripts/audit_log.py`. |
| [`CHANGELOG.md`](CHANGELOG.md) | Policy and rule changes, and each 90-day review |
| [`policy_update_tracker.csv`](policy_update_tracker.csv) | Per-source freshness with due dates |
| [`published_index.json`](published_index.json) | Every published video. **Duplicate detection reads this.** |

## Logging a decision

```bash
python3 scripts/audit_log.py --stage review --decision FLAG \
  --reason "Frame 44 hand geometry unclear; regenerated" \
  --actor "Sam Ortiz" --ref VID-2026-001

python3 scripts/audit_log.py --tail 20
```

Stages: `ideation script music video_prompt generation review duplicate_check publish policy incident`
Decisions: `PASS FLAG BLOCK APPROVED REJECTED REVISED ESCALATED NOTE`

A reason is **required**. An unexplained decision is not a logged decision, and `log_decision()` raises if
you try.

## The 90-day cycle

`policy_update_tracker.csv` carries `next_due` per source. `compliance/rules.json` carries the master
`next_review_due`, and **`scripts/compliance_gate.py` reads it on every single run**:

| State | Behaviour |
|---|---|
| Current | Runs normally |
| Overdue 1–30 days | Loud warning on every command |
| **Overdue > 30 days** | **The pipeline stops. Nothing generates.** |

That escalation is deliberate. A compliance folder nobody refreshes is worse than none, because it
manufactures confidence.

```bash
python3 compliance/fetch_compliance.py --check     # exit 1 if stale or drifted
python3 compliance/fetch_compliance.py --refresh   # re-download, diff, report
```

`--check` also verifies the SHA-256 of each source-text file against `PROVENANCE.json`, so hand-edited
reference law is caught immediately. **Nobody edits the law by hand.**

## published_index.json

Append a row after every upload. `review/duplicate_detection.py` compares candidates against it, so **an
unmaintained index means duplicate detection silently stops working** — the failure is invisible, which is
what makes it dangerous. Never delete rows: the history *is* the anti-duplication defence.

## If something goes wrong

Log it as `--stage incident --decision ESCALATED` with what happened, what you did, and what you changed
so it does not recur. Then add a CHANGELOG entry. **An incident with no changed process is an incident
that will happen again.**

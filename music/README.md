# /music/ — Clearance Before Render

This folder answers one question for every track: **can we prove we are allowed to use this?**

| File | Purpose |
|---|---|
| [`licensing_tracker.csv`](licensing_tracker.csv) | The register. One row per rhyme. The pipeline reads it. |
| [`public_domain_sources.md`](public_domain_sources.md) | Where to verify public-domain status properly |
| `evidence/` | The actual documents: work-for-hire agreements, PD verification, AI tool terms |

## How it is enforced

`scripts/pipeline.py` looks up the rhyme in `licensing_tracker.csv` **before generating any video
prompts.** If there is no row, or the row is not `CLEARED`, the pipeline stops with a `BLOCK`. Then
`compliance_gate.check_publish_package()` checks it again at the publish gate, so a track cannot slip
through by editing an intermediate file.

**No row, no render.** This applies to "obviously fine" traditional songs too — the row is what proves it
was obviously fine, six months later, to someone who wasn't there.

## Clearance statuses

| Status | Meaning | Pipeline |
|---|---|---|
| `CLEARED` | PD composition verified, our own recording, evidence on file | Proceeds |
| `PENDING` | Clearance started, not finished | **Blocks** |
| `FLAGGED` | A real problem — unverified PD, or a third-party recording | **Blocks** |

## Adding a rhyme

1. Verify the composition against a primary source (see `public_domain_sources.md`).
2. Commission or record an original performance. **Get work-for-hire signed in writing before the session.**
3. Save the agreement and PD verification into `evidence/`.
4. Add the tracker row with `clearance_status: CLEARED` and a working `evidence_url`.
5. Add the rhyme to `../scripts/rhyme_library.json` with `pd_verified: true`.
6. Log it: `python3 scripts/audit_log.py --stage music --decision APPROVED --reason "..."`.

Skipping straight to step 4 is the failure this folder exists to prevent.

# /scripts/ — Generation, Gated

Everything here calls `compliance_gate.preflight()` before it does anything, and gates its own output
before writing it. **A script that generates without gating is a bug.**

| File | Purpose |
|---|---|
| [`compliance_gate.py`](compliance_gate.py) | **The enforcement engine.** Preflight, copy scanning, publish-package validation. Imported by everything. |
| [`pipeline.py`](pipeline.py) | End-to-end orchestrator. Stops dead at the human review gate. |
| [`rhyme_generator.py`](rhyme_generator.py) | Builds a script from a verified public-domain rhyme. Refuses unverified ones. |
| [`title_thumbnail_copy.py`](title_thumbnail_copy.py) | Titles, description, thumbnail text — CTA-free by construction |
| [`batch_ideas.py`](batch_ideas.py) | Batch planning with anti-duplication and volume caps applied up front |
| [`audit_log.py`](audit_log.py) | Append-only decision log. Refuses an empty reason. |
| [`rhyme_library.json`](rhyme_library.json) | Verified public-domain rhymes. `pd_verified: false` means the generator refuses it. |

**Python 3.8+, standard library only.** No `pip install`, no virtualenv, no network. Clone and run.

## Typical use

```bash
python3 scripts/compliance_gate.py --preflight              # may we generate at all?
python3 scripts/rhyme_generator.py --list                   # what is cleared?
python3 scripts/batch_ideas.py --count 3 --weeks 1          # plan a week
python3 scripts/pipeline.py --ref VID-2026-001 --rhyme hickory_dickory
#   ... human review happens here ...
python3 scripts/pipeline.py --ref VID-2026-001 --package
```

## Exit codes — usable in CI

| Code | Meaning |
|---|---|
| `0` | PASS |
| `1` | FLAG — a human decides |
| `2` | BLOCK — refused |

## The three verdicts

`PASS` proceeds. `FLAG` means **a named human decides and the decision is logged** — never "proceed
carefully". `BLOCK` is refused with **no software override**.

## Adding a script

1. `from compliance_gate import preflight, scan_text` and call `preflight()` first.
2. Gate your output **before** you write it, not after.
3. Log the outcome with `audit_log.log_result()`.
4. Return `0/1/2` to match the verdict.
5. Never add a flag that skips a gate. If you think you need one, that is a policy conversation, not a
   code change.

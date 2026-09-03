# Nursery Rhyme Channel — Agency System

A complete, runnable production system for an AI-assisted children's nursery-rhyme YouTube channel, built
so that **non-compliant content cannot reach an upload**, and so that a human is the final approver at
every gate.

Python 3.8+, **standard library only**. No install step, no dependencies, no network access required to
run. Clone it and go.

```bash
python3 scripts/compliance_gate.py --preflight
```

---

## The seven non-negotiables

| ID | Rule | Enforced by |
|---|---|---|
| **NN-1** | Every video labeled **Made for Kids**. No exceptions. | `compliance_gate` · upload checklist |
| **NN-2** | No personalized ads, comments, notifications, or live chat. | `compliance_gate` · upload checklist |
| **NN-3** | No mass-production patterns, near-duplicates, or template farms. | `duplicate_detection.py` · `batch_ideas.py` |
| **NN-4** | All AI output human-reviewed for warped faces, extra limbs, garbled text, unsafe visuals. | `frame_review_checklist.md` · sign-off gate |
| **NN-5** | Public-domain rhymes only, or properly licensed. No famous recorded versions. | `licensing_tracker.csv` · `pipeline.py` |
| **NN-6** | No collecting personal data from children off-platform, anywhere. | `compliance_gate` copy scanner |
| **NN-7** | Photorealistic AI carries the AI label; cartoon does not — but still gets the kids setting. | `compliance_gate` · upload checklist |

Machine-readable in [`compliance/rules.json`](compliance/rules.json). The agent's operating contract is
[`AGENT_RULES.md`](AGENT_RULES.md) — **load that as the system prompt.**

---

## How the folders connect

```
                        ┌─────────────────────────────────────────┐
                        │            /compliance/                 │
                        │  verbatim COPPA + FTC Rule + copyright  │
                        │  rules.json = 7 non-negotiables         │
                        │  re-fetched every 90 days               │
                        └────────────────────┬────────────────────┘
                          read first, by everything below
                                             │
     ┌───────────────┬───────────────────────┼───────────────────┐
     ▼               ▼                       ▼                   ▼
┌─────────┐    ┌──────────┐            ┌──────────┐        ┌──────────┐
│/scripts/│───▶│ /music/  │            │ /video/  │        │ /audit/  │
│ rhymes  │    │ clearance│            │ prompts  │        │ every    │
│ titles  │    │ tracker  │            │ scenes   │        │ decision │
│ batches │    │ evidence │            │ frame QA │        │ 90-day   │
└────┬────┘    └────┬─────┘            └────┬─────┘        │ tracker  │
     │              │                       │              └────▲─────┘
     │   NN-5: no row, no render            │                   │
     └──────────────┴───────────────────────┘                   │
                          │                                     │
                          ▼                                     │
                 ┌─────────────────┐                            │
                 │    /review/     │   ◀── THE HUMAN GATE ──▶    │
                 │ safety checklist│   nothing crosses this      │
                 │ quality bar     │   without a named person    │
                 │ duplicate detect│                             │
                 └────────┬────────┘                             │
                          │ signoff.json                         │
                          ▼                                      │
                 ┌─────────────────┐                             │
                 │  /publishing/   │─────────────────────────────┘
                 │ upload checklist│   logged back to /audit/
                 │ metadata · sched│
                 └─────────────────┘
                          │
                          ▼
                  a human uploads
```

### What each folder does, and what it hands to the next

**[`/compliance/`](compliance/)** — the law shelf, and the root of everything. Holds the **verbatim** text
of COPPA (15 U.S.C. §§ 6501–6506), the FTC's COPPA Rule (16 C.F.R. Part 312, including the 2025
amendments), and the copyright sections that decide public-domain status — plus restatements applying them
to this channel, and `rules.json`, the machine-readable form the scripts enforce.
**Feeds: everything.** `compliance_gate.preflight()` refuses to run if this folder is missing, drifted, or
more than 30 days past its 90-day review.

**[`/scripts/`](scripts/)** — generation, gated. Rhyme scripts from verified public-domain sources, titles
and descriptions with no call to action, batch plans that enforce diversity up front.
**Reads:** `/compliance/`, `/music/`. **Writes:** `build/<ref>/`, `/audit/`.

**[`/music/`](music/)** — clearance before render. One tracker row per rhyme; the pipeline looks it up
*before* generating video prompts and stops if it is not `CLEARED`. **No row, no render.**
**Feeds:** `/scripts/`, the publish package.

**[`/video/`](video/)** — prompts in, reviewed frames out. House style, the mandatory negative prompt,
scene templates, and the 100%-of-frames review checklist where NN-4 lives.
**Reads:** the script. **Feeds:** `/review/`.

**[`/review/`](review/)** — **the human gate, and the point of the whole system.** Safety checklist,
quality bar, numeric duplicate detection, and the sign-off artifact the pipeline demands.
**Blocks:** `/publishing/`. Nothing reaches an upload without a named human here.

**[`/publishing/`](publishing/)** — the last mile, done by hand. Upload checklist, metadata contract,
scheduling caps. **This repository never touches the YouTube API.**
**Reads:** the publish package. **Writes:** `/audit/published_index.json`.

**[`/audit/`](audit/)** — the record. Every decision with a date and a reason, the change log, the 90-day
policy tracker, and the published index that duplicate detection reads.
**Fed by:** every stage. **Feeds:** `/review/` (via the published index) and the next 90-day cycle.

---

## Quick start — one test video, end to end

Full detail in **[QUICKSTART.md](QUICKSTART.md)**. The short version:

```bash
# 0. May we generate at all? (checks the corpus is present and current)
python3 scripts/compliance_gate.py --preflight

# 1. What is cleared for use?
python3 scripts/rhyme_generator.py --list

# 2. Script + copy + music clearance + video prompts + duplicate check
python3 scripts/pipeline.py --ref VID-2026-001 --rhyme hickory_dickory

#    ... the pipeline STOPS at the human review gate ...
#    Generate frames from build/VID-2026-001/video_prompts.json
#    Review 100% of them: video/frame_review_checklist.md
#    Work through review/safety_checklist.md and review/quality_bar.md
#    Copy review/gate_signoff.template.json -> build/VID-2026-001/signoff.json, sign it

# 3. Build the publish package (refuses without a signed sign-off)
python3 scripts/pipeline.py --ref VID-2026-001 --package

# 4. A human uploads, following publishing/youtube_upload_checklist.md
```

Try `--rhyme wheels_bus` to watch the system refuse a rhyme whose public-domain status is unverified. That
refusal is the system working.

---

## The human is the final approver at every gate

**This is the design principle, not a disclaimer.**

The pipeline has no `--force`, no `--yes`, and no `--auto-publish`. It does not touch the YouTube API. It
stops before review and refuses to build a publish package until `build/<ref>/signoff.json` exists with a
real person's name, `frames_reviewed_pct: 100`, and a passed safety checklist — and the compliance gate
re-checks all three at the publish gate, so editing an intermediate file does not get you past it.

That is deliberate. Automating the last mile would make the worst possible failure — a bad video going live
unattended, in front of children — the *easy* failure. Every gate is a place where a person looks:

| Gate | Who | What they are actually for |
|---|---|---|
| Rhyme clearance | Human | Verify public domain against a real printed source |
| Script + copy | Agent, human confirms | Nothing scripts can catch is the whole risk |
| Frame review | **Human** | Scripts cannot see a six-fingered hand or an unsettling smile |
| Safety + quality | **Human** | The parent test: would you be glad they watched it? |
| Upload | **Human** | Verify Made for Kids actually took effect |
| Post-publish | Human | Log it; watch for claims and strikes |

---

## Maintenance

```bash
python3 compliance/fetch_compliance.py --check     # stale or drifted? exit 1 if so
python3 compliance/fetch_compliance.py --refresh   # re-download, diff, report
```

**Every 90 days**, re-fetch the law, read the YouTube policy pages at source, update `/compliance/`, and
log it in `audit/CHANGELOG.md`. Overdue by 1–30 days, every command warns. **Overdue by more than 30 days,
the pipeline stops.**

This is not bureaucracy. The FTC amended the COPPA Rule in April 2025 with full compliance required by
**April 22, 2026** — a channel running on pre-2025 assumptions would have been out of compliance without
changing a line of its own process.

> **Before relying on this in production, run `--refresh` once from a machine with open internet access.**
> The verbatim texts here came through provenance-tracked mirrors because the government sites were blocked
> by the build environment's network policy. They were checked against known citations, but *checked* is
> not *authoritative*. See [`audit/CHANGELOG.md`](audit/CHANGELOG.md) for the full, honest list of
> limitations.

---

## Repository layout

```
├── README.md                    this file
├── QUICKSTART.md                exact steps for your first compliant video
├── AGENT_RULES.md               the agent's operating contract — load as system prompt
├── compliance/                  the law shelf, read before anything generates
│   ├── rules.json               7 non-negotiables, machine-readable
│   ├── fetch_compliance.py      the 90-day refresher
│   ├── source_text/             VERBATIM law + provenance + SHA-256
│   └── *.md                     restatements applied to this channel
├── scripts/                     generation, gated
├── video/                       prompts, scene templates, frame review
├── music/                       clearance tracker + evidence
├── review/                      THE HUMAN GATE
├── publishing/                  upload checklist, metadata, scheduling
└── audit/                       decisions, changelog, 90-day tracker, published index
```

---

## Not legal advice

This is a working compliance system, not a lawyer. It is built to make the safe path the easy path and to
make uncertainty **visible** rather than silent — that is what the FLAG state is for throughout. Where the
stakes are real, do what the agent rules already require: **flag it and escalate to qualified counsel.
Do not guess.**

# AI Disclosure and Labeling

> **Document type: RESTATEMENT with official source.**
> Authoritative: <https://support.google.com/youtube/answer/14328491>
> Read the live page — this restatement is not a substitute for it.
> Last reviewed: 2026-09-03 · Next review: 2026-12-02

---

## The rule this implements

> **NN-7: Photorealistic AI content must carry the required AI label; cartoon-style does not, but still
> gets the kids setting.**

YouTube requires creators to disclose when content is **altered or synthetic** *and* could be mistaken for
a real person, place, or event. The disclosure is a toggle in the upload flow (Altered content), and
YouTube surfaces a label from it — in the expanded description for most content, and more prominently on
the video itself for sensitive topics.

**The test is realism, not tooling.** "Did I use AI?" is the wrong question. The right question is:

> **Could a reasonable viewer think this actually happened, or that this is a real person or place?**

---

## Decision table for this channel

| What we made | Disclosure? | Made for Kids? | Why |
|---|---|---|---|
| 2D/3D cartoon animation, stylized characters | **No** | **Yes** | Obviously animated. Nobody mistakes it for reality. |
| Storybook / painterly illustration | **No** | **Yes** | Clearly an artistic rendering. |
| Puppet or claymation *style* | **No** | **Yes** | Clearly stylized. |
| **Photorealistic** children, adults, or animals | **YES** | **Yes** | Could be mistaken for real people or real animals. |
| **Photorealistic** real-world locations | **YES** | **Yes** | Could be mistaken for a real place. |
| A synthetic voice that sounds like a real, identifiable person | **YES** | **Yes** | Synthetic likeness of a real person. |
| Generic sung vocals, clearly performed for the piece | **No** | **Yes** | Not an imitation of an identifiable person. |
| Minor edits: color grading, cropping, cleanup, denoising | **No** | **Yes** | Explicitly outside the disclosure requirement. |

Note the second column never changes. **The kids setting is unconditional (NN-1); only the AI label is
conditional.** Confusing the two is the most common error here.

## The house preference: stay in cartoon-style

The agency's default is stylized animation, and that is a deliberate risk decision rather than an aesthetic
one:

- It removes the disclosure question entirely.
- **It removes the uncanny-valley failure mode.** Photorealistic AI generation of *children* is precisely
  where "warped faces, extra limbs" (NN-4) becomes genuinely disturbing rather than merely wrong, in front
  of the audience least equipped to handle it. A six-fingered cartoon hand is a bug. A photorealistic child
  with a melting face is a safeguarding incident.
- It sidesteps any question of resembling a real, identifiable child.

**Photorealistic depiction of children is FLAG-by-default in this agency.** It requires named human
sign-off with a written reason in `audit/decision_log.csv` before generation, not after.

---

## How the pipeline enforces this

`scripts/compliance_gate.py` reads `visual_style` from the project brief. When it is `photorealistic`, the
gate requires `metadata.altered_content_disclosed == true` and **fails the publish package without it**
(machine check for NN-7 in `rules.json`).

The upload checklist carries the human-side verification, because the toggle is set in YouTube Studio and
no script can confirm it was actually flipped. See
[`../publishing/youtube_upload_checklist.md`](../publishing/youtube_upload_checklist.md).

---

## Disclosure is not a penalty

Creators avoid the toggle believing it suppresses reach. **Do not treat it as a cost to be minimized.**
The label is a fraction of the cost of a strike for undisclosed synthetic content, and the reputational
damage for a *children's* channel caught doing it is materially worse than for a general-audience one.
When the answer is genuinely unclear: **disclose, or change the style so the question disappears.**
Never resolve the ambiguity by staying silent — that is guessing, and the agent rules forbid it.

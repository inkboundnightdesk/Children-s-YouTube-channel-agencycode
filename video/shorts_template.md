# Shorts Template

A Short is **not** a trimmed long video. Different aspect, different attention curve, different job.
`scripts/rhyme_generator.py --format short` builds this shape.

## Specification

| Property | Value |
|---|---|
| Aspect | **9:16 vertical** (1080×1920) |
| Runtime | **20–55 s** (the generator targets ~28 s) |
| Scenes | 3 — hook, verse, loop-close |
| Thumbnail | 1080×1920 |
| Audience setting | **Made for Kids** — identical to long form, no exceptions |

## Structure

| # | Scene | Duration | Job |
|---|---|---|---|
| 1 | **Hook** | ~4 s | Straight into motion. No logo, no title card, no wind-up. |
| 2 | **Verse** | ~18 s | One continuous action. The single strongest verse. |
| 3 | **Loop-close** | ~6 s | Return to the exact opening framing so the loop is seamless. |

## The three rules that matter

**Keep the lower fifth of frame clear.** YouTube's Shorts UI — title, channel handle, action buttons —
sits over it. Anything you put there is covered. The generated SVG thumbnail marks this zone with a
dashed guide.

**Compose for the upper two thirds.** Subject centred and large. A Short is watched on a phone held at
arm's length, often one-handed.

**Build it to loop.** Shorts replay automatically. If the last frame matches the first, the loop is
invisible and watch time compounds. If it snaps, every repeat is a jolt — and for this audience, a
jolt every 28 seconds is genuinely unpleasant.

## What does not change

Everything in the compliance stack applies identically:

- Made for Kids on every Short (**NN-1**)
- No CTA — the features do not exist and the ask is inappropriate regardless (**NN-2**)
- 100% of frames reviewed, same three passes (**NN-4**)
- Music cleared with a tracker row (**NN-5**)
- Stylised, so no AI disclosure needed (**NN-7**)

A Short being 28 seconds does not make its review optional. Shorter footage means *less* review time,
not *no* review time — budget ~14 minutes each.

## What is never a Short

**Lullabies.** `hush_little_baby` and `rock_a_bye` are marked `formats: ["long"]` in the library and the
generator refuses `--format short` for them. A 20-second lullaby is not a lullaby — the entire function
of the form is the slow wind-down, and compressing it produces something that just sounds rushed.

## Not a duplicate — but only if the treatment differs

`duplicate_detection.py` treats a Short and a long video of the same rhyme as different products, and
discounts the structure and look scores accordingly.

**That discount does not cover a straight reskin.** Same rhyme, same setting, same palette, same
companion, just cropped to vertical, still scores ~0.60 and **blocks**. Give a Short its own setting,
palette and companion — the bulk scheduler already rotates all three independently of the title.

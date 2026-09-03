# Scene Template

The house structure for a nursery-rhyme video. `scripts/rhyme_generator.py` builds this shape
automatically; this is the reference, and the place to look when you want to break the pattern
deliberately.

## Standard structure

| # | Scene | Duration | Purpose |
|---|---|---|---|
| 1 | **Open** | ~10s | Establish the world. Introduce the companion. Set a calm tone. |
| 2..n | **Verse** | ~22s each | One verse of the rhyme, one clear action per scene |
| n+1 | **Learn** | ~18s | The teaching beat — one idea, plainly shown |
| n+2 | **Reprise** | ~22s | The rhyme once more, slower and softer |
| n+3 | **Close** | ~8s | Settle, dim, fade. No call to action. |

**Typical runtime: 90–150 seconds.** Short is correct for this audience. Resist padding to hit an
arbitrary length — watch time bought with filler is worse than a shorter video that holds attention.

## Why there is no call to action

There is nothing to call to. Made-for-Kids disables comments, notifications, playlists, end screens and
cards. And engagement bait aimed at children is a child-safety problem, not a style problem. The generator
does not produce a CTA and the compliance gate blocks one if you write it by hand.

## Varying the structure — required, not optional

**NN-3 forbids template farms, and this template is exactly the thing that becomes one.** If every video
is `open / verse / verse / learn / reprise / close` with a 102-second runtime, `duplicate_detection.py`
will start flagging on structure alone — and it will be right.

Deliberately vary, video to video:

- **Scene count and verse count** — some rhymes carry four verses, some carry one
- **Where the teaching beat sits** — middle or end, not always penultimate
- **Runtime** — a 75-second video and a 150-second video are different products
- **Whether there is a reprise at all**
- **The arc** — a narrative rhyme (*Mary Had a Little Lamb*) wants a story shape; a cumulative one
  (*Old MacDonald*) wants a building shape

## Per-scene fields

Every scene in `script.json` carries:

```json
{
  "n": 1,
  "kind": "open",
  "duration_s": 10,
  "visual": "what the camera sees",
  "narration": "spoken or [SUNG] line",
  "on_screen_text": "overlay text, added in the editor - NEVER generated in-frame"
}
```

## Pacing rules for preschool

- **Hold shots.** Minimum ~4 seconds. Under 2 seconds is too fast for this audience.
- **One action per scene.** Two simultaneous events do not parse.
- **Slow camera moves only.** No whip pans, no fast zooms.
- **No strobing.** Nothing above ~3 flashes per second — this is a seizure risk, not a style note.
- **Silence is allowed.** Let a moment land before moving on.
- **Repetition is a feature.** It is how small children learn, and it is why the reprise exists.

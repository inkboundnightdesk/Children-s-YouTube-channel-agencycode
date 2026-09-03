# AI Video Prompt Library

Prompts for a preschool audience, written to fail safely. `scripts/pipeline.py` builds per-scene prompts
automatically from a script — this file is the reference behind them, and what you edit when you want to
change the house look.

**Generated prompts are not approved output.** Everything that comes back goes through
[`frame_review_checklist.md`](frame_review_checklist.md), 100% of frames, before it enters an edit.

---

## The house style block

Append to every prompt. Consistency across videos is what makes a channel look like a channel rather than
a pile of renders — and the stylised look is also what keeps us out of the AI-disclosure requirement
(NN-7) and away from uncanny-valley failures.

```
cartoon style, soft rounded shapes, gentle diffused lighting, flat storybook illustration,
friendly and calm, generous negative space, simple uncluttered composition, slow camera,
warm and reassuring mood, hand-drawn feel, matte finish
```

Then the per-video palette, e.g. `palette of deep indigo, soft gold, cream`.

## The negative prompt — non-optional

**Attach this to every single generation.** It is the first line of defence for NN-4, and it costs nothing.

```
extra limbs, extra fingers, six fingers, malformed hands, deformed hands, warped face,
melting features, asymmetric eyes, misaligned eyes, distorted anatomy, extra heads,
fused bodies, garbled text, misspelled words, gibberish letters, random symbols,
watermark, signature, logo, brand marks, trademarked characters,
photorealistic child, realistic human child, uncanny valley, hyperrealistic skin,
horror, gore, blood, injury, weapons, knives, guns, darkness, menacing shadows,
scary expression, creepy smile, staring eyes, lurking figure,
sexualised, adult themes, alcohol, smoking,
crowds, chaotic composition, fast strobing, flashing lights, harsh saturation
```

The negative prompt reduces failures. **It does not eliminate them.** Review every frame anyway.

---

## Scene prompts by type

### Establishing / opening
```
Wide gentle establishing shot of {SETTING}. Soft morning light. {COMPANION} enters slowly
from the left and settles. Nothing else moves. Calm, spacious composition.
[house style] [palette] Camera: very slow push in.
```

### Verse / action
```
{CHARACTER} performing {SIMPLE_ACTION} in {SETTING}. One clear action, centre frame,
nothing else competing for attention. {COMPANION} joins the motion gently.
[house style] [palette] Camera: locked off or very slow drift.
```

### Teaching beat
```
Simple, uncluttered frame showing {ONE_CONCEPT}. A single subject on a plain background,
generous empty space around it. No competing detail.
[house style] [palette] Camera: locked off.
```
> Leave physical space in the composition for the text overlay you will add in the editor.
> **Never generate the words inside the frame.**

### Closing
```
{COMPANION} settling down to rest in {SETTING}. Light dimming gently to a warm glow.
Peaceful, still, safe. Slow fade.
[house style] [palette] Camera: static, slow fade to black.
```

---

## Rules for writing prompts

**One action per scene.** Preschoolers cannot parse two simultaneous events, and models render multiple
actions badly. Both problems, one fix.

**Name the camera move, and keep it slow.** Unspecified camera work produces music-video energy — wrong
for the audience and a review failure.

**Describe light explicitly.** "Soft morning light", "warm lantern glow". Left unspecified, models reach
for dramatic contrast, which reads as menacing to a small child.

**Never generate text in-frame.** Every model garbles it. Compose for an overlay and add words in the
editor. This is a workflow rule, not a preference.

**Avoid close-ups on faces and hands.** Both are where artefacts live. Mid and wide shots hide far more
than they lose, and suit the calm pacing anyway.

**Say what is in the background.** "Plain sky", "simple green field". Unspecified backgrounds are where
hallucinated logos, faces, and text appear.

**Never name another channel's IP** — not in the prompt, not as a style reference, not as "in the style
of". `compliance/rules.json` lists the brands; the gate blocks them in copy, but a prompt is on you.

**Do not prompt for photorealistic children.** House rule. FLAG-by-default, and it needs a named human's
written reason before generation, not after.

---

## Common failures and the fix

| Symptom | Fix |
|---|---|
| Warped or extra fingers | Avoid hand close-ups; mid-shot; strengthen hand negatives; regenerate |
| Character drifts between shots | Fix the seed; describe the character identically every time; use image-to-image |
| Gibberish text appears | Add "no text, no letters, no signage" positively; overlay in the editor |
| Unsettling / uncanny expression | Add "gentle relaxed expression"; move further from photorealism |
| Background too busy | "Simple uncluttered background, generous negative space" |
| Too dark or moody | Name the light source explicitly; add "bright, warm, airy" |
| Hallucinated logos on props | Describe props plainly; add "unbranded, plain, no logos" |

---

## Tool notes

Whatever generator you use, record **which tool, which model version, and its commercial-use terms as of
the date you used it** in the project folder. AI service terms change, and a screenshot dated to the
session is worth far more later than a remembered impression. Some services claim rights over output or
restrict commercial use — **read the terms before the render, not after.**

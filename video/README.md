# /video/ — Prompts In, Reviewed Frames Out

| File | Purpose |
|---|---|
| [`prompt_library.md`](prompt_library.md) | House style, the mandatory negative prompt, per-scene patterns |
| [`scene_template.md`](scene_template.md) | The standard structure — and how to vary it so it never becomes a template farm |
| [`frame_review_checklist.md`](frame_review_checklist.md) | The 100%-of-frames human review. **NN-4 lives here.** |

## Where this sits

```
script.json  ->  pipeline builds video_prompts.json  ->  YOU generate frames
                                                             |
                                                             v
                                              frame_review_checklist.md (100%)
                                                             |
                                                             v
                                                  review/safety_checklist.md
```

The pipeline writes `build/<ref>/video_prompts.json` with the negative prompt attached to every scene,
then **stops**. Generation happens in your AI video tool, and review happens in a human's eyes. Neither is
something this repository does for you, and no flag skips the review.

## The three rules people break

1. **Review every frame.** Not a sample, not keyframes. Artefacts appear and vanish within a few frames.
2. **Never generate text inside a frame.** Every model garbles it. Compose space for an overlay; add words
   in the editor.
3. **Stay stylised.** Cartoon output removes the AI-disclosure question (NN-7) *and* removes the
   uncanny-valley failure mode. Photorealistic children are FLAG-by-default and need a named human's
   written reason before generation.

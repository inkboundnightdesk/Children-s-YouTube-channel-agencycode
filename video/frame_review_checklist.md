# Frame Review Checklist

> **NN-4: All AI output is human-reviewed for warped faces, extra limbs, garbled text, unsafe or creepy
> visuals.**
>
> **There is no sampling clause. 100% of generated frames.** A checkpoint every two seconds is not review —
> AI artefacts appear and vanish within a few frames, and the one you skipped is the one that ends up in a
> screenshot.

**Reviewer:** ________________  **Ref:** ____________  **Date:** __________
**Frames generated:** ______  **Frames reviewed:** ______  *(these must be equal)*

---

## How to actually do this

1. Export the render as an image sequence, or scrub at **0.25× speed**. Full speed hides everything.
2. Watch **once for anatomy**, **once for text**, **once for tone.** Three passes beat one careful one —
   you cannot hold all three failure modes in your head at the same time.
3. **Any single FAIL kills the frame.** Regenerate or cut. Do not "fix it in the grade", do not decide it
   is "only a few frames", and do not talk yourself into it because the render took forty minutes.

---

## 1. Anatomy and faces

- [ ] **Hands: count the fingers.** Every visible hand, every frame. Five. This is the single most common
      AI failure and the most noticeable to an adult viewer.
- [ ] **Limbs: count them.** No extra arms or legs, no limbs merging into bodies or backgrounds.
- [ ] **Faces are stable** across the shot — eyes stay the same size, colour and spacing; features do not
      drift, melt, or slide between frames.
- [ ] **Eyes point the same way.** Both of them. No dead, misaligned, or vacant stares.
- [ ] **Mouths and teeth are correct** — no extra rows, no teeth in profile where there should be none.
- [ ] **Character identity holds** shot to shot. The same character is recognisably the same character.
- [ ] **Animals have the right number of legs, ears, eyes and tails.**
- [ ] **No body-horror at any scale** — melting, fusing, duplicated heads, figures growing out of others.

## 2. Text

- [ ] **Any text in the frame is real, spelled correctly, and legible.** AI models produce convincing
      gibberish; read every word out loud.
- [ ] **No accidental text** in backgrounds — signage, book spines, labels, packaging.
- [ ] **No watermarks, signatures, or logos** hallucinated by the model.
- [ ] **On-screen words were added in the editor as an overlay**, not generated inside the frame.
      *(If any generated frame contains title text, that is a process failure — go fix the process.)*

## 3. Safety and tone — the part that matters most

Read these as a parent would, not as the person who made it.

- [ ] **Nothing creepy.** No uncanny stares, no unsettling smiles, no figures lurking in backgrounds.
- [ ] **Nothing frightening.** No looming shadows, menacing shapes, sudden darkness, or threat.
- [ ] **No violence, weapons, blood, injury, or peril.** Including cartoon peril and including things that
      only *look* like weapons.
- [ ] **No adult themes.** Nothing sexualised, nothing romantic, no substances, no innuendo.
- [ ] **No distress.** Characters are not crying, panicking, trapped, alone, or abandoned.
- [ ] **No "Elsagate" pattern** — nothing that pairs a children's surface with disturbing content. This is
      a child-safety violation and a channel-termination event, not a gray area.
- [ ] **Children depicted are stylised, never photorealistic** (see NN-7). Photorealistic children are
      FLAG-by-default and need a written, named sign-off before generation.
- [ ] **No real, identifiable person's likeness.**
- [ ] **No third-party characters, brands, logos or trade dress** — check backgrounds and merchandise
      especially; models love to hallucinate a Mickey silhouette onto a toy shelf.

## 4. Motion and sensory safety

- [ ] **No strobing or rapid flashing.** Nothing above ~3 flashes/second — this is a seizure risk.
      Take it seriously.
- [ ] **No aggressive camera moves**, whip pans, or violent zooms.
- [ ] **Cuts are slow.** Preschool pacing: hold shots, let things breathe.
- [ ] **No high-frequency flicker** between frames.
- [ ] **Colour is not oversaturated** to the point of harshness.

## 5. Continuity

- [ ] Palette matches the brief across every scene.
- [ ] Lighting direction is consistent within a scene.
- [ ] Props and set dressing do not pop in and out between frames.
- [ ] Backgrounds are stable — no boiling, crawling, or morphing textures.

---

## Verdict

- [ ] **PASS** — every frame reviewed, no failures. Proceed to `../review/safety_checklist.md`.
- [ ] **FIX** — listed frames regenerated and re-reviewed from the top. *(A re-review is a full review.)*
- [ ] **REJECT** — the render is not salvageable. Back to prompts.

**Frames rejected:** ______  **Reason(s):**

_______________________________________________________________________________

**Signature:** ________________  **Date:** __________

> Record the outcome:
> ```
> python3 scripts/audit_log.py --stage review --decision PASS \
>   --reason "Frame review complete, 100% reviewed, no failures" \
>   --actor "<your name>" --ref <REF>
> ```

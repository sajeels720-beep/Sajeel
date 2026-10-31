# Voiceover parts and file names

The voiceover is made in ElevenLabs in four parts, all by the narrator. Generate each part on its own with the same voice and settings, download it and name it as shown (ElevenLabs' `.mp3` is fine; `.wav` also works). Put them all in `videos/wrinkly-fingers/audio/`. The edit splits each part at its pauses and fits the shots to your recording, so the times are a guide, not a rule.

## ElevenLabs settings

- **Voice:** the same narrator voice and settings as videos 1 and 2, so the channel sounds the same. Don't clone a real person's voice without their permission.
- **Model:** Eleven v4 or Eleven v3, or Eleven Multilingual v2 for the steadiest read. The text below has no audio tags or capitals: those tend to overact, and the punctuation already sets the pace (`...` and line breaks are the pauses).
- **Stability:** on v4 or v3, use **Robust** (or about 65–75%) so it stays natural; on Multilingual v2, about 55–60% with Style at 0. **Similarity** about 75%, **speed** about 1.05–1.1 (brisk, about 2.9 words a second).
- If one word needs more punch, write just that word in capitals. If a part still sounds overacted, generate it two or three times and keep the most natural take.
- **Licence:** the free plan has no commercial licence and needs ElevenLabs credited. For a monetized channel, use the Starter plan or above.

## The parts

### `voiceover_1`: the hook (0.0–7.6 s, shots 1–5)

Lazy and summery at first, a little grossed out on "wrinkly raisins", then a sly twist.

```
You stay in the pool too long,
and your fingers turn into wrinkly raisins.
It's not just the water...
It's your nerves.
```

### `voiceover_2`: how it works (8.0–16.1 s, shots 6–11)

"Here's the secret", then brisk and punchy, a little squeamish on "crumples".

```
You see, water sets off your nerves,
which squeeze the blood vessels under your skin.
Your fingertips shrink,
and the skin crumples into wrinkles.
```

### `voiceover_3`: the question (16.5–21.0 s, shots 12–14)

Puzzled on "But why?", then pleased with the answer.

```
But why?
Scientists think wrinkles grip wet things better... like tyre treads.
```

### `voiceover_4`: the payoff (21.4–24.2 s, shots 15–16)

Warm and proud, with a smile.

```
So those raisin fingers?
Built-in rain tyres.
```

## Timing notes

- The short gaps at 4.8–5.1, 7.6–8.0, 16.1–16.5 and 21.0–21.4 s are deliberate beats: before "It's not just the water", "You see", "But why?" and "So those raisin fingers?". The first is the line break inside `voiceover_1`; the others fall between the parts.
- 24.2–25.0 s has no voice: he leans back with a happy sigh (`sfx_sigh` in `SOUND_EFFECTS.md`) and the music ends on its button.
- A little silence at the start or end of a file is fine; it gets trimmed.
- If a part sounds wrong, generate just that part again. Made everything in one go instead? Name it `voiceover_full`.

# Voiceover parts and file names

The voiceover is made in ElevenLabs in six parts: five for the narrator and one for her sneeze. Generate each part on its own with the same voice and settings, download it and name it as shown (ElevenLabs' `.mp3` is fine; `.wav` also works). Put them all in `videos/sneeze/audio/`. The edit splits each part at its pauses and fits the shots to your recording, so the times are a guide, not a rule.

## ElevenLabs settings

- **Model:** Eleven v4, or Eleven v3. Both read the `[bracket]` audio tags. Neither reads `<break>` tags, so the pauses come from `...`, line breaks and `[pause]`.
- **Voice:** a friendly, upbeat narrator from the Voice Library, the same one for every part. Don't clone a real person's voice without their permission.
- **Stability** about the middle (Natural, or 50%), **similarity** about 75%, **speed** about 1.05–1.1 (brisk, about 2.7 words a second).
- **Capitals** mark the stressed words. If one comes out shouted, put it back in lowercase and generate again.
- **Licence:** the free plan has no commercial licence and needs ElevenLabs credited. For a monetized channel, use the Starter plan or above.

## The parts

### `voiceover_1`: the hook (0.0–7.5 s, shots 1–5)

Casual and teasing, then dry and ominous on "Big mistake".

```
[curious] You feel a GIANT sneeze coming...
so you pinch your nose, shut your mouth, and hold it in.
[pause] Big... [ominous] mistake.
```

### `voiceover_2`: what happens (7.9–18.2 s, shots 6–11)

"Here's the secret", then punchy, building up to "twenty times".

```
[excited] You see, a sneeze BLASTS air out of your lungs super fast.
With nowhere to go, it gets trapped inside you,
and the pressure in your airways jumps about TWENTY times higher.
```

### `voiceover_3`: ears and eyes (18.2–25.6 s, shots 12–16)

Fast, sharp on "burst" and "pop", a little grossed out at the end.

```
[urgent] That air shoots up the tiny tubes to your ears,
and can BURST your eardrums,
or POP the blood vessels in your eyes.
```

### `voiceover_4`: the twist (26.0–30.0 s, shots 17–18)

Serious.

```
[serious] But, in rare cases... it can even tear a hole in your throat.
```

### `voiceover_5`: the advice (30.0–33.6 s, shots 19–20)

Friendly, then warm, with a smile.

```
[warm] So next time you feel one coming...
[smiling] just let it out.
```

### `voiceover_6`: her sneeze (33.6–35.2 s, shot 21)

This is her (a young woman), not the narrator. Make it in ElevenLabs' **Sound Effects** (about 2 seconds), generate three or four and keep the best:

```
A young woman's big dramatic sneeze: two quick gasping breaths in, "ahh... ahh...", then a loud "CHOO!", close up, dry, no background noise
```

Optional: a small relieved sniff for shot 22, named `sfx_sniff`.

## Timing notes

- The short gaps at 6.0–6.3, 7.5–7.9 and 25.6–26.0 s are deliberate beats before "Big mistake", "You see" and "But". The first is the `[pause]` inside `voiceover_1`; the other two fall between the parts.
- Shot 22 (35.2–37.0 s) has no voice: just the seeds floating away and the music ending.
- The sneeze in the animation: her mouth opens for "ahh..." at 32.8 s and "AHH..." at 33.4 s (under "just let it out"), the big breath in peaks at 33.8 s, and her head snaps forward on the **CHOO at 34.2 s**. She sniffs at 36.1 s. You don't need to time anything: the edit lines the sneeze up with her.
- A little silence at the start or end of a file is fine; it gets trimmed.
- If a part sounds wrong, generate just that part again. Made everything in one go instead? Name it `voiceover_full`.

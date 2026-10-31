# Voiceover parts and file names

The voiceover is made in ElevenLabs in six parts: five for the narrator and one for her sneeze. Generate each part on its own with the same voice and settings, download it and name it as shown (ElevenLabs' `.mp3` is fine; `.wav` also works). Put them all in `videos/sneeze/audio/`. The edit splits each part at its pauses and fits the shots to your recording, so the times are a guide, not a rule.

## ElevenLabs settings

- **Model:** Eleven v4 or Eleven v3, or Eleven Multilingual v2 for the steadiest read. The text below has no audio tags or capitals: those tend to overact, and the punctuation already sets the pace (`...` and line breaks are the pauses).
- **Voice:** a friendly, upbeat narrator from the Voice Library, the same one for every part. Don't clone a real person's voice without their permission.
- **Stability:** on v4 or v3, use **Robust** (or about 65–75%) so it stays natural; on Multilingual v2, about 55–60% with Style at 0. **Similarity** about 75%, **speed** about 1.05–1.1 (brisk, about 2.7 words a second).
- If one word needs more punch, write just that word in capitals. If a part still sounds overacted, generate it two or three times and keep the most natural take.
- **Licence:** the free plan has no commercial licence and needs ElevenLabs credited. For a monetized channel, use the Starter plan or above.

## The parts

### `voiceover_1`: the hook (0.0–7.5 s, shots 1–5)

Casual and teasing, then dry on "Big mistake".

```
You feel a giant sneeze coming...
so you pinch your nose, shut your mouth, and hold it in.
Big... mistake.
```

### `voiceover_2`: what happens (7.9–18.2 s, shots 6–11)

"Here's the secret", then punchy, building up to "twenty times".

```
You see, a sneeze blasts air out of your lungs super fast.
With nowhere to go, it gets trapped inside you,
and the pressure in your airways jumps about twenty times higher.
```

### `voiceover_3`: ears and eyes (18.2–25.6 s, shots 12–16)

Fast, sharp on "burst" and "pop", a little grossed out at the end.

```
That air shoots up the tiny tubes to your ears,
and can burst your eardrums,
or pop the blood vessels in your eyes.
```

### `voiceover_4`: the twist (26.0–30.0 s, shots 17–18)

Serious.

```
But, in rare cases... it can even tear a hole in your throat.
```

### `voiceover_5`: the advice (30.0–33.6 s, shots 19–20)

Friendly, then warm, with a smile.

```
So next time you feel one coming...
just let it out.
```

### `voiceover_6`: her sneeze (33.6–35.2 s, shot 21)

This is her (a young woman), not the narrator. Make it in ElevenLabs' **Sound Effects** (about 2 seconds), generate three or four and keep the best:

```
A young woman's big dramatic sneeze: two quick gasping breaths in, "ahh... ahh...", then a loud "CHOO!", close up, dry, no background noise
```

Optional: a small relieved sniff for shot 22, named `sfx_sniff`.

## Timing notes

- The short gaps at 6.0–6.3, 7.5–7.9 and 25.6–26.0 s are deliberate beats before "Big mistake", "You see" and "But". The first is the line break inside `voiceover_1`; the other two fall between the parts.
- Shot 22 (35.2–37.0 s) has no voice: just the seeds floating away and the music ending.
- The sneeze in the animation: her mouth opens for "ahh..." at 32.8 s and "AHH..." at 33.4 s (under "just let it out"), the big breath in peaks at 33.8 s, and her head snaps forward on the **CHOO at 34.2 s**. She sniffs at 36.1 s. You don't need to time anything: the edit lines the sneeze up with her.
- A little silence at the start or end of a file is fine; it gets trimmed.
- If a part sounds wrong, generate just that part again. Made everything in one go instead? Name it `voiceover_full`.

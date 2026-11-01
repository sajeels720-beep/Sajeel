# Why Do Your Fingers Wrinkle In Water? 💦

Video 3: a vertical Short of 25 seconds (750 frames at 30 fps) in the style of Zack D. Films, built from Python scripts that drive Blender. Each script builds its shot (set, character, animation, lights, camera, compositing) from scratch in an empty file.

- `SCRIPT_AND_SHOTS.md`: the voiceover script with timings, the sources, and the 16-shot plan.
- `MASTER_PROMPT.md`: your master prompt for this video.
- `shots/`: one script per shot, all 16.
- `scenes/`: shared sets and acting.
  - `pool_set.py`: the sunny backyard pool (Poly Haven "Pool" HDRI with a bluer sky, mosaic tiles with dancing light patterns, the stone edge and deck, the water, the rubber duck, the marble), plus the time-lapse controls, ripples, falling drops, palm-frond shadows and the lights.
  - `swimmer.py`: the new character, wet, in a red Jay3Dfilms swim shirt.
  - `wrinkles.py`: the wrinkles that grow on his fingertips (real geometry in the close-ups).
  - `pool_acting.py`: placing and posing him in the pool (arms, hands, face and body over time).
  - `opening_take.py`: his performance for shots 1–3, animated as one take so the acting carries across the cuts.
  - `hand_set.py`: his hand alone on the studio blue for shots 4–5 (open, palm up): the drops that soak in, his red "?", and the X-ray (glass skin, bones and nerves fitted inside his hand).
  - `skin_macro.py`: shot 6, the fingerprint ridges up close, with sweat pores and drops of water draining into them.
  - `finger_inside.py`: shots 7–8 inside the fingertip (the warm tissue backdrop of videos 1 and 2): the nerve ending sparks, a pulse races down the nerve, the vessels squeeze and the blood cells slow.
  - `cutaway.py`: shots 9–10, the fingertip cut in half like a textbook: the vessels drain, the pad shrinks and the skin buckles.
  - `tyre_set.py`: shot 14, a rain tyre (modelled, no logos) on an alloy wheel rolling through water on a strip of wet road.
  - `closing_take.py`: his performance for shots 12–16 as one take: the baffled squint, the underwater grab of the marble, holding it up to the sun, the toss and the lean back at sunset.
- `previews/`: test images and preview clips from each step.
- `VOICEOVER.md` and `SOUND_EFFECTS.md`: the voiceover parts and every sound to make in ElevenLabs, with file names, prompts and where each goes.
- `timeline.py`, `assemble_cut.py` and `mix_audio.py`: the edit (as for video 2). The picture is fixed, so each voiceover part is split at its pauses and every phrase starts on its cue in the picture. `assemble_cut.py` joins the shots and burns in the captions; `mix_audio.py` adds the voice, sound effects and music and sets the loudness to YouTube level.

## One-time setup

The same as videos 1 and 2. If you already ran `videos/production/setup_assets.py`, there is nothing to do. The first time a shot is built, it downloads the Poly Haven files it needs (about 40 MB: the pool HDRI, tile, stone and fabric textures, the rubber duck) into your `vfx_assets` folder; after that it works offline.

## Render a shot

Shots render with EEVEE at 1080×1920, 64 samples, with motion blur. Each script writes PNG frames to `videos/wrinkly-fingers/renders/<shot>/`. Frames that already exist are skipped, so an interrupted render simply continues when you run it again.

In PowerShell, from the repository folder (`C:\Users\asc\Sajeel`):

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P videos\wrinkly-fingers\shots\shot01_lounge.py -a
```

All shots in a loop:

```powershell
Get-ChildItem videos\wrinkly-fingers\shots\shot*.py | ForEach-Object { & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P $_.FullName -a }
```

To look at a shot in Blender instead: start a new file (File > New > General), then in the Python Console:

```python
import runpy
runpy.run_path(r"C:\Users\asc\Sajeel\videos\wrinkly-fingers\shots\shot01_lounge.py", run_name="__main__")
```

## Build the final video

Make the voiceover and the sounds first (`VOICEOVER.md`, `SOUND_EFFECTS.md`) and put the files in `videos/wrinkly-fingers/audio/`. This needs Python 3 and ffmpeg on your PATH (on Windows, type `py` instead of `python3`). Once every shot is rendered, run these two commands from the repository folder:

```bash
python3 videos/wrinkly-fingers/assemble_cut.py videos/wrinkly-fingers/renders wrinkles_captions.mp4 --captions --voiceover videos/wrinkly-fingers/audio
python3 videos/wrinkly-fingers/mix_audio.py videos/wrinkly-fingers/audio wrinkles_captions.mp4 wrinkles_final.mp4
```

The first joins the 16 shots (every frame as rendered) and burns in the caption style: 2–4 white bold words at about 72% height, each group coming up as it is spoken, with no punctuation. The second puts every voiceover phrase on its cue, lines up the sound effects, fits the music's last hit to the moment he leans back, dips the music under the voice and sets the loudness YouTube expects (-14 LUFS). `wrinkles_final.mp4` is the finished Short. For a version without captions, leave out `--captions --voiceover videos/wrinkly-fingers/audio`.

## Credits (for the video description)

- Character: MPFB 2 with MakeHuman assets (CC0): skin, eyes, short hair, eyebrows, eyelashes, T-shirt (as the swim shirt), shorts, and the faceunits01 expression pack. No credit required.
- Poly Haven (CC0, no credit required): "Pool" HDRI, "Rounded Square Tiled Wall" and "Patio Tiles" textures, "Bi Stretch" fabric, "Rubber Duck Toy".
- Water, wrinkles, fingertip, marble, palm fronds, X-ray bones and nerves, skin ridges and pores, the inside of the finger, the cutaway, the tyre and wheel, and effects: modelled procedurally by the scripts.
- No CC-BY or non-commercial assets are used.
- Sources for the facts: listed in `SCRIPT_AND_SHOTS.md` (Wilder-Smith and Chow, Muscle & Nerve 2003; Wilder-Smith, Clinical Autonomic Research 2004; Changizi et al., Brain, Behavior and Evolution 2011; Kareklas, Nettle and Smulders, Biology Letters 2013; Davis, PLOS ONE 2021; Haseleu et al., PLOS ONE 2014).

## Preview vs final

Previews are rendered with Cycles on a CPU at reduced size (`SHOT_PREVIEW=1`). Without it, the scripts build the final EEVEE setup. The water has no refraction (a see-through surface with a Fresnel sheen), and the colour of things under it comes from an underwater tint in their materials, so EEVEE and Cycles look the same.

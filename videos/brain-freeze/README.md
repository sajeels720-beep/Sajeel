# Why Ice Cream Freezes Your Brain 🥶

A 36.8-second vertical Short in the style of Zack D. Films, built entirely from Python scripts that drive Blender. Every shot is reproducible: each script builds its scene, animation, lights, camera and compositing from scratch in an empty file.

- `SCRIPT_AND_SHOTS.md`: the voiceover script with timings and the shot plan.
- `shots/`: one script per shot (20 shots; shot 19 is split into 19a and 19b).
- `scenes/`: shared sets (ice cream, mouth interior, vessels, blood vessel tunnel, nerves, park bench, the protagonist, head cutaway, x-ray head).
- `assets/`: the logo-free T-shirt texture (derived from a CC0 MakeHuman asset).
- `assemble_cut.py`: edits the rendered shots into the final timeline; `mix_audio.py` adds the voiceover, sound effects and music; `timeline.py` holds the shared timing, so when a recorded line runs long, the shots, captions and sounds after it all move back together.
- `audio/`: your recorded voiceover lines (and later the sound effects and music).
- `VOICEOVER.md` and `SOUND_EFFECTS.md`: what to record and generate, with file names, times and levels.
- `../production/vfx_kit.py`: the video toolkit. `../production/setup_assets.py` is the one-time asset installer.
- `../MASTER_PROMPT.md`: your master prompt, revised for this style.

## One-time setup

1. Blender 4.2 or newer. The scripts were tested on Blender 5.2 (preview renders) and 4.5 LTS (every shot builds).
2. In Blender, open `videos/production/setup_assets.py` in the Scripting tab and press **Run Script**. It does three things:
   - installs the MPFB 2 character extension;
   - installs the CC0 MakeHuman asset packs (skins, hair, clothes, poses, face expressions);
   - downloads the NIH brain model.

   It needs internet and about 450 MB of downloads.
3. The Poly Haven sky and textures download automatically the first time a shot is built. They are saved to `~/vfx_assets` (set `VFX_ASSETS` to use a different folder).

**Your channel name on the T-shirt.** The shirt says "Jay3Dfilms", printed exactly as written, on the upper chest above the ice cream cup. To change it, set the environment variable `CHANNEL_NAME` before building (for example `CHANNEL_NAME="Brain Facts Daily"`), or edit `CHANNEL_NAME` near the top of `scenes/character.py`. The shirt colour is `SHIRT_COLOR` in the same file.

## Look at a shot in Blender

Start a new file (File > New > General). Then run the shot in the Python Console:

```python
import runpy
runpy.run_path(r"C:\path\to\Sajeel\videos\brain-freeze\shots\shot03_perfect.py", run_name="__main__")
```

Building takes 1–25 seconds. Scrub the timeline to see the animation, or press F12 to render the current frame.

## Final renders

The final look is EEVEE, 1080×1920, 30 fps, 64 samples, with motion blur. Each script writes PNG frames to `renders/<shot>/`:

```bash
# from the repository root; repeat for every script in videos/brain-freeze/shots/
blender -b -P videos/brain-freeze/shots/shot03_perfect.py -a
```

On Windows PowerShell, render all shots in a loop:

```powershell
Get-ChildItem videos\brain-freeze\shots\shot*.py | ForEach-Object { blender -b -P $_.FullName -a }
```

Render one frame first (F12) to measure the time per frame on your laptop, then multiply by the shot's frame count (1,104 frames in total). As a rough guide, EEVEE on a laptop with integrated graphics takes about 6–20 seconds per frame at 1080×1920 and 64 samples, which is about 2–6 hours for the whole Short (most likely 3–4), plus a minute or so per shot to load and compile shaders. The inside-the-mouth shots (8–12) and the character shots are the slowest; the nerve and vessel close-ups are the fastest. To roughly halve the time, set the render samples to 32.

Frames already rendered are skipped, so if a render stops (crash, sleep, closing the laptop), run the same command again and it continues. Delete a shot's folder in `renders/` to render that shot from scratch.

**Build the edit.** This needs Python 3 and ffmpeg on your PATH (on Windows, type `py` instead of `python3`):

```bash
python3 videos/brain-freeze/assemble_cut.py videos/brain-freeze/renders brain_freeze.mp4 --voiceover videos/brain-freeze/audio
```

Your voiceover recordings set the pace: every shot is fitted to the line it plays under, so the picture never freezes, and the still frames where a camera move eases in or out are left out at the cuts. Without `--voiceover`, the cut follows the planned script times. `--captions` burns in his caption style (2–4 white bold words at about 75% height).

**Add the sound.** Record the lines in `VOICEOVER.md` and make the sounds in `SOUND_EFFECTS.md`, put all the files in one folder (for example `videos/brain-freeze/audio/`), build the edit with `--voiceover` and that folder as above, then:

```bash
python3 videos/brain-freeze/mix_audio.py videos/brain-freeze/audio brain_freeze.mp4 brain_freeze_with_sound.mp4
```

It places every voiceover line, sound effect and loop at its time and level, dips the music under the voice and sets the loudness YouTube expects (-14 LUFS). Any file that is missing is simply left out.

**Captions in the final video.** Build the edit with burned-in captions that follow your recording (each group of words appears while it is spoken), then add the sound:

```bash
python3 videos/brain-freeze/assemble_cut.py videos/brain-freeze/renders brain_freeze_captions.mp4 --captions --voiceover videos/brain-freeze/audio
python3 videos/brain-freeze/mix_audio.py videos/brain-freeze/audio brain_freeze_captions.mp4 brain_freeze_final.mp4
```

## Shot list

| Shot | Time (s) | Voiceover | Script |
|---|---|---|---|
| 1 | 0.0–1.5 | You take a giant bite | `shot01_big_bite.py` |
| 2 | 1.5–3.0 | of ice cream, | `shot02_pov_spoon.py` |
| 3 | 3.0–5.6 | and for a second, it's perfect. | `shot03_perfect.py` |
| 4 | 5.6–7.0 | Then a stabbing pain | `shot04_pain_snap.py` |
| 5 | 7.0–8.4 | shoots through your forehead, | `shot05_forehead_cracks.py` |
| 6 | 8.4–11.0 | like your brain is freezing solid. | `shot06_brain_freeze.py` |
| 7 | 11.0–12.8 | You see, when something freezing | `shot07_xray_explainer.py` |
| 8 | 12.8–14.8 | hits the roof of your mouth, | `shot08_palate_frost.py` |
| 9 | 14.8–16.8 | the blood vessels in your head | `shot09_xray_vessels.py` |
| 10 | 16.8–18.8 | squeeze tight to hold in heat, | `shot10_squeeze.py` |
| 11 | 18.8–20.4 | then suddenly rush wide open | `shot11_rush_open.py` |
| 12 | 20.4–22.0 | to warm back up, | `shot12_warm_melt.py` |
| 13 | 22.0–23.8 | and that flood of blood | `shot13_blood_flood.py` |
| 14 | 23.8–25.9 | sets off pain sensors. | `shot14_pain_sparks.py` |
| 15 | 25.9–27.8 | But the nerve carrying that signal | `shot15_nerve_signal.py` |
| 16 | 27.8–29.6 | also runs to your forehead, | `shot16_forehead_branch.py` |
| 17 | 29.6–32.0 | so that's where your brain feels it, | `shot17_question.py` |
| 18 | 32.0–34.2 | leaving you with a frozen brain | `shot18_frozen_callback.py` |
| 19a | 34.2–35.4 | that isn't frozen | `shot19a_ice_shatters.py` |
| 19b | 35.4–36.8 | at all. | `shot19b_another_bite.py` |

## Credits (put these in the video description)

- Brain model: "Detailed Human Brain Model" by Schmidt's, NIH 3D (3DPX-021161), licensed CC BY.
- Character: MPFB 2 with MakeHuman assets (CC0): skin, eyes, hair, casual suit, shoes, sitting pose, and the faceunits01 expression pack.
- Sky and textures: Poly Haven, all CC0 ("Rooitou Park" HDRI, "Wood Table Worn", "Leafy Grass").
- Everything else (ice cream, mouth, vessels, blood cells, nerves, effects) is modelled procedurally by the scripts.

## Preview vs final

The preview renders were made with Cycles on a CPU at 34–50% size, with low sample counts, to check motion and timing. With `SHOT_PREVIEW=1` the scripts switch to that mode, and `../production/vfx_kit.py: fast_preview()` holds those settings. Without it they build the final EEVEE setup. Spot checks of shots 3 and 9 rendered in EEVEE matched the Cycles previews.

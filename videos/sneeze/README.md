# What Happens If You Hold In A Sneeze 🤧

Video 2: a vertical Short of about 37 seconds (1,110 frames at 30 fps) in the style of Zack D. Films, built from Python scripts that drive Blender. Each script builds its shot (set, character, animation, lights, camera, compositing) from scratch in an empty file.

- `SCRIPT_AND_SHOTS.md`: the voiceover script with timings, and the 22-shot plan.
- `VOICEOVER.md`: what to record, with file names and time slots.
- `SOUND_EFFECTS.md`: every sound effect, with an ElevenLabs prompt and where it plays.
- `MASTER_PROMPT.md`: your master prompt, revised for this video.
- `shots/`: one script per shot, 22 in all.
- `scenes/`: shared sets. `heroine.py` is the new character, `sky_set.py` the studio blue backdrop and lights, `dandelion_set.py` the dandelion and its seeds.
  - `acting.py` poses her arm and fingers (the nose pinch), and `hold_in.py` is her performance while she holds the sneeze in (shots 3–17), animated as one take so the acting carries across the cuts.
  - The x-ray shots use four modules. `xray_body.py` turns her skin and clothes to glass with a scan line. `airways.py` builds her lungs, windpipe, throat, nose and mouth passages inside her. `air_fx.py` makes the glowing air (the blast, the slam and the swirl). `xray_set.py` puts these together for each shot.
  - The close-ups of the damage have their own sets: `throat_set.py` (the windpipe from inside, its blisters and the tear), `gauge_set.py` (the pressure gauge), `eardrum_set.py` (the ear canal and the eardrum that bursts) and `eye_set.py` (the blood vessels on her eye).
  - `release.py` is her performance for the ending (shots 19–22), again one take: the second seed lands on her nose, she lets go, sneezes into the dandelion and blows it bald.
- `assets/`: the logo-free T-shirt texture and its mask (from a CC0 MakeHuman asset).
- `previews/`: test images from each step.

## One-time setup

The same as video 1. If you already ran `videos/production/setup_assets.py` for the brain-freeze video, there is nothing to do. Otherwise open it in Blender's Scripting tab and press **Run Script** (needs internet).

## Render a shot

Shots render with EEVEE at 1080×1920, 64 samples, with motion blur. Each script writes PNG frames to `videos/sneeze/renders/<shot>/`. Frames that already exist are skipped, so an interrupted render simply continues when you run it again.

In PowerShell, from the repository folder (`C:\Users\asc\Sajeel`):

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P videos\sneeze\shots\shot01_dandelion.py -a
```

All shots in a loop:

```powershell
Get-ChildItem videos\sneeze\shots\shot*.py | ForEach-Object { & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P $_.FullName -a }
```

To look at a shot in Blender instead: start a new file (File > New > General), then in the Python Console:

```python
import runpy
runpy.run_path(r"C:\Users\asc\Sajeel\videos\sneeze\shots\shot01_dandelion.py", run_name="__main__")
```

## Credits (for the video description)

- Character: MPFB 2 with MakeHuman assets (CC0): skin, eyes, ponytail, eyebrows, eyelashes, T-shirt and jeans, shoes, the faceunits01 expression pack and the nose targets. No credit required.
- Dandelion, seeds, backdrop and effects: modelled procedurally by the scripts.
- No CC-BY or non-commercial assets are used so far. Any CC-BY asset added later will be listed here with its creator.

## Preview vs final

Previews are rendered with Cycles on a CPU at half size (`SHOT_PREVIEW=1`). Without it, the scripts build the final EEVEE setup. Strands (the dandelion fluff) are rendered as strips in EEVEE so they look the same as in Cycles.

# Why Do Your Fingers Wrinkle In Water? 💦

Video 3: a vertical Short of 25 seconds (750 frames at 30 fps) in the style of Zack D. Films, built from Python scripts that drive Blender. Each script builds its shot (set, character, animation, lights, camera, compositing) from scratch in an empty file.

- `SCRIPT_AND_SHOTS.md`: the voiceover script with timings, the sources, and the 16-shot plan.
- `MASTER_PROMPT.md`: your master prompt for this video.
- `shots/`: one script per shot. Built so far: shots 1–5.
- `scenes/`: shared sets and acting.
  - `pool_set.py`: the sunny backyard pool (Poly Haven "Pool" HDRI with a bluer sky, mosaic tiles with dancing light patterns, the stone edge and deck, the water, the rubber duck, the marble), plus the time-lapse controls, ripples, falling drops, palm-frond shadows and the lights.
  - `swimmer.py`: the new character, wet, in a red Jay3Dfilms swim shirt.
  - `wrinkles.py`: the wrinkles that grow on his fingertips (real geometry in the close-ups).
  - `pool_acting.py`: placing and posing him in the pool (arms, hands, face and body over time).
  - `opening_take.py`: his performance for shots 1–3, animated as one take so the acting carries across the cuts.
  - `hand_set.py`: his hand alone on the studio blue for shots 4–5 (open, palm up): the drops that soak in, his red "?", and the X-ray (glass skin, bones and nerves fitted inside his hand).
- `previews/`: test images from each step.

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

The edit (joining the shots, the captions, the voiceover, sound effects and music) is added once you have recorded the voiceover, as for video 2.

## Credits (for the video description)

- Character: MPFB 2 with MakeHuman assets (CC0): skin, eyes, short hair, eyebrows, eyelashes, T-shirt (as the swim shirt), shorts, and the faceunits01 expression pack. No credit required.
- Poly Haven (CC0, no credit required): "Pool" HDRI, "Rounded Square Tiled Wall" and "Patio Tiles" textures, "Bi Stretch" fabric, "Rubber Duck Toy".
- Water, wrinkles, fingertip, marble, palm fronds, X-ray bones and nerves, and effects: modelled procedurally by the scripts.
- No CC-BY or non-commercial assets are used.
- Sources for the facts: listed in `SCRIPT_AND_SHOTS.md` (Wilder-Smith and Chow, Muscle & Nerve 2003; Wilder-Smith, Clinical Autonomic Research 2004; Changizi et al., Brain, Behavior and Evolution 2011; Kareklas, Nettle and Smulders, Biology Letters 2013; Davis, PLOS ONE 2021; Haseleu et al., PLOS ONE 2014).

## Preview vs final

Previews are rendered with Cycles on a CPU at reduced size (`SHOT_PREVIEW=1`). Without it, the scripts build the final EEVEE setup. The water has no refraction (a see-through surface with a Fresnel sheen), and the colour of things under it comes from an underwater tint in their materials, so EEVEE and Cycles look the same.

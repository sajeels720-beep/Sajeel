# What Happens If You Hold In A Sneeze 🤧

Video 2: a vertical Short of about 37 seconds (1,110 frames at 30 fps) in the style of Zack D. Films, built from Python scripts that drive Blender. Each script builds its shot (set, character, animation, lights, camera, compositing) from scratch in an empty file.

- `SCRIPT_AND_SHOTS.md`: the voiceover script with timings, and the 22-shot plan.
- `VOICEOVER.md`: what to record, with file names and time slots.
- `SOUND_EFFECTS.md`: every sound effect, with an ElevenLabs prompt and where it plays.
- `audio/`: the voiceover (and, once made, the sound effects and music).
- `timeline.py`, `assemble_cut.py` and `mix_audio.py`: the edit. The picture is fixed, so each voiceover part is split at its pauses and every phrase starts on its cue in the picture. `assemble_cut.py` joins the shots and burns in the captions; `mix_audio.py` adds the voice, sound effects and music and sets the loudness to YouTube level.
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

## Build the final video

This needs Python 3 and ffmpeg on your PATH (on Windows, type `py` instead of `python3`). Once every shot is rendered, run these two commands from the repository folder:

```bash
python3 videos/sneeze/assemble_cut.py videos/sneeze/renders sneeze_captions.mp4 --captions --voiceover videos/sneeze/audio
python3 videos/sneeze/mix_audio.py videos/sneeze/audio sneeze_captions.mp4 sneeze_final.mp4
```

The first joins the 22 shots (every frame as rendered) and burns in his caption style: 2–4 white bold words at about 72% height, each group coming up as it is spoken. The second puts every voiceover phrase on its cue, lines up the sound effects, fits the music's last hit to her smile, dips the music under the voice and sets the loudness YouTube expects (-14 LUFS). `sneeze_final.mp4` is the finished Short. For a version without captions, leave out `--captions --voiceover videos/sneeze/audio`.

## Credits (for the video description)

- Character: MPFB 2 with MakeHuman assets (CC0): skin, eyes, ponytail, eyebrows, eyelashes, T-shirt and jeans, shoes, the faceunits01 expression pack and the nose targets. No credit required.
- Dandelion, seeds, anatomy, pressure gauge, backdrop and effects: modelled procedurally by the scripts.
- Voice and sound effects: made in ElevenLabs. On a paid plan no credit is required; on the free plan ElevenLabs must be credited (for example "Voice and sound: ElevenLabs (elevenlabs.io)") and the video can't be monetized. The music follows its own licence: ElevenLabs Music as above; a YouTube Audio Library track needs the attribution line its page gives, if it asks for one.
- No CC-BY or non-commercial assets are used.
- Sources for the facts: Misirovs R. et al., "Spontaneous tracheal perforation following a sneeze", BMJ Case Reports 2023 (doi:10.1136/bcr-2023-255633); Yang W. et al., "Snap, crackle and pop: when sneezing leads to crackling in the neck", BMJ Case Reports 2018.

## Preview vs final

Previews are rendered with Cycles on a CPU at half size (`SHOT_PREVIEW=1`). Without it, the scripts build the final EEVEE setup. Strands (the dandelion fluff) are rendered as strips in EEVEE so they look the same as in Cycles.

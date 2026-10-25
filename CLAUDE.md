# Jay3Dfilms YouTube Shorts: standing rules

These videos are made with Blender scripts and uploaded to a monetized YouTube channel.

- Follow the master prompt for each video (`videos/<video>/MASTER_PROMPT.md`; the template is `videos/MASTER_PROMPT.md`), including its YOUTUBE section: everything original or licensed for commercial use, no copying other creators' work, cleared music and voices, sourced facts, no gore.
- Never delete the user's objects without asking.
- Never use Non-Commercial licensed models. List every CC-BY model with its creator so it can be credited; keep each video's credits in its README.
- Write the shot list before building and wait for approval. Work one step at a time and give a 2–3 line summary after each step.

## The user's setup

- Windows 11 laptop with no dedicated GPU; Blender 5.2.2 at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; this repository at `C:\Users\asc\Sajeel`. Development branch: `claude/video-review-r3e9jp`.
- Final renders run from PowerShell with the loop in each video's README (EEVEE, 1080×1920, 9:16, 30 fps, 64 samples, PNG frames in `renders/`), then the edit is built with `py assemble_cut.py … --captions --voiceover …` and `py mix_audio.py …`. One-time Blender setup: `videos/production/setup_assets.py` (MPFB and the MakeHuman packs), already done for video 1.
- Voiceover, sound effects and music are made in ElevenLabs as plain text (no audio tags or capitals: they overact), one file per part, uploaded here and placed by `timeline.py`.
- Captions: the brain-freeze style (2–4 white bold words at about 72% height, timed to the voice), with no punctuation.

## Where things stand

- Video 1, brain freeze (`videos/brain-freeze/`): finished and delivered.
- Video 2, "What Happens If You Hold In A Sneeze" (`videos/sneeze/`): all 22 shots built and previewed; voiceover (6 parts), all 27 sound effects, music and captions are in the edit; title, description, tags and upload settings are in `YOUTUBE.md`. The user is rendering the final shots on the laptop.
- Still to confirm with the user: that the ElevenLabs audio was made on a paid plan (needed to monetize), and where the music came from.

## Compact instructions

When this conversation is compacted, keep: these rules and the user's setup; where things stand; every decision the user made and every change they asked for (with the reason); file names, paths and commands; open questions; and anything promised but not done yet. Update "Where things stand" in this file whenever it changes.

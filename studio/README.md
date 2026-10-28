# Short-film studio

Makes flat 2-D animated short films in the round-head "inner battle" style (like *DISCIPLINE | An Animated
Short Film*) entirely from code: characters, sets, camera, effects, original music, sound design, whispered
voices, thumbnail and upload sheet. No stock footage, no AI video, no copyrighted music.

## One command

```bash
.venv/bin/python studio/make_film.py films/what_will_people_say all
```

Outputs land in `output/<film>/`:

| File | What it is |
|---|---|
| `what_will_people_say.mp4` | Final film, 1080p30 H.264, AAC audio at -14 LUFS |
| `thumbnail.png` | 1280x720 thumbnail; `thumbnail_a.png` ... `thumbnail_e.png` are variants for Test & Compare |
| `audio/mix.wav` | The finished soundtrack; `audio/stems/` has the music stems |

The YouTube title, description, chapters and tags live in `films/<film>/youtube.md`. Thumbnails follow the
house style in [`THUMBNAILS.md`](THUMBNAILS.md); `studio/polish.py` finishes a code-drawn layout in that style.

## Stages

```bash
make_film.py <film> sheet 0 30 1.5   # contact sheet of frames 0-30 s every 1.5 s (fast preview)
make_film.py <film> still 15.2       # one full-size frame
make_film.py <film> audio            # score -> stems, effects, whispers, mix
make_film.py <film> video [t0 t1]    # picture only (4 parallel workers)
make_film.py <film> thumb            # thumbnail
make_film.py <film> mux              # picture + soundtrack -> final mp4
make_film.py <film> all              # everything
```

## Setup (once per machine)

```bash
sudo apt-get install -y ffmpeg libegl1 fluidsynth fluid-soundfont-gm
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r studio/requirements.txt
```

Whispered lines use Gemini text-to-speech when `GEMINI_API_KEY` is set (or saved in `~/.config/watch/.env`).
Results are cached in `output/<film>/audio/tts_cache/`, so rebuilding doesn't use your quota again. Without a
key, wordless synthetic whispers are used and the on-screen text still carries the words.

## How it's built

```
studio/
  engine/   core.py (time, easing, keyframes)  draw.py (Skia helpers, palette)  rig.py (character rig, IK, faces)
            props.py (guitar, bed, stage, ...)  fx.py (notes, shards, eyes, shockwaves)  captions.py  render.py
  audio/    score.py (MIDI in seconds -> FluidR3 GM stems)  sfx.py (synthesised effects)  voices.py (TTS whispers)
            dsp.py  mix.py (buses, ducking, leveller, limiter)
  make_film.py
films/what_will_people_say/
  cues.py       the master timeline (every caption, whisper, counter and story beat)
  common.py     cast and shared sets   act1.py / act2.py / act3.py   the shots
  film.py       picture assembly       sound.py   the score, effects and mix    thumbnail.py   youtube.md
```

Every frame is a pure function of time, so renders are deterministic and split across CPU cores.

## Making the next film

1. Copy `films/what_will_people_say` to `films/<new_film>`.
2. Rewrite `cues.py` with the new beats (keep the structure: the loop -> mirror -> rock bottom -> Day 1 -> grind ->
   final fight -> summit -> callback -> title card).
3. Change the scenes in the act files, reusing `common.py`, `engine/props.py` and `engine/fx.py`.
4. Rewrite the score in `sound.py` (a theme, its broken version, the build, the drop, the release).
5. Preview with `sheet` until it reads, then run `all`.

Licences: fonts are SIL OFL (see `assets/fonts/LICENSES.txt`); FluidR3_GM soundfont is MIT. All music is
composed in `sound.py`, so the film is safe from Content ID claims on the soundtrack.

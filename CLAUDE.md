# Brave Films studio

Animated short films for the YouTube channel **Brave Films** ("animated short films about being scared and
doing it anyway"), made entirely in code: a 2D puppet engine on skia-python, a fluidsynth score, synthesised
sound effects and Gemini TTS whispers. See `studio/README.md`.

- Build a film: `.venv/bin/python studio/make_film.py films/<film> all` (or `still`, `video`, `audio`, `thumb`, `subs`, `mux`).
- Outputs go to `output/<film>/` (git-ignored).
- Gemini API key: `GEMINI_API_KEY`, or `~/.config/watch/.env`. Never print it, log it or commit it.

## Thumbnails

Every thumbnail must follow `studio/THUMBNAILS.md`: match the quality and style of the owner's favourite,
`studio/assets/reference/thumbnail_reference.png`, but not its content. Each film gets its own scene, props and
words. Look at that image before designing a new one.

## Subtitles

Every film the owner gets comes with subtitles, without being asked: `make_film.py films/<film> subs` writes
`output/<film>/subtitles.srt` (timed; YouTube Studio > Subtitles > Add > Upload file > With timing) and
`transcript.txt` (YouTube's Auto-sync). Send both with the video, thumbnail and upload sheet. The lines come from
the film's `cues.py` (`NARRATOR`, `WHISPERS`, `SPEECH`, `ROAR`, `COUNTDOWN`, `TITLE_CARD`, `SUBTITLES_EXTRA`), so keep
every on-screen or spoken line there.

## The owner's standing rules for every film

- **The hero always looks like film 1's hero**: a round, hairless, off-white head (`Look()` defaults: skin
  `#EDE6D9`, the blue hoodie `#36586C`). No hair, no other skin tone, no other top colour. Other characters
  (an older self, a friend) are built from that look.
- **Characters never speak aloud.** Their lines appear as captions only, with closed mouths (no lip
  movement, no character voices). Only the shadow (which has no mouth) whispers.
- **Music is dark and cinematic** where the story needs tension or emotional weight: low drones, heavy hits,
  slow builds, a sombre lead line. Avoid warm, cosy or light-hearted music under the drama.

## Every film is its own film

The owner asked for this on film 4 and it holds for every film after it:

- **Its own music and sound design.** Never reuse the previous films' palette. Films 1-3 used piano, strings,
  choir, horns, timpani and taiko over a 120 BPM 4/4 grind; film 4 used a ticking pocket watch as the pulse, dark
  pads, contrabass, synth strings, synth-brass braams, melodic toms and an English horn theme in D minor (6/8 on
  the tick for the climb). Pick new instruments (General
  MIDI programs and drum kits), a new key, tempo and metre, motifs that come from the story's own objects, and
  sound effects built for its world. Note the palette in the film's `sound.py` docstring.
- **A strong opening hook.** Within the first 5 seconds a question the viewer needs answered; the premise and
  stakes clear by about 15 seconds; then the title.
- **Smooth movement.** Animate with `studio/engine/motion.py`: `Curve` (spline keys that flow through poses,
  with `lag` for overlapping action), `Gait` (planted-foot walks and runs, also on slopes), `blend` for
  transitions, `CamPath` for cameras. Avoid switching poses between frames; blend them. Films render at 30 fps.

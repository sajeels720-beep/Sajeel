# Brave Films studio

Animated short films for the YouTube channel **Brave Films** ("animated short films about being scared and
doing it anyway"), made entirely in code: a 2D puppet engine on skia-python, a fluidsynth score, synthesised
sound effects and Gemini TTS whispers. See `studio/README.md`.

- Build a film: `.venv/bin/python studio/make_film.py films/<film> all` (or `still`, `video`, `audio`, `thumb`, `mux`).
- Outputs go to `output/<film>/` (git-ignored).
- Gemini API key: `GEMINI_API_KEY`, or `~/.config/watch/.env`. Never print it, log it or commit it.

## Thumbnails

Every thumbnail must follow `studio/THUMBNAILS.md` and match the owner's favourite,
`studio/assets/reference/thumbnail_reference.png`. Look at that image before designing a new one.

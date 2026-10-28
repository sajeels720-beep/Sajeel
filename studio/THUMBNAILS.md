# Thumbnails: the house style

The channel owner's favourite thumbnail sets the **quality and style** every new one must reach:
[`assets/reference/thumbnail_reference.png`](assets/reference/thumbnail_reference.png) (film 1, "WHAT WILL PEOPLE SAY?").

**Copy the style, not the picture.** Each film gets its own thumbnail idea: its own scene, characters, props,
colours and words, chosen to fit that story. Nothing about film 1's content (the red-eyed crowd, the guitar,
the stage) carries over unless the new story needs it.

## Style to copy every time

- **Polished finish.** A premium 2D cartoon look, not flat clip-art: soft shading on rounded forms, small
  catchlights in the eyes, soft cinematic light from one clear source with a little haze, and shallow depth of
  field (soft-focus foreground shapes, sharp subject).
- **Clear brightness order.** The title and the main face are the brightest things in the frame. One accent
  colour that belongs to the story comes next; everything else sits darker. A moody, dark background suits the
  channel, but the story decides the palette.
- **House lettering.** 1 to 4 words in huge bold white capitals with rough dry-brush edges and a thick black
  outline, usually top-left on one or two lines. Never over the face.
- **One character, one quiet emotion, big.** The hero's head is about a third of the frame height. The emotion is
  subtle and human: no sweat drops, no shake lines, no exaggerated faces (wide white eyes, open mouth).
- **The story object reads instantly.** Whatever prop carries the story is fully visible and recognisable.
- **Restraint at the edges.** Glows and accent light stay subtle near the frame edges; no colour haze.
- **Phone first.** At 320 px wide the words, the face's emotion and the story object still read.

## Film 1 specifics (example, not a template)

A crowd of black silhouettes with glowing red eyes in layers around him, a guitar, the hero without his beanie,
a two-line white title. The owner asked for: white text only, no hat, a calmer face, the hero moved toward the
centre and made bigger, and less red glow at the edges.

## Workflow

1. **Layout in code.** Draw the new idea in `films/<film>/thumbnail.py` with the studio engine: scene, hero size
   and position, emotion, props, palette, title placement. Render with
   `.venv/bin/python studio/make_film.py films/<film> thumb`.
2. **Polish to the reference quality.**
   `.venv/bin/python studio/polish.py LAYOUT.png OUT.png --title "LINE ONE|LINE TWO" --emotion "..." --extra "..."`
   sends the layout (what to show) and the reference (how to render it) to a Gemini image model (Nano Banana Pro,
   then Nano Banana 2, then Nano Banana) and writes a 1280x720 file under YouTube's 2 MB limit.
   - Needs `GEMINI_API_KEY` with **billing enabled** on its Google AI Studio project: the free tier allows
     0 image generations (checked October 2026). The request has not yet run end to end.
   - Without billing: add `--print-prompt`, and hand the owner the layout, the reference and that prompt to
     paste into the free Gemini app.
3. **Check before sending.**
   - The title is spelled exactly right (image models can garble letters; regenerate if so).
   - Nothing from the reference's content leaked in (no stray red-eyed crowd or guitar in another film).
   - At 320 px wide the emotion and the story object still read.
   - Nothing important in the bottom-right corner, where YouTube puts the video length.
   - No stray colours, extra text, logos or watermarks; 16:9, 1280x720, under 2 MB.
4. **Offer 2 or 3 variants** for YouTube's Test & Compare rather than one guess.

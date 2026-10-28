# Thumbnails: the house style

The channel owner's favourite thumbnail is the standard every new one is measured against:
[`assets/reference/thumbnail_reference.png`](assets/reference/thumbnail_reference.png) (film 1, "WHAT WILL PEOPLE SAY?").
Open it before designing anything, and match its look.

## What makes it work

- **Two bright things only.** The title and the hero's face are the only white in the frame; the red eyes come
  second; everything else is near-black. The eye goes straight to the words, then the face.
- **The title.** Top-left, two short lines, huge (letters about 12% of the frame height). Bold white capitals
  with rough dry-brush edges and a thick black outline, slightly overlapping the scene. Never over the face.
- **One character, one quiet emotion.** The hero's round white head is big (about a third of the frame height)
  and just right of centre, under the title. Soft spherical shading on the head, small white catchlights in the
  dot eyes, worried brows and a small frown, glancing sideways at the crowd. Subtle and human, not cartoon panic.
- **The prop tells the story.** The guitar is fully readable: body, sound hole, neck, headstock and tuning pegs.
- **The crowd in layers.** Black round-headed silhouettes with glowing, slanted red eyes and a thin red rim
  light: big soft-focus figures cropped at the left and right edges, sharper ones in the middle distance,
  tiny pairs of red eyes far back in the dark.
- **Light and depth.** A near-black charcoal background with a faint cool haze and a soft spotlight from above
  on the hero. Shallow depth of field: foreground blurred, hero sharp.

## Owner's preferences (from film 1 feedback)

- No sweat drops, shake lines or exaggerated faces (wide white eyes, open mouth). Keep the emotion quiet.
- The hero has no hat in thumbnails.
- Keep the red eyes bright, but the red glow at the frame edges subtle: thin rims, no red haze.
- Make the hero big enough that the emotion reads on a phone.
- White title text only (no yellow second line).

## Workflow

1. **Layout in code.** Draw the composition in `films/<film>/thumbnail.py` with the studio engine: hero size and
   position, emotion, prop, crowd layers, title placement. Render with
   `.venv/bin/python studio/make_film.py films/<film> thumb`.
2. **Polish in the reference style.**
   `.venv/bin/python studio/polish.py LAYOUT.png OUT.png --title "LINE ONE|LINE TWO" --emotion "quiet worry" --extra "..."`
   sends the layout and the reference to a Gemini image model (Nano Banana Pro, then Nano Banana 2, then
   Nano Banana) and writes a 1280x720 file under YouTube's 2 MB limit.
   - Needs `GEMINI_API_KEY` with **billing enabled** on its Google AI Studio project: the free tier allows
     0 image generations (checked October 2026). The request has not yet run end to end.
   - Without billing: add `--print-prompt`, and hand the owner the layout, the reference and that prompt to
     paste into the free Gemini app.
3. **Check before sending.**
   - The title is spelled exactly right (image models can garble letters; regenerate if so).
   - At 320 px wide the face's emotion and the prop still read.
   - Nothing important in the bottom-right corner, where YouTube puts the video length.
   - No stray colours (for example a purple rim), no extra text, logos or watermarks.
   - 16:9, 1280x720, under 2 MB.
4. **Offer 2 or 3 variants** for YouTube's Test & Compare rather than one guess.

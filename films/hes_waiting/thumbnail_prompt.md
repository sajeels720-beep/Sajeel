# Thumbnail prompt (Gemini app / ChatGPT)

Attach two images, in this order: `output/hes_waiting/thumbnail.png` (the layout) and
`studio/assets/reference/thumbnail_reference.png` (the style). The prompt also works on its own.

```
Create a YouTube thumbnail, 16:9 (1280x720), as a still from a premium 2D animated short film.

If I attached images: use the FIRST for the layout and the characters, and the SECOND only for the style and finish. Copy how the second image is drawn and lit, never what it shows.

SCENE: a dark bedroom at 2:47 AM. On the left, out of focus, a young man lies half-reclined in bed under a blue quilt, scrolling his phone; the phone's cold blue light is on his face. On the right, much closer to us and in focus, an old man sits in the dark at the foot of the bed, looking at him. Behind the old man, a window with a crescent moon and a sleeping city.

THE OLD MAN (keep this design): a simple cartoon person with a perfectly round, smooth, off-white head and NO hair at all: bald, with a few faint age spots, a short white beard along the jaw, soft grey eyebrows and gentle wrinkles at the eyes and forehead. No ears, no nose. Black dot eyes with tiny white catchlights. He wears a faded blue hoodie. In both hands, in front of his chest, he holds an old gold pocket watch with a cream face and a thin chain; the watch catches a warm glint and is fully visible. Clean thick dark outlines, soft shading on the round head.

THE YOUNG MAN (keep this design): the same simple cartoon person, young: a perfectly round, smooth, off-white head with no hair, no beard, no ears, no nose, in a blue hoodie.

EMOTION: quiet, patient sadness, like someone who has waited a very long time. Eyes a little wet, the inner ends of the eyebrows slightly raised, a small closed frown. No tears running down, no sweat drops, no open mouth, nothing exaggerated.

COMPOSITION:
- The old man's head is big, about a third of the frame height, right of centre.
- The young man in bed is smaller, on the left, below the title, softly blurred.
- Keep the bottom-right corner free of anything important.

LIGHT AND COLOUR: near-black navy darkness. Cold moonlight from the window behind the old man gives him a thin rim of light; the phone's soft blue light reaches across the room. The gold watch is the only warm colour. Soft cinematic lighting, a little haze, shallow depth of field, high contrast. The title and the old man's face are the brightest things in the image.

TITLE: exactly "HE'S" on the first line and "WAITING." on the second line, top-left, huge (the second line about 45% of the frame width), in bold white rough dry-brush capital letters with a thick black outline and a soft drop shadow. The text must not cover either face.

Do not add any other text, numbers, labels, clock digits, logos or watermarks. No realistic people, no red eyes, no purple or pink tints. It must read clearly at small phone size.
```

## Fix-ups if the first try misses

- `The title is misspelled. Redo it exactly as two lines: "HE'S" and "WAITING."`
- `Make both heads perfect smooth circles with no hair at all; the old man only has a short white beard and soft grey eyebrows, like a cartoon, not a realistic old man.`
- `Make the expression quieter: eyebrows only slightly raised, mouth closed, no tears on the cheeks.`
- `Make the pocket watch bigger and clearer: gold case, cream face, held in both hands in front of his chest.`
- `Make the young man in bed smaller and more blurred so the old man is clearly the subject.`

## Variant B

Attach `output/hes_waiting/thumbnail_b.png` as the first image instead, and replace the COMPOSITION and TITLE
paragraphs with:
`COMPOSITION: the old man alone, big, right of centre, looking straight at the viewer; he holds the pocket watch up by its chain so it hangs in front of his chest. The young man in bed is a small blurred shape far behind on the left.`
`TITLE: exactly "HE'S" on the first line and "YOU." on the second line, top-left, huge, in bold white rough dry-brush capital letters with a thick black outline and a soft drop shadow. The text must not cover his face.`

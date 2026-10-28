"""Finish a code-drawn thumbnail layout in the house thumbnail style with a Gemini image model.

The layout decides what is in the picture (scene, characters, props, palette, title placement); the reference
image only sets the rendering quality and style (see studio/THUMBNAILS.md). The API key is read the same way
as for the whispers and never printed.

    .venv/bin/python studio/polish.py LAYOUT.png OUT.png --title "WHAT WILL|PEOPLE SAY?" --emotion "quiet worry"
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from audio.voices import _key  # noqa: E402

REFERENCE = HERE / 'assets' / 'reference' / 'thumbnail_reference.png'
# Best first; quota or overload on one falls through to the next.
MODELS = ['gemini-3-pro-image', 'gemini-3.1-flash-image', 'gemini-2.5-flash-image']
MAX_BYTES = 2 * 1024 * 1024  # YouTube's thumbnail limit

PROMPT = """Create a finished YouTube thumbnail, 16:9.

The FIRST image is the layout and decides WHAT is in the picture: keep its scene, composition, framing, every \
character exactly as drawn (round white heads, their clothes and accessories), their positions, sizes, poses and \
expressions, the props, the colour palette and mood, and where the title sits.

The SECOND image is a style and quality reference only. Copy HOW it is rendered, never what it shows (ignore its \
characters, crowd, guitar and words): a polished, premium 2D cartoon finish; soft cinematic lighting from one \
clear source with a gentle haze; soft shading on rounded forms; small catchlights in the eyes; shallow depth of \
field with soft-focus foreground shapes; strong contrast so the title and the main face are the brightest things \
in the frame; glows kept subtle near the frame edges; clean shapes that still read at phone size.

The main character shows {emotion}, kept subtle and human: no sweat drops, no shake lines, no exaggerated face. \
{extra}

Title text, spelled exactly as written and nothing else: {title}. Bold white rough-brush capital letters with \
a thick black outline, in the lettering style of the second image, placed where the layout has it. No other \
text, no logos, no watermark, no borders."""


def request(model, parts, size):
    cfg = {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': '16:9'}}
    if size:
        cfg['imageConfig']['imageSize'] = size
    body = json.dumps({'contents': [{'role': 'user', 'parts': parts}], 'generationConfig': cfg}).encode()
    req = Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', data=body,
                  headers={'Content-Type': 'application/json', 'x-goog-api-key': _key()})
    with urlopen(req, timeout=280) as r:
        return json.load(r)


def generate(prompt, images, retries=3):
    """Return (model, image bytes), or (None, reason) when no model will draw."""
    parts = [{'text': prompt}] + [
        {'inline_data': {'mime_type': 'image/png', 'data': base64.b64encode(Path(p).read_bytes()).decode()}}
        for p in images]
    free_tier_zero = False
    for model in MODELS:
        size = '2K' if model.startswith('gemini-3') else None
        for attempt in range(retries):
            try:
                data = request(model, parts, size)
            except HTTPError as e:
                msg = e.read().decode(errors='replace')
                free_tier_zero |= e.code == 429 and 'free_tier' in msg and 'limit: 0' in msg
                print(f'{model}: HTTP {e.code} {msg[:200]}', file=sys.stderr)
                if e.code == 400 and size:
                    size = None  # model doesn't take imageSize; retry without it
                    continue
                if e.code in (500, 503) and attempt < retries - 1:
                    time.sleep(8 * (attempt + 1))
                    continue
                break  # quota, permission or bad request: try the next model
            except (URLError, TimeoutError) as e:
                print(f'{model}: {e}', file=sys.stderr)
                continue
            for cand in data.get('candidates', []):
                for part in cand.get('content', {}).get('parts', []):
                    blob = part.get('inlineData') or part.get('inline_data')
                    if blob:
                        return model, base64.b64decode(blob['data'])
            reason = [c.get('finishReason') for c in data.get('candidates', [])] or data.get('promptFeedback')
            print(f'{model}: no image returned ({reason})', file=sys.stderr)
            break
    if free_tier_zero:
        return None, ('this API key is on the free tier, which allows 0 image generations: turn on billing for '
                      'its project in Google AI Studio, or use --print-prompt in the Gemini app')
    return None, 'no image model produced an image'


def finish(raw, out):
    """Crop to exact 16:9, 1280x720; PNG unless that breaks YouTube's 2 MB limit, then JPEG."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.raw')
    tmp.write_bytes(raw)
    vf = 'scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(tmp), '-vf', vf, str(out.with_suffix('.png'))],
                   check=True)
    final = out.with_suffix('.png')
    if final.stat().st_size > MAX_BYTES:
        jpg = out.with_suffix('.jpg')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(final), '-q:v', '2', str(jpg)], check=True)
        final.unlink()
        final = jpg
    tmp.unlink()
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('layout')
    ap.add_argument('out')
    ap.add_argument('--title', required=True, help="lines separated by '|'")
    ap.add_argument('--emotion', default='quiet worry')
    ap.add_argument('--extra', default='', help='anything else about the character or props')
    ap.add_argument('--reference', default=str(REFERENCE))
    ap.add_argument('--print-prompt', action='store_true',
                    help='print the prompt for pasting into the Gemini app with both images, then stop')
    a = ap.parse_args()
    if not a.print_prompt and not _key():
        sys.exit('No Gemini API key (GEMINI_API_KEY or ~/.config/watch/.env).')
    title = ' / '.join(f'"{line.strip()}"' for line in a.title.split('|')) + \
        (' (two lines)' if '|' in a.title else '')
    prompt = PROMPT.format(title=title, emotion=a.emotion, extra=a.extra)
    if a.print_prompt:
        print(prompt)
        return
    model, raw = generate(prompt, [a.layout, a.reference])
    if model is None:
        sys.exit(f'Not polished: {raw}. Keep the code-drawn layout.')
    path = finish(raw, a.out)
    print(f'{path} ({model}, {path.stat().st_size / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()

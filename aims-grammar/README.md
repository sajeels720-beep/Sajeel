# AIMS Grammar High School website

One-page site for AIMS Grammar High School, Khiali, Gujranwala.
Built with React, Vite, Tailwind CSS v4 and Motion.

## Run it

> **Don't double-click `aims-grammar/index.html`.** That's the source template. It only works
> through the dev server, so opening it directly shows a blank page.
> To look at the finished site without installing anything, open **`dist/index.html`** instead.

Install Node.js 20+ from nodejs.org, then:

```bash
cd aims-grammar
npm install      # first time only
npm run dev      # live preview at http://localhost:5173 that updates as you edit
npm run build    # writes the finished site to dist/
```

`dist/` is a plain static site. Double-click `dist/index.html` to view it, upload the contents
of `dist/` to any host, or connect the repo to Netlify or Vercel with **aims-grammar** as the
base/root directory.

## Editing details

Phone numbers, address, email, social links and the admission session are all in
`src/data/site.ts`. Change them there and they update everywhere.

## Before going live, confirm with the school

- **Email**: the Facebook bio says `aimshs@yaoo.com`. The site uses `aimshs@yahoo.com`, assuming a typo.
- **WhatsApp**: the admission form sends to 0301-8640524. Make sure that number is on WhatsApp.
- **"100%" results claim** on the Matric card comes from the school's own YouTube video. Make sure they're happy to state it.
- **Director quote** paraphrases the same video. Swap in their exact words and name if they want.
- **Logo** (`public/brand/logo.webp`) was cut from a YouTube thumbnail. Replace it with the original artwork file if available.

## Media

- `public/media/hero-*.mp4`: the two classroom clips, cleaned of the corner watermark, cross-faded into one muted loop. There's a desktop cut (1600px) and a portrait mobile cut.
- `public/media/*.webp`: event photos (stage show, Fruit Day, pool party, prize distribution).

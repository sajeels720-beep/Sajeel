import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Browsers refuse to run `type="module"` / `crossorigin` scripts from a file:// URL,
// which leaves a blank page when dist/index.html is double-clicked. The build is a
// single classic (IIFE) bundle instead, and this strips those attributes from the HTML.
function openFromDisk(): Plugin {
  return {
    name: "open-from-disk",
    apply: "build",
    enforce: "post",
    transformIndexHtml(html) {
      return html
        .replace(/<script type="module" crossorigin/g, "<script defer")
        .replace(/<link rel="stylesheet" crossorigin/g, '<link rel="stylesheet"');
    },
  };
}

// `base: "./"` keeps asset paths relative so the built site works from any
// folder or static host (Netlify, Vercel, GitHub Pages, cPanel).
export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss(), openFromDisk()],
  build: {
    modulePreload: false,
    cssCodeSplit: false,
    rollupOptions: {
      output: { format: "iife" },
    },
  },
});

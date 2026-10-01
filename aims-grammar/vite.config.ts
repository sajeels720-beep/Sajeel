import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// `base: "./"` keeps asset paths relative so the built site works from any
// folder or static host (Netlify, Vercel, GitHub Pages, cPanel).
export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
});

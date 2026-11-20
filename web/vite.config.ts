import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The Laravel server hosts the API and the built app on one origin.
const API_ORIGIN = process.env.MLBB_API_ORIGIN ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      // The manifest is served from the origin root so the installed app can
      // use `/` as its start URL and scope.
      name: 'mlbb-root-manifest',
      transformIndexHtml(html) {
        return html.replace('/app/manifest.webmanifest', '/manifest.webmanifest')
      },
    },
  ],
  // Assets live under /app so they never collide with Laravel's own files.
  base: '/app/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    // The polyfill is an inline script. The app is served with a strict
    // Content Security Policy, so it is left out and the browser's native
    // modulepreload support is used instead.
    modulePreload: { polyfill: false },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '^/api/(.*)': {
        target: API_ORIGIN,
        changeOrigin: true,
      },
      '^/download': {
        target: API_ORIGIN,
        changeOrigin: true,
      },
    },
  },
})

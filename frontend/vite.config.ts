import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
import path from "path"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/kredit': 'http://127.0.0.1:8000',
      '/generate': 'http://127.0.0.1:8000',
      '/riwayat': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
  resolve: {
    alias: {
      "@": path.resolve("./src"),
    },
  },
})
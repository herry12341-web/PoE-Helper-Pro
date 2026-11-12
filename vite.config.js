import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const root = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), {
    name: 'offline-campaign-maps',
    closeBundle() {
      fs.cpSync(path.join(root, 'assets/maps'), path.join(root, 'build/assets/maps'), { recursive: true })
    },
  }],
  base: './',
  build: {
    outDir: 'build',
  },
})

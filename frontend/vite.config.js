import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Forward /api/* to the FastAPI server so the browser sees one origin (no CORS setup).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, /api requests are forwarded to the Flask backend so the
// browser sees a single origin (no CORS needed). In Docker, nginx does the
// same job in production.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': apiTarget,
    },
  },
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Where the FastAPI backend lives. In Docker this is set to http://backend:8000.
const target = process.env.VITE_API_PROXY || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // /api    -> all application endpoints
    // /health -> backend health check (used by the Metrics page)
    proxy: {
      '/api': target,
      '/health': target,
    },
  },
})
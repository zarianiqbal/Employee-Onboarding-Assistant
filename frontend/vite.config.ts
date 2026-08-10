import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// During local development, proxy /api and health calls to the FastAPI backend
// so the SPA and API share an origin (no CORS friction in dev).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});

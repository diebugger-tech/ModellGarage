import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5173,
    proxy: {
      // Dev: API-Calls ans FastAPI-Backend weiterreichen (Makefile BACKEND_PORT)
      '/api': 'http://127.0.0.1:8003',
      '/media': 'http://127.0.0.1:8003'
    }
  }
});

import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      // Dev: API-Calls ans FastAPI-Backend weiterreichen
      '/api': 'http://127.0.0.1:8137',
      '/media': 'http://127.0.0.1:8137'
    }
  }
});

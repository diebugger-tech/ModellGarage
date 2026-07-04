import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    // SPA-Modus: FastAPI serviert das Ergebnis (ein Prozess, ein Port).
    adapter: adapter({
      fallback: 'index.html',
      pages: 'build',
      assets: 'build'
    })
  }
};

export default config;

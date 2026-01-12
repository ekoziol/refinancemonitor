import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],

  // Base path for production build (served from Flask static)
  base: mode === 'production' ? '/static/react/' : '/',

  build: {
    // Output to Flask static directory
    outDir: path.resolve(__dirname, '../refi_monitor/static/react'),
    emptyDirOnBuild: true,
    // Generate manifest for Flask integration
    manifest: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
    },
  },

  server: {
    // Proxy API requests to Flask in development
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
}));

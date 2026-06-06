import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  define: {
    localStorage: 'window.safeLocalStorage',
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://127.0.0.1:8000',
        ws: true,
      }
    }
  },
  resolve: {
    alias: [
      { find: '@codingame/monaco-vscode-api/vscode/vs/base/browser/cssValue', replacement: path.resolve(__dirname, './src/shims/cssValue.js') }
    ],
    dedupe: [
      'vscode',
      'monaco-editor',
      '@codingame/monaco-vscode-api'
    ]
  },
  worker: {
    format: 'es'
  },
  plugins: [
    react()
  ],
})


import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// https://vite.dev/config/
export default defineConfig({
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
      }
    }
  },
  resolve: {
    alias: [
      { find: '@codingame/monaco-vscode-api/vscode/vs/base/browser/cssValue', replacement: '/games/CodeProjects/AntiGravity/Neurex/neurex/neurex-web/src/shims/cssValue.js' }
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

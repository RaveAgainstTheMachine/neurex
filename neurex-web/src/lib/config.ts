// src/lib/config.ts
// Standardized API and WebSocket configuration.
// In development, Vite proxies /api and /ws to port 8000.
// In production (Caddy/Docker), the same relative paths work via the reverse proxy.

export const API_BASE = ""; 
export const WS_BASE = window.location.origin.replace(/^http/, "ws");

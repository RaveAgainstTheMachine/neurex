// src/lib/config.ts
// Standardized API and WebSocket configuration.
// In development, Vite proxies /api and /ws to port 8000.
// In production (Caddy/Docker), the same relative paths work via the reverse proxy.

const config = (window as any).__NEUREX_CONFIG__ || {};
const _protocol = config.enableHttps ? "https" : "http";
const wsProtocol = config.enableHttps ? "wss" : "ws";

export const API_BASE = (window as any).__API_BASE__ || ""; 
export const WS_BASE = (window as any).__WS_BASE__ || `${wsProtocol}://${window.location.host}`;

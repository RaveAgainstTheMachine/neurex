// src/lib/config.ts
const origin = window.location.origin;

// Force IPv4 loopback if localhost is used, to avoid IPv6 resolution issues (::1 vs 127.0.0.1)
export const API_BASE = origin.includes("localhost:3000") 
  ? "http://127.0.0.1:8000"
  : origin.replace(":3000", ":8000");

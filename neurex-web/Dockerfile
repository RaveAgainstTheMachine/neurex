# neurex-web/Dockerfile
# High-performance Vite production build served via Nginx.

# ── Build Stage ───────────────────────────────────────────────────────────────
FROM node:20-slim AS builder
WORKDIR /app

# Enable corepack for pnpm if needed, but we use npm
COPY package*.json ./
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN npm install

COPY . .
RUN npm run build

# ── Production Stage ──────────────────────────────────────────────────────────
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]

# ── Stage 1: builder — compile Vite/React static assets ─────────────────────
FROM node:20-slim AS builder
WORKDIR /build

# VITE_API_BASE_URL must be a build-arg — Vite bakes env vars at compile time.
# At K8s runtime, the frontend calls the backend via the K8s-internal service DNS name.
# This arg is set to the ClusterIP service name so the browser-side JS hits the correct URL.
ARG VITE_API_BASE_URL=http://todo-chatbot-backend:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY src/frontend/package*.json .
RUN npm ci
COPY src/frontend/ .
RUN npm run build

# ── Stage 2: runtime — nginx serving static files ────────────────────────────
FROM nginx:alpine AS runtime

COPY --from=builder /build/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Health check — nginx responds 200 on root when serving the React SPA
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

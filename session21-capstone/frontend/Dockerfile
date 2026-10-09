# StockPilot frontend - multi-stage: Node builds the static bundle, nginx serves it.

# ---- stage 1: build ------------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY public/ public/
COPY src/ src/
RUN npm run build

# ---- stage 2: runtime (no Node, no npm, no source - just static files) ---------
FROM nginxinc/nginx-unprivileged:1.31-alpine
# Pick up Alpine security fixes published after the base image was built (Trivy flagged a
# fixable HIGH CVE in libtiff, which nginx's image-filter module pulls in). Needs root briefly.
USER root
RUN apk upgrade --no-cache
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /src/dist /usr/share/nginx/html
ENV BACKEND_URL=http://backend:8000
# The unprivileged image runs as UID 101 and listens on 8080 - no root needed.
USER 101
EXPOSE 8080

# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Frontend image: Vite -> static bundle, served by Nginx with /api proxy.
#
# Two stages:
#   1. `build`   - node:20-alpine, npm ci, vite build -> /app/dist
#   2. `runtime` - nginx:1.27-alpine, copy dist into /usr/share/nginx/html
#                  and a custom nginx.conf that handles SPA fallback +
#                  reverse-proxies /api/* to the backend container.
#
# Build-time arg `VITE_API_BASE_URL` defaults to `/api`, which means the
# browser hits the same origin and Nginx forwards the call. Override at
# build time only if you want the SPA to talk directly to a different
# backend host (no proxy).
# ---------------------------------------------------------------------------

FROM node:20-alpine AS build

WORKDIR /app

# Copy lockfile (or package.json alone if no lockfile yet) BEFORE the rest
# of the source so `npm ci` is cached as long as deps don't change.
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


FROM nginx:1.27-alpine AS runtime

# Replace the default site config with one that serves the SPA and proxies
# /api/* to the backend service over the compose-internal network.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Drop the built static bundle into Nginx's web root.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# nginx:alpine's base CMD already runs `nginx -g 'daemon off;'`, but we set
# it explicitly so the intent is obvious to anyone reading this file.
CMD ["nginx", "-g", "daemon off;"]

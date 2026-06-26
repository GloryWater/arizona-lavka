# =============================================================================
# ARIZONA LAVKA MARKETPLACE - FRONTEND DOCKERFILE
# =============================================================================
# Multi-stage build: compile Vite app, then serve static assets with nginx
# =============================================================================

FROM node:22-alpine AS builder

WORKDIR /app

ARG VITE_API_URL=/api
ARG VITE_CLOUDFLARE_TURNSTILE_SITE_KEY=
ARG VITE_APP_NAME="Arizona Lavka Marketplace"
ARG VITE_APP_VERSION=5.0.0

ENV VITE_API_URL=$VITE_API_URL \
    VITE_CLOUDFLARE_TURNSTILE_SITE_KEY=$VITE_CLOUDFLARE_TURNSTILE_SITE_KEY \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_APP_VERSION=$VITE_APP_VERSION

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine AS production

LABEL maintainer="Arizona Lavka Team"
LABEL version="3.2.0"
LABEL description="Arizona Lavka Marketplace Frontend - Production"

# Use Alibaba Cloud mirror for faster apk in Russia/Asia
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# Install curl for healthcheck
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy server nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/health || exit 1

# Nginx foreground mode
CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# ARIZONA LAVKA MARKETPLACE - FRONTEND DOCKERFILE
# =============================================================================
# Production - Uses pre-built dist folder (run 'npx vite build' before building)
# =============================================================================

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

# Copy pre-built assets from dist folder
COPY dist /usr/share/nginx/html

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

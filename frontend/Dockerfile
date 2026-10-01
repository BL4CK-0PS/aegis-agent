# ==============================================================================
# Stage 1: Build production static bundle
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json* ./

# Install dependencies cleanly
RUN npm install

# Copy application sources
COPY . .

# Compile TypeScript and build production bundle
RUN npm run build

# ==============================================================================
# Stage 2: Serve with lightweight Nginx web server
# ==============================================================================
FROM nginx:alpine

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with reverse proxy support
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]

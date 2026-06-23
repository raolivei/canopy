FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files (lock file enables reproducible, cache-friendly installs)
COPY package.json package-lock.json ./

# Install dependencies — npm ci is faster than install; retries handle transient
# registry DNS failures (EAI_AGAIN) seen on self-hosted ARM64 runners.
RUN npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && for attempt in 1 2 3; do \
         npm ci --legacy-peer-deps && break; \
         if [ "$attempt" -eq 3 ]; then exit 1; fi; \
         echo "npm ci failed (attempt $attempt/3), retrying in 30s..."; \
         sleep 30; \
       done

# Copy source code
COPY . .

# Baked into the client bundle at build time. Use empty for same-origin `/v1` (production ingress);
# do not set cluster service URLs (e.g. http://canopy-api:8000) — they are not valid in the browser.
ARG NEXT_PUBLIC_API_URL=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

# Copy built application
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Use existing user 1000 or create new non-root user
RUN chown -R 1000:1000 /app 2>/dev/null || \
    (adduser -D -u 1001 canopy && chown -R canopy:canopy /app) || \
    chown -R node:node /app || true
USER 1000

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run application
CMD ["npm", "start"]


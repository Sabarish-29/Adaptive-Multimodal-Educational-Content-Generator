# Simple multi-stage Dockerfile for Next.js dev/prod
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
COPY package-lock.json* ./
COPY yarn.lock* ./
COPY pnpm-lock.yaml* ./
RUN [ -f package-lock.json ] || [ -f yarn.lock ] || [ -f pnpm-lock.yaml ] || echo "No lock file" \
	&& npm install --legacy-peer-deps --no-optional

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Disable ESLint during Next.js build to avoid plugin resolution failures in container
ENV NEXT_DISABLE_ESLINT_PLUGIN=true
ENV NEXT_DISABLE_TYPECHECK=true
RUN mkdir -p public && npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/next.config.js ./
# No public assets in repo currently; skip copy
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["node","node_modules/next/dist/bin/next","start","-p","3000"]

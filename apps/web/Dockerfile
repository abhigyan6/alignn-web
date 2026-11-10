# Build from the repository root. Only the public Clerk key is a build argument.
FROM node:24-bookworm-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages ./packages
RUN npm ci
COPY apps/web ./apps/web
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# Caddy routes browser /api requests directly; retain the internal Next rewrite too.
ENV API_ORIGIN=http://api:8000
RUN npm run build

FROM node:24-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 API_ORIGIN=http://api:8000
COPY --from=build --chown=node:node /app /app
USER node
EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "apps/web", "--hostname", "0.0.0.0", "--port", "3000"]

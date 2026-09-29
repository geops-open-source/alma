FROM cypress/browsers:node-24.18.0-chrome-150.0.7871.114-1-ff-152.0.5-edge-150.0.4078.65-1

WORKDIR /frontend

COPY --chown=node:node frontend ./

ENV CYPRESS_BASE_URL=http://nginx
ENV COREPACK_INTEGRITY_KEYS=0

# Requires root privileges
RUN corepack enable pnpm
RUN chown -R node:node /frontend

USER node
RUN pnpm install

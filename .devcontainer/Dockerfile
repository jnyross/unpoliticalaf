FROM node:22-bookworm-slim AS node
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# This project does not use Yarn. Its inherited apt source has a stale signing
# key; keep Debian's signed package sources and verification unchanged.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# Project tooling uses Node 22, not the base image's optional Node installation.
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
RUN node -e 'if (process.versions.node.split(".")[0] !== "22") process.exit(1)'

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# This Python project does not use Yarn. Its inherited apt source has a stale
# signing key and blocks Playwright's dependency install; keep Debian's signed
# package sources and signature verification unchanged.
RUN rm -f /etc/apt/sources.list.d/yarn.list

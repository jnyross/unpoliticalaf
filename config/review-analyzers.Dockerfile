# Built only from the trusted workflow snapshot, before the token-bearing step.
FROM python:3.12.12-slim
COPY requirements-review.txt /tmp/requirements-review.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/requirements-review.txt
ENV HOME=/tmp
WORKDIR /scan

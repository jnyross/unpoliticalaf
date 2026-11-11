# Built only from the trusted workflow snapshot, before the token-bearing step.
FROM python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c
COPY requirements-review.txt /tmp/requirements-review.txt
# Every distribution, including transitive ones, must match a locked wheel hash.
RUN python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /tmp/requirements-review.txt && python -m pip check
ENV HOME=/tmp
WORKDIR /scan

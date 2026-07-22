# syntax=docker/dockerfile:1

# Build stage: install sil-lift from the local source tree into a throwaway
# prefix, so the final image carries only the installed package, not the
# source tree or pip's build-time footprint.
FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91 AS builder

WORKDIR /src

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# lxml>=5 ships manylinux wheels, so this needs no compiler/apt packages.
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

COPY --from=builder /install /usr/local

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Plain `docker run <image> validate ...` uses this entrypoint directly; the
# GitHub Action (action.yml) overrides it with /docker-entrypoint.sh, which
# turns the action's optional/boolean inputs into CLI flags before exec'ing
# this same command.
ENTRYPOINT ["sil-lift"]

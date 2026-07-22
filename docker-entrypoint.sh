#!/bin/bash
# Entrypoint for the "sil-lift validate" Docker/GitHub Action.
#
# Docker-action `args:` are static, so they can't conditionally add flags
# for boolean inputs. This script reads the GitHub-supplied INPUT_* env
# vars and builds the `sil-lift validate` argument list instead, then
# execs it so sil-lift's exit code (0/1/2) propagates unchanged.
#
# bash, not /bin/sh, on purpose: GitHub only replaces spaces with `_` when
# deriving INPUT_<NAME> env vars, so the `no-check-media` input's hyphen
# survives literally as INPUT_NO-CHECK-MEDIA -- not a valid shell
# identifier. dash (this image's /bin/sh) discards any env var whose name
# isn't a valid identifier before the script body even runs, so under
# /bin/sh the value is unrecoverable by the time this script starts
# (verified: `sh -c 'printenv "INPUT_NO-CHECK-MEDIA"'` fails, even though
# the var is present in the container's env). bash does not filter the
# environment this way, so `printenv` can still retrieve it here.
set -eu

no_check_media=$(printenv 'INPUT_NO-CHECK-MEDIA' 2>/dev/null || printenv INPUT_NO_CHECK_MEDIA 2>/dev/null || echo false)

set -- validate "$INPUT_PATH" --format "${INPUT_FORMAT:-text}"

if [ "${INPUT_STRICT:-false}" = "true" ]; then
  set -- "$@" --strict
fi

if [ "$no_check_media" = "true" ]; then
  set -- "$@" --no-check-media
fi

exec sil-lift "$@"

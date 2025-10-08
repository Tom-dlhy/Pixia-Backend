#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=.
# charge .env si tu veux (optionnel) : export $(grep -v '^#' .env | xargs)
uv run prod

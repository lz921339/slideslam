#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BASE_IMAGE="${BASE_IMAGE:-slideslam-single-car:small-city-2026-10-29}"
IMAGE="${SLIDESLAM_IMAGE:-slideslam-single-car:small-city-dev}"

if ! sudo docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
  echo "Missing base image: $BASE_IMAGE" >&2
  exit 1
fi

sudo docker build \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" \
  --tag "$IMAGE" \
  --file "$WORKSPACE/Dockerfile.small-city" \
  "$WORKSPACE"

echo "Built $IMAGE"
echo "Run with: SLIDESLAM_IMAGE=$IMAGE bash $WORKSPACE/run-small-city-wsl.sh"

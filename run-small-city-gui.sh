#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/ubuntu20/workspace/slideslam"
IMAGE="${SLIDESLAM_IMAGE:-slideslam-single-car:small-city-2026-10-29}"
ARCHIVE="$WORKSPACE/slideslam-single-car-small-city.tar"
CONTAINER="slideslam_small_city"

# Use the active local desktop display when this script is started over SSH.
export DISPLAY="${DISPLAY:-:1}"
export XAUTHORITY="${XAUTHORITY:-/run/user/1000/gdm/Xauthority}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install docker.io first." >&2
  exit 1
fi

if ! sudo -n docker info >/dev/null 2>&1; then
  echo "Starting Docker service..."
  sudo service docker start
fi

if command -v xhost >/dev/null 2>&1; then
  xhost +local:docker >/dev/null 2>&1 || true
fi

if ! sudo docker image inspect "$IMAGE" >/dev/null 2>&1; then
  if [[ ! -f "$ARCHIVE" ]]; then
    echo "Missing image archive: $ARCHIVE" >&2
    exit 1
  fi
  sudo docker load -i "$ARCHIVE"
fi

if sudo docker ps -q --filter "name=^/${CONTAINER}$" | grep -q .; then
  echo "Container $CONTAINER is already running."
  exit 0
fi
if sudo docker ps -aq --filter "name=^/${CONTAINER}$" | grep -q .; then
  sudo docker rm "$CONTAINER" >/dev/null
fi

echo "Starting Gazebo GUI + RViz with GPU inference on DISPLAY=$DISPLAY"
exec sudo -E env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" \
  GAZEBO_GUI=true RVIZ=true YOLO_DEVICE=0 \
  bash "$WORKSPACE/run-small-city-wsl.sh"

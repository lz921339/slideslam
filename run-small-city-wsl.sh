#!/usr/bin/env bash
set -euo pipefail

IMAGE="${SLIDESLAM_IMAGE:-slideslam-single-car:small-city-2026-10-29}"
PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="$PACKAGE_DIR/slideslam-single-car-small-city.tar"

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop is not reachable from this Ubuntu terminal." >&2
  exit 1
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  if [[ ! -f "$ARCHIVE" ]]; then
    echo "The image archive is missing: $ARCHIVE" >&2
    exit 1
  fi
  docker load -i "$ARCHIVE"
fi

DEVICE="${YOLO_DEVICE:-cpu}"
GPU_OPTIONS=()
REQUIRE_CUDA=false
if [[ "$DEVICE" != "cpu" ]]; then
  if docker run --rm --gpus all --entrypoint python3 "$IMAGE" -c \
    'import torch; assert torch.cuda.is_available(); a=torch.ones(8,device="cuda"); assert (a+a).sum().item()==16'; then
    GPU_OPTIONS=(--gpus all)
    REQUIRE_CUDA=true
  elif [[ "$DEVICE" != "auto" ]]; then
    echo "The requested GPU cannot run this image. Use YOLO_DEVICE=cpu." >&2
    exit 1
  else
    DEVICE=cpu
  fi
fi
if [[ "$DEVICE" == "auto" ]]; then DEVICE=0; fi

exec docker run --rm -it \
  --name slideslam_small_city \
  "${GPU_OPTIONS[@]}" \
  --shm-size=2g \
  -e "DISPLAY=${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -e LIBGL_ALWAYS_SOFTWARE=1 \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e "GAZEBO_GUI=${GAZEBO_GUI:-false}" \
  -e "RVIZ=${RVIZ:-true}" \
  -e "YOLO_DEVICE=$DEVICE" \
  -e "REQUIRE_CUDA=$REQUIRE_CUDA" \
  -e GAZEBO_MODEL_PATH=/opt/slideslam_worlds/models \
  -e GAZEBO_MODEL_DATABASE_URI= \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  "$IMAGE" roslaunch urdf02_gazebo single_car_full_stack.launch \
  "gui:=${GAZEBO_GUI:-false}" \
  "rviz:=${RVIZ:-true}" \
  "device:=$DEVICE" \
  "require_cuda:=$REQUIRE_CUDA" \
  "car_x:=${CAR_X:-0.0}" \
  "car_y:=${CAR_Y:--45.0}" \
  "car_z:=${CAR_Z:-0.25}" \
  world:=/opt/slideslam_worlds/worlds/small_city.world \
  "yaw:=${CAR_YAW:-0.0}"

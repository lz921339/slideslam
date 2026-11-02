#!/usr/bin/env bash
set -e

AUTO_ARM="${1:-false}"
TARGET_Z="${2:-1.0}"

source /opt/ros/noetic/setup.bash
source "$HOME/demo05_ws/devel/setup.bash"
source "$HOME/PX4-Autopilot/Tools/setup_gazebo.bash" \
  "$HOME/PX4-Autopilot" \
  "$HOME/PX4-Autopilot/build/px4_sitl_default"

export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/gazebo-11/plugins:${LD_LIBRARY_PATH:-}"
export GAZEBO_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/gazebo-11/plugins:${GAZEBO_PLUGIN_PATH:-}"
export ROS_PACKAGE_PATH="$HOME/PX4-Autopilot:$HOME/PX4-Autopilot/Tools/sitl_gazebo:$HOME/demo05_ws/src:/opt/ros/noetic/share"

rospack profile >/dev/null
rospack find px4 >/dev/null
rospack find mavlink_sitl_gazebo >/dev/null

killall px4 2>/dev/null || true
killall gzserver 2>/dev/null || true
killall gzclient 2>/dev/null || true

exec roslaunch urdf02_gazebo px4_full.launch \
  auto_arm:="$AUTO_ARM" target_z:="$TARGET_Z"

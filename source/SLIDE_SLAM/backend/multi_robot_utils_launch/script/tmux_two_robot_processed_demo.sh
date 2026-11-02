#!/bin/bash

# Two-robot SlideSLAM backend demo using processed parking-lot bags.
# This validates namespaces, inter-robot communication, map exchange, and RViz
# without requiring Gazebo or raw sensor frontends.

set -u

SESSION_NAME=two_robot_processed
ROS_MASTER_PORT=11312
BAG_PLAY_RATE=1.0
BAG_START_OFFSET=60
BAG_DIR=/opt/bags/processed_data/parking-lot
CURRENT_DISPLAY=${DISPLAY:-:0}

if [ -n "${TMUX:-}" ]; then
  echo "Run this script from a normal container shell, not from inside tmux."
  exit 1
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "tmux session '$SESSION_NAME' already exists."
  echo "Attach with: tmux attach -t $SESSION_NAME"
  echo "Stop with:   tmux kill-session -t $SESSION_NAME"
  exit 1
fi

if ! compgen -G "$BAG_DIR/robot0*.bag" >/dev/null; then
  echo "No robot0 bag found under $BAG_DIR"
  exit 1
fi

if ! compgen -G "$BAG_DIR/robot1*.bag" >/dev/null; then
  echo "No robot1 bag found under $BAG_DIR"
  exit 1
fi

SETUP_ROS_STRING="source /opt/ros/noetic/setup.bash; source /opt/slideslam_docker_ws/devel/setup.bash; export ROS_MASTER_URI=http://localhost:$ROS_MASTER_PORT; export DISPLAY=$CURRENT_DISPLAY"

tmux new-session -d -s "$SESSION_NAME" -n Main
tmux set-environment -g DISPLAY "$CURRENT_DISPLAY"
tmux setw -t "$SESSION_NAME" -g mouse on

tmux split-window -h -t "$SESSION_NAME:Main"
tmux split-window -v -t "$SESSION_NAME:Main.0"
tmux split-window -v -t "$SESSION_NAME:Main.1"
tmux select-layout -t "$SESSION_NAME:Main" tiled

# ROS master.
tmux send-keys -t "$SESSION_NAME:Main.0" "$SETUP_ROS_STRING; roscore -p $ROS_MASTER_PORT" Enter

# Static transforms used by the supplied RViz configuration.
tmux send-keys -t "$SESSION_NAME:Main.1" "$SETUP_ROS_STRING; until rostopic list >/dev/null 2>&1; do sleep 1; done; rosparam set /use_sim_time false; roslaunch multi_robot_utils_launch publish_tf.launch" Enter

# Processed robot 0 observations and odometry.
tmux send-keys -t "$SESSION_NAME:Main.2" "$SETUP_ROS_STRING; until rostopic list >/dev/null 2>&1; do sleep 1; done; sleep 2; cd $BAG_DIR; rosbag play robot0*.bag -r $BAG_PLAY_RATE -s $BAG_START_OFFSET --topics /Odometry /robot0/semantic_meas_sync_odom /Odometry:=/robot0/odom /robot0/semantic_meas_sync_odom:=/robot0/semantic_meas_sync_odom" Enter

# Processed robot 1 observations and odometry.
tmux send-keys -t "$SESSION_NAME:Main.3" "$SETUP_ROS_STRING; until rostopic list >/dev/null 2>&1; do sleep 1; done; sleep 2; cd $BAG_DIR; rosbag play robot1*.bag -r $BAG_PLAY_RATE -s $BAG_START_OFFSET --topics /Odometry /robot0/semantic_meas_sync_odom /Odometry:=/robot1/odom /robot0/semantic_meas_sync_odom:=/robot1/semantic_meas_sync_odom" Enter

# Existing two-node SlideSLAM backend and RViz.
tmux new-window -t "$SESSION_NAME" -n Sloam
tmux send-keys -t "$SESSION_NAME:Sloam" "$SETUP_ROS_STRING; until rostopic list >/dev/null 2>&1; do sleep 1; done; sleep 2; roslaunch sloam decentralized_sloam_two_robot_processed.launch enable_rviz:=true" Enter

tmux new-window -t "$SESSION_NAME" -n Kill
tmux send-keys -t "$SESSION_NAME:Kill" "tmux kill-session -t $SESSION_NAME"

tmux select-window -t "$SESSION_NAME:Main"
tmux attach-session -t "$SESSION_NAME"
